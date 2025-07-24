from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.util import session_waiter, SessionController
import astrbot.api.message_components as Comp

import urllib.parse
import re
import asyncio

from .client.oauth_client import OsuOAuthClient
from .client.link_account import LinkAccountManager
from .client.token_manager import TokenManager
from .client.osu_client import OsuClient
from .client.osutrack_client import OsuTrackClient
from .osuapi.enumtype import Scopes, OsuModes
from .osuapi.trans import convert_osu_mode_to_track_mode, validate_osu_mode
from .osutrackapi.enums import GameMode
from .help_info import HelpCommandInfo

@register("osu","gameswu","基于osu!track与osu!api的osu!插件","0.2.0","https://github.com/gameswu/astrbot_plugin_osutrack")
class OsuTrackPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.link_account_manager = LinkAccountManager()
        self.token_manager = TokenManager()
        self.osu_client = OsuClient(self.token_manager)
        self.osu_track_client = OsuTrackClient()
        
        # 从配置获取 OAuth 设置
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret") 
        self.redirect_uri = config.get("redirect_uri", "http://localhost:7210/")

    async def initialize(self):
        pass

    async def _check_user_authentication(self, event: AstrMessageEvent, require_scopes: list[Scopes] = None) -> tuple[bool, str, str]:
        """
        检查用户认证状态
        
        Args:
            event: 消息事件
            require_scopes: 需要的权限范围列表，如 [Scopes.PUBLIC] 或 [Scopes.IDENTIFY]
            
        Returns:
            tuple[bool, str, str]: (是否通过检查, 平台ID, OSU用户ID)
                                   如果检查失败，会自动发送错误消息
        """
        platform_id = event.get_sender_id()
        
        # 检查是否已关联
        existing_osu_id = self.link_account_manager.get_osu_id_by_platform(platform_id)
        if not existing_osu_id:
            await event.send(MessageChain([Comp.Plain(
                "❌ 您的账号尚未关联任何 OSU 账号\n"
                "使用 /osu link 开始关联流程"
            )]))
            return False, platform_id, ""
        
        # 检查是否有有效的 token
        if not self.osu_client.has_valid_token(platform_id):
            await event.send(MessageChain([Comp.Plain(
                "❌ 您的 OSU 认证已过期\n"
                "请使用 /osu link 重新认证"
            )]))
            return False, platform_id, existing_osu_id
        
        # 如果需要特定权限，进行权限检查
        if require_scopes:
            missing_scopes = []
            for scope in require_scopes:
                scope_value = scope.value if isinstance(scope, Scopes) else str(scope)
                if not self.osu_client.check_scope_permission(platform_id, scope_value):
                    missing_scopes.append(scope_value)
            
            if missing_scopes:
                scopes_text = ", ".join(missing_scopes)
                await event.send(MessageChain([Comp.Plain(
                    f"❌ 权限不足，缺少以下权限: {scopes_text}\n"
                    "请使用 /osu link 重新认证以获取所需权限"
                )]))
                return False, platform_id, existing_osu_id
        
        return True, platform_id, existing_osu_id

    @filter.command_group("osu")
    async def osu(self, event: AstrMessageEvent):
        pass

    @osu.command("link")
    async def link_account(self, event: AstrMessageEvent):
        """
        关联 OSU 账号和平台 ID
        """
        platform_id = event.get_sender_id()
        
        # 检查是否已经关联
        existing_osu_id = self.link_account_manager.get_osu_id_by_platform(platform_id)
        if existing_osu_id:
            await event.send(MessageChain([Comp.Plain(
                f"❌ 您的账号已经关联了 OSU 账号 ID: {existing_osu_id}\n"
                f"如需重新关联，请先使用 /osu unlink 解除关联。"
            )]))
            return
        
        # 检查配置
        if not self.client_id or not self.client_secret:
            await event.send(MessageChain([Comp.Plain(
                "❌ OSU OAuth 配置不完整，请联系管理员配置 osu_client_id 和 osu_client_secret。"
            )]))
            return
        
        try:
            # 创建 OAuth 客户端
            oauth_client = OsuOAuthClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )
            
            # 生成授权 URL
            state = f"{platform_id}_{int(asyncio.get_event_loop().time())}"
            auth_url = oauth_client.get_authorization_url(state)
            
            # 发送授权链接
            auth_message = (
                "🎮 OSU 账号关联流程\n\n"
                "请按以下步骤操作：\n"
                "1️⃣ 点击下方链接进行 OSU 授权\n"
                f"🔗 {auth_url}\n\n"
                "2️⃣ 完成授权后，浏览器会跳转到一个新页面\n"
                "3️⃣ 将浏览器地址栏的完整 URL 复制并发送给我\n"
                "   （URL 包含类似 ?code=xxxxx 的授权码）\n\n"
                "⏰ 此操作将在 5 分钟后超时"
            )
            
            await event.send(MessageChain([Comp.Plain(auth_message)]))
            
            # 等待用户输入授权回调 URL
            @session_waiter(timeout=300)  # 5分钟超时
            async def handle_auth_callback(controller: SessionController, event: AstrMessageEvent):
                try:
                    callback_url = event.message_str.strip()
                    
                    # 验证并解析回调 URL
                    if "code=" not in callback_url:
                        await event.send(MessageChain([Comp.Plain(
                            "❌ 无效的回调 URL，请确保 URL 中包含授权码 (code=xxxxx)\n"
                            "请重新发送完整的回调 URL"
                        )]))
                        controller.keep(60)  # 继续等待 60 秒
                        return
                    
                    # 提取授权码
                    parsed_url = urllib.parse.urlparse(callback_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    
                    auth_code = query_params.get('code', [None])[0]
                    callback_state = query_params.get('state', [None])[0]
                    
                    if not auth_code:
                        await event.send(MessageChain([Comp.Plain(
                            "❌ 无法从 URL 中提取授权码，请重新发送完整的回调 URL"
                        )]))
                        controller.keep(60)
                        return
                    
                    # 验证 state 参数（可选的安全检查）
                    if callback_state and not callback_state.startswith(platform_id):
                        await event.send(MessageChain([Comp.Plain(
                            "❌ 授权状态验证失败，请重新开始关联流程"
                        )]))
                        controller.stop()
                        return
                    
                    # 显示处理中状态
                    await event.send(MessageChain([Comp.Plain("🔄 正在处理授权信息...")]))
                    
                    # 交换授权码获取访问令牌
                    token_data = await oauth_client.exchange_code_for_token(auth_code)
                    
                    # 保存 token
                    oauth_client.save_token(platform_id, token_data)
                    
                    # 获取用户信息
                    user_info = await oauth_client.get_user_info(platform_id)
                    if not user_info:
                        await event.send(MessageChain([Comp.Plain(
                            "❌ 获取用户信息失败，请重试"
                        )]))
                        controller.stop()
                        return
                    
                    osu_user_id = user_info["id"]
                    username = user_info["username"]
                    
                    # 关联账号
                    success = self.link_account_manager.link_account(osu_user_id, platform_id)
                    if success:
                        await event.send(MessageChain([Comp.Plain(
                            f"✅ 账号关联成功！\n"
                            f"🎮 OSU 用户: {username} (ID: {osu_user_id})\n"
                            f"🆔 平台 ID: {platform_id}\n"
                            f"🎯 现在可以使用 OSU 相关功能了！"
                        )]))
                        logger.info(f"成功关联 OSU 账号: {username}({osu_user_id}) <-> {platform_id}")
                    else:
                        # 关联失败，清理 token
                        oauth_client.remove_token(platform_id)
                        await event.send(MessageChain([Comp.Plain(
                            f"❌ 账号关联失败\n"
                            f"平台 ID {platform_id} 可能已经关联到其他 OSU 账号"
                        )]))
                    
                    controller.stop()
                    
                except Exception as e:
                    logger.error(f"处理 OSU 授权回调失败: {e}")
                    await event.send(MessageChain([Comp.Plain(
                        f"❌ 授权处理失败: {str(e)}\n"
                        f"请重新使用 /osu link 开始关联流程"
                    )]))
                    controller.stop()
            
            # 开始等待用户输入
            try:
                await handle_auth_callback(event)
            except TimeoutError:
                await event.send(MessageChain([Comp.Plain(
                    "⏰ 授权超时（5分钟），请重新使用 /osu link 开始关联流程"
                )]))
            
        except Exception as e:
            logger.error(f"OSU 账号关联过程中发生错误: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 关联过程中发生错误: {str(e)}\n"
                f"请稍后重试或联系管理员"
            )]))

    @osu.command("unlink")
    async def unlink_account(self, event: AstrMessageEvent):
        """
        解除平台 ID 的关联
        """
        platform_id = event.get_sender_id()
        
        # 检查是否已关联
        existing_osu_id = self.link_account_manager.get_osu_id_by_platform(platform_id)
        if not existing_osu_id:
            await event.send(MessageChain([Comp.Plain(
                "❌ 您的账号尚未关联任何 OSU 账号"
            )]))
            return
        
        try:
            # 解除关联
            success = self.link_account_manager.unlink_account(platform_id)
            if success:
                # 同时删除 token
                oauth_client = OsuOAuthClient(
                    client_id=self.client_id or 0,
                    client_secret=self.client_secret or "",
                    redirect_uri=self.redirect_uri
                )
                oauth_client.remove_token(platform_id)
                
                await event.send(MessageChain([Comp.Plain(
                    f"✅ 成功解除关联！\n"
                    f"已解除与 OSU 账号 ID: {existing_osu_id} 的关联"
                )]))
                logger.info(f"解除 OSU 账号关联: {existing_osu_id} <-> {platform_id}")
            else:
                await event.send(MessageChain([Comp.Plain(
                    "❌ 解除关联失败，请稍后重试"
                )]))
        except Exception as e:
            logger.error(f"解除 OSU 账号关联失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 解除关联过程中发生错误: {str(e)}"
            )]))

    @osu.command("me")
    async def get_me(self, event: AstrMessageEvent, mode: str = None):
        """
        获取当前关联账号的用户信息
        """
        # 检查用户认证状态（需要 identify 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.IDENTIFY])
        if not auth_ok:
            return
        
        try:
            await event.send(MessageChain([Comp.Plain("🔄 正在获取您的 OSU 信息...")]))
            
            # 获取用户信息
            user_info = await self.osu_client.get_own_data(platform_id, mode)
            
            # 格式化用户信息
            avatar_url, user_message = self._format_user_info(user_info, is_self=True)
            
            # 构建消息链
            chain = []
            if avatar_url:
                chain.append(Comp.Image.fromURL(avatar_url))
            chain.append(Comp.Plain(user_message))
            
            await event.send(MessageChain(chain))
            
        except Exception as e:
            logger.error(f"获取个人 OSU 信息失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 获取个人信息失败: {str(e)}\n"
                "请稍后重试或使用 /osu link 重新认证"
            )]))

    @osu.command("user")
    async def get_user(self, event: AstrMessageEvent, user: str, mode: str = None, type: str = None):
        """
        查询指定用户的信息
        
        Args:
            user: 用户名或用户ID
            mode: 游戏模式 (osu, taiko, fruits, mania)
            type: 查询类型 (id, name) - 指定输入是用户ID还是用户名
        """
        if not user:
            await event.send(MessageChain([Comp.Plain(
                "❌ 请提供用户名或用户ID\n"
                "用法: /osu user <用户名或ID> [模式] [类型]\n"
                "示例: \n"
                "  /osu user peppy osu name\n"
                "  /osu user 124493 taiko id\n"
                "  /osu user peppy (自动检测)\n\n"
                "类型参数:\n"
                "  id - 按用户ID查询\n"
                "  name - 按用户名查询\n"
                "  不指定 - 自动检测（纯数字视为ID，其他视为用户名）"
            )]))
            return
        
        # 检查用户认证状态（不需要 identify 权限，只需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        # 验证 type 参数
        if type and type not in ['id', 'name']:
            await event.send(MessageChain([Comp.Plain(
                "❌ 无效的查询类型\n"
                "支持的类型: id, name\n"
                "或者不指定类型进行自动检测"
            )]))
            return
        
        try:
            await event.send(MessageChain([Comp.Plain(f"🔄 正在查询用户 {user} 的信息...")]))
            
            # 根据 type 参数处理用户输入
            processed_user = user
            if type == 'id':
                # 强制按 ID 查询
                if user.isdigit():
                    processed_user = int(user)
                else:
                    await event.send(MessageChain([Comp.Plain(
                        f"❌ 指定为 ID 查询，但输入 '{user}' 不是有效的数字ID"
                    )]))
                    return
            elif type == 'name':
                # 强制按用户名查询，确保有 @ 前缀
                if not user.startswith('@'):
                    processed_user = f"@{user}"
            else:
                # 自动检测模式（默认行为）
                if user.isdigit():
                    processed_user = int(user)
                elif not user.startswith('@'):
                    processed_user = f"@{user}"
            
            # 获取用户信息
            user_info = await self.osu_client.get_user(platform_id, processed_user, mode)
            
            # 格式化用户信息
            avatar_url, user_message = self._format_user_info(user_info)
            
            # 构建消息链
            chain = []
            if avatar_url:
                chain.append(Comp.Image.fromURL(avatar_url))
            chain.append(Comp.Plain(user_message))
            
            await event.send(MessageChain(chain))
            
        except Exception as e:
            logger.error(f"查询用户 {user} 信息失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 查询用户 {user} 失败: {str(e)}\n"
                "请检查用户名是否正确，或稍后重试"
            )]))

    @osu.command("users")
    async def get_users(self, event: AstrMessageEvent):
        """
        批量查询多个用户的信息
        通过对话模式获取用户ID列表
        """
        # 检查用户认证状态（不需要 identify 权限，只需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        # 发送提示信息
        prompt_message = (
            "📊 批量用户查询\n\n"
            "请在接下来的消息中发送要查询的用户ID，用空格分隔：\n"
            "📝 示例: 124493 3 2 53378\n"
            "📝 最多支持 50 个用户ID\n"
            "⏰ 请在 5 分钟内发送，超时将取消查询"
        )
        
        await event.send(MessageChain([Comp.Plain(prompt_message)]))
        
        # 等待用户输入用户ID列表
        @session_waiter(timeout=300)  # 5分钟超时
        async def handle_user_ids_input(controller: SessionController, event: AstrMessageEvent):
            try:
                user_input = event.message_str.strip()
                
                # 检查是否取消
                if user_input.lower() in ['取消', 'cancel', '退出', 'quit']:
                    await event.send(MessageChain([Comp.Plain("❌ 已取消批量查询")]))
                    controller.stop()
                    return
                
                # 解析用户ID列表
                user_ids = user_input.split()
                if not user_ids:
                    await event.send(MessageChain([Comp.Plain(
                        "❌ 请提供至少一个用户ID\n"
                        "请重新发送用户ID，用空格分隔"
                    )]))
                    controller.keep(60)  # 继续等待 60 秒
                    return
                
                # 检查数量限制
                if len(user_ids) > 50:
                    await event.send(MessageChain([Comp.Plain(
                        f"❌ 最多支持同时查询 50 个用户\n"
                        f"您提供了 {len(user_ids)} 个用户ID\n"
                        "请重新发送，减少用户ID数量"
                    )]))
                    controller.keep(60)
                    return
                
                # 转换用户ID列表，支持字符串和数字
                processed_ids = []
                invalid_ids = []
                
                for uid in user_ids:
                    if uid.isdigit():
                        processed_ids.append(int(uid))
                    else:
                        # 对于非数字ID，检查是否为有效格式
                        if len(uid) > 0 and not uid.isspace():
                            processed_ids.append(str(uid))
                        else:
                            invalid_ids.append(uid)
                
                # 如果有无效ID，提示用户
                if invalid_ids:
                    await event.send(MessageChain([Comp.Plain(
                        f"⚠️ 发现无效的用户ID: {', '.join(invalid_ids)}\n"
                        f"将继续查询其余 {len(processed_ids)} 个有效ID"
                    )]))
                
                if not processed_ids:
                    await event.send(MessageChain([Comp.Plain(
                        "❌ 没有找到有效的用户ID\n"
                        "请重新发送正确格式的用户ID"
                    )]))
                    controller.keep(60)
                    return
                
                await event.send(MessageChain([Comp.Plain(f"🔄 正在查询 {len(processed_ids)} 个用户的信息...")]))
                
                # 批量获取用户信息
                users_info = await self.osu_client.get_users(platform_id, processed_ids)
                
                if not users_info:
                    await event.send(MessageChain([Comp.Plain(
                        "❌ 没有找到任何用户信息\n"
                        "请检查用户ID是否正确"
                    )]))
                    controller.stop()
                    return
                
                # 发送概览信息
                await event.send(MessageChain([Comp.Plain(f"📊 找到 {len(users_info)} 个用户，正在逐个发送详细信息...")]))
                
                # 为每个用户单独发送信息
                for i, user_info in enumerate(users_info, 1):
                    # 格式化用户信息
                    avatar_url, user_message = self._format_user_info(user_info)
                    
                    # 构建消息链
                    chain = []
                    if avatar_url:
                        chain.append(Comp.Image.fromURL(avatar_url))
                    
                    # 添加序号前缀
                    prefixed_message = f"【{i}/{len(users_info)}】\n{user_message}"
                    chain.append(Comp.Plain(prefixed_message))
                    
                    # 发送单个用户信息
                    await event.send(MessageChain(chain))
                    
                    # 稍微延迟避免消息发送过快
                    if i < len(users_info):  # 最后一个不需要延迟
                        await asyncio.sleep(0.5)
                
                controller.stop()
                
            except Exception as e:
                logger.error(f"批量查询用户信息失败: {e}")
                await event.send(MessageChain([Comp.Plain(
                    f"❌ 批量查询失败: {str(e)}\n"
                    "请检查用户ID是否正确，或稍后重试"
                )]))
                controller.stop()
        
        # 开始等待用户输入
        try:
            await handle_user_ids_input(event)
        except TimeoutError:
            await event.send(MessageChain([Comp.Plain(
                "⏰ 输入超时（5分钟），批量查询已取消\n"
                "请重新使用 /osu users 开始查询"
            )]))

    @osu.command("update")
    async def update(self, event: AstrMessageEvent, mode: str = None):
        """
        上传用户成绩至 OSU!track
        
        Args:
            mode: 游戏模式 (osu, taiko, fruits, mania)，默认为 osu
        """
        # 检查用户认证状态（不需要 identify 权限，只需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        try:
            # 验证和标准化模式
            validated_mode = validate_osu_mode(mode or "osu")
            
            # 转换为 OSU Track 模式
            track_mode = convert_osu_mode_to_track_mode(validated_mode)
            
            await event.send(MessageChain([Comp.Plain(f"🔄 正在上传您的 {validated_mode.upper()} 模式成绩到 OSU!track...")]))
            
            # 调用 OSU Track API 更新用户数据
            update_response = await self.osu_track_client.update_user(osu_id, track_mode)
            
            # 构建成功消息
            success_message = [
                "✅ 成功上传成绩到 OSU!track！",
                f"🎮 用户: {update_response.username}",
                f"🎯 模式: {validated_mode.upper()}",
            ]
            
            # 如果有新的统计信息
            if update_response.newhs:
                success_message.append(f"🆕 新增 {len(update_response.newhs)} 个高分记录")
            
            # 如果有统计变化
            if update_response.update:
                stats = update_response.update
                changes = []
                
                if stats.pp is not None:
                    changes.append(f"PP: {stats.pp:+.2f}")
                if stats.rank is not None:
                    changes.append(f"排名: {stats.rank:+d}")
                if stats.country_rank is not None:
                    changes.append(f"国家排名: {stats.country_rank:+d}")
                if stats.accuracy is not None:
                    changes.append(f"准确率: {stats.accuracy:+.2f}%")
                
                if changes:
                    success_message.append(f"📊 统计变化: {', '.join(changes)}")
            
            await event.send(MessageChain([Comp.Plain("\n".join(success_message))]))
            
        except ValueError as e:
            await event.send(MessageChain([Comp.Plain(f"❌ 参数错误: {str(e)}")]))
        except Exception as e:
            logger.error(f"上传成绩到 OSU!track 失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 上传成绩失败: {str(e)}\n"
                "请稍后重试或检查网络连接"
            )]))

    def _format_user_info(self, user_info, is_self: bool = False) -> tuple[str, str]:
        """
        格式化用户信息为可读文本
        
        Args:
            user_info: UserExtended 对象
            is_self: 是否为当前用户自己的信息
            
        Returns:
            tuple[str, str]: (avatar_url, formatted_text) 头像URL和格式化后的用户信息文本
        """
        prefix = "📋 您的 OSU 信息" if is_self else "📋 用户信息"
        
        # 基本信息
        basic_info = [
            f"{prefix}:",
            f"🎮 用户名: {user_info.username}",
            f"🆔 用户ID: {user_info.id}",
        ]
        
        # 国家信息
        if user_info.country:
            basic_info.append(f"🌍 国家: {user_info.country.get('name', '未知')}")
        
        # 加入日期
        if user_info.join_date:
            basic_info.append(f"📅 加入日期: {user_info.join_date}")
        
        # 游戏统计信息
        if user_info.statistics:
            stats = user_info.statistics
            
            stats_info = [
                "",
                "📊 游戏统计:",
                f"⭐ 等级: {stats.level.get('current') if stats.level else 'N/A'}",
                f"🏆 PP: {stats.pp or 'N/A'}",
                f"🎯 准确率: {stats.hit_accuracy:.2f}%" if stats.hit_accuracy else "🎯 准确率: N/A",
                f"🎲 游戏次数: {stats.play_count or 'N/A'}",
                f"⏱️ 游戏时间: {self._format_play_time(stats.play_time) if stats.play_time else 'N/A'}",
            ]
            
            # 排名信息
            if stats.global_rank:
                stats_info.append(f"🌍 全球排名: #{stats.global_rank}")
            if stats.country_rank:
                stats_info.append(f"🏳️ 国家排名: #{stats.country_rank}")
            
            basic_info.extend(stats_info)
        
        # 在线状态
        if hasattr(user_info, 'is_online') and user_info.is_online is not None:
            status = "🟢 在线" if user_info.is_online else "🔴 离线"
            basic_info.append(f"📡 状态: {status}")
        
        # 支持者状态
        if hasattr(user_info, 'is_supporter') and user_info.is_supporter:
            basic_info.append("💎 OSU 支持者")
        
        # 返回头像URL和格式化文本
        avatar_url = user_info.avatar_url if hasattr(user_info, 'avatar_url') and user_info.avatar_url else None
        return avatar_url, "\n".join(basic_info)

    def _format_play_time(self, play_time_seconds: int) -> str:
        """
        格式化游戏时间为可读格式
        
        Args:
            play_time_seconds: 游戏时间（秒）
            
        Returns:
            str: 格式化后的时间字符串
        """
        if not play_time_seconds:
            return "N/A"
        
        hours = play_time_seconds // 3600
        minutes = (play_time_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"

    @osu.command("help")
    async def help_command(self, event: AstrMessageEvent, command: str = None):
        """
        显示 OSU 插件帮助信息
        """
        if command:
            help_text = (
                f"OSU! 插件帮助 - {command}\n\n"
            )
            help_info = HelpCommandInfo.get(command.upper())
            if help_info:
                help_text += help_info
        else:
            help_text = (
                "OSU! 插件帮助\n\n"
                "账号管理:\n"
                "  /osu link - 关联 OSU 账号\n"
                "  /osu unlink - 解除账号关联\n\n"
                "查询功能:\n"
                "  /osu me [模式] - 查看自己的信息\n"
                "  /osu user <用户名/ID> [模式] [类型] - 查看指定用户信息\n"
                "  /osu users - 批量查询用户信息（对话模式）\n\n"
                "成绩统计功能:\n"
                "  /osu update [模式] - 上传成绩到 OSU!track（默认 osu 模式）\n\n"
                "帮助:\n"
                "  /osu help [命令] - 查看帮助信息\n"
            )
        await event.send(MessageChain([Comp.Plain(help_text)]))

    async def terminate(self):
        return await super().terminate()