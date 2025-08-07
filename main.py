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

@register("osu","gameswu","基于osu!track与osu!api的osu!插件","0.2.1","https://github.com/gameswu/astrbot_plugin_osutrack")
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

    @osu.command("map")
    async def get_beatmap(self, event: AstrMessageEvent, beatmap_id: str):
        """
        查询指定谱面的详细信息
        
        Args:
            beatmap_id: 谱面ID
        """
        if not beatmap_id:
            await event.send(MessageChain([Comp.Plain(
                "❌ 请提供谱面ID\n"
                "用法: /osu map <谱面ID>\n"
                "示例: /osu map 129891"
            )]))
            return
        
        # 验证谱面ID格式
        if not beatmap_id.isdigit():
            await event.send(MessageChain([Comp.Plain(
                f"❌ 无效的谱面ID: {beatmap_id}\n"
                "谱面ID必须是数字"
            )]))
            return
        
        # 检查用户认证状态（需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        try:
            await event.send(MessageChain([Comp.Plain(f"🔄 正在查询谱面 {beatmap_id} 的信息...")]))
            
            # 获取谱面信息
            beatmap_info = await self.osu_client.get_beatmap(platform_id, int(beatmap_id))
            
            # 格式化谱面信息
            beatmap_message = self._format_beatmap_info(beatmap_info)
            
            await event.send(MessageChain([Comp.Plain(beatmap_message)]))
            
        except Exception as e:
            logger.error(f"查询谱面 {beatmap_id} 信息失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 查询谱面 {beatmap_id} 失败: {str(e)}\n"
                "请检查谱面ID是否正确，或稍后重试"
            )]))

    @osu.command("mapset")
    async def get_beatmapset(self, event: AstrMessageEvent, mapset_id: str):
        """
        查询指定谱面集的详细信息
        
        Args:
            mapset_id: 谱面集ID
        """
        if not mapset_id:
            await event.send(MessageChain([Comp.Plain(
                "❌ 请提供谱面集ID\n"
                "用法: /osu mapset <谱面集ID>\n"
                "示例: /osu mapset 41823"
            )]))
            return
        
        # 验证谱面集ID格式
        if not mapset_id.isdigit():
            await event.send(MessageChain([Comp.Plain(
                f"❌ 无效的谱面集ID: {mapset_id}\n"
                "谱面集ID必须是数字"
            )]))
            return
        
        # 检查用户认证状态（需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        try:
            await event.send(MessageChain([Comp.Plain(f"🔄 正在查询谱面集 {mapset_id} 的信息...")]))
            
            # 获取谱面集信息
            beatmapset_info = await self.osu_client.get_beatmapset(platform_id, int(mapset_id))
            
            # 格式化谱面集信息
            cover_url, beatmapset_message = self._format_beatmapset_info(beatmapset_info)
            
            # 构建消息链
            chain = []
            if cover_url:
                chain.append(Comp.Image.fromURL(cover_url))
            chain.append(Comp.Plain(beatmapset_message))
            
            await event.send(MessageChain(chain))
            
        except Exception as e:
            logger.error(f"查询谱面集 {mapset_id} 信息失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 查询谱面集 {mapset_id} 失败: {str(e)}\n"
                "请检查谱面集ID是否正确，或稍后重试"
            )]))

    @osu.command("mapsets")
    async def get_beatmapsets(self, event: AstrMessageEvent):
        """
        批量查询多个谱面集的信息
        通过对话模式获取谱面集ID列表
        """
        # 检查用户认证状态（需要 public 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        # 发送提示信息
        prompt_message = (
            "📊 批量谱面集查询\n\n"
            "请在接下来的消息中发送要查询的谱面集ID，用空格分隔：\n"
            "📝 示例: 41823 129891 55496 162019\n"
            "📝 最多支持 20 个谱面集ID\n"
            "⏰ 请在 5 分钟内发送，超时将取消查询"
        )
        
        await event.send(MessageChain([Comp.Plain(prompt_message)]))
        
        # 等待用户输入谱面集ID列表
        @session_waiter(timeout=300)  # 5分钟超时
        async def handle_mapset_ids_input(controller: SessionController, event: AstrMessageEvent):
            try:
                user_input = event.message_str.strip()
                
                # 检查是否取消
                if user_input.lower() in ['取消', 'cancel', '退出', 'quit']:
                    await event.send(MessageChain([Comp.Plain("❌ 已取消批量查询")]))
                    controller.stop()
                    return
                
                # 解析谱面集ID列表
                mapset_ids = user_input.split()
                if not mapset_ids:
                    await event.send(MessageChain([Comp.Plain(
                        "❌ 请提供至少一个谱面集ID\n"
                        "请重新发送谱面集ID，用空格分隔"
                    )]))
                    controller.keep(60)  # 继续等待 60 秒
                    return
                
                # 检查数量限制
                if len(mapset_ids) > 20:
                    await event.send(MessageChain([Comp.Plain(
                        f"❌ 最多支持同时查询 20 个谱面集\n"
                        f"您提供了 {len(mapset_ids)} 个谱面集ID\n"
                        "请重新发送，减少谱面集ID数量"
                    )]))
                    controller.keep(60)
                    return
                
                # 验证谱面集ID格式
                valid_ids = []
                invalid_ids = []
                
                for mapset_id in mapset_ids:
                    if mapset_id.isdigit():
                        valid_ids.append(int(mapset_id))
                    else:
                        invalid_ids.append(mapset_id)
                
                # 如果有无效ID，提示用户
                if invalid_ids:
                    await event.send(MessageChain([Comp.Plain(
                        f"⚠️ 发现无效的谱面集ID: {', '.join(invalid_ids)}\n"
                        f"将继续查询其余 {len(valid_ids)} 个有效ID"
                    )]))
                
                if not valid_ids:
                    await event.send(MessageChain([Comp.Plain(
                        "❌ 没有找到有效的谱面集ID\n"
                        "请重新发送正确格式的谱面集ID（必须是数字）"
                    )]))
                    controller.keep(60)
                    return
                
                await event.send(MessageChain([Comp.Plain(f"🔄 正在查询 {len(valid_ids)} 个谱面集的信息...")]))
                
                # 逐个获取谱面集信息
                successful_count = 0
                failed_count = 0
                
                for i, mapset_id in enumerate(valid_ids, 1):
                    try:
                        # 获取谱面集信息
                        beatmapset_info = await self.osu_client.get_beatmapset(platform_id, mapset_id)
                        
                        # 格式化谱面集信息
                        cover_url, beatmapset_message = self._format_beatmapset_info(beatmapset_info)
                        
                        # 构建消息链
                        chain = []
                        if cover_url:
                            chain.append(Comp.Image.fromURL(cover_url))
                        
                        # 添加序号前缀
                        prefixed_message = f"【{i}/{len(valid_ids)}】\n{beatmapset_message}"
                        chain.append(Comp.Plain(prefixed_message))
                        
                        # 发送单个谱面集信息
                        await event.send(MessageChain(chain))
                        successful_count += 1
                        
                        # 稍微延迟避免发送过快
                        if i < len(valid_ids):  # 最后一个不需要延迟
                            await asyncio.sleep(0.5)
                            
                    except Exception as e:
                        logger.error(f"查询谱面集 {mapset_id} 失败: {e}")
                        await event.send(MessageChain([Comp.Plain(
                            f"❌ 【{i}/{len(valid_ids)}】查询谱面集 {mapset_id} 失败: {str(e)}"
                        )]))
                        failed_count += 1
                
                # 发送总结信息
                summary_message = f"✅ 批量查询完成！成功: {successful_count}, 失败: {failed_count}"
                await event.send(MessageChain([Comp.Plain(summary_message)]))
                
                controller.stop()
                
            except Exception as e:
                logger.error(f"批量查询谱面集信息失败: {e}")
                await event.send(MessageChain([Comp.Plain(
                    f"❌ 批量查询失败: {str(e)}\n"
                    "请检查谱面集ID是否正确，或稍后重试"
                )]))
                controller.stop()
        
        # 开始等待用户输入
        try:
            await handle_mapset_ids_input(event)
        except TimeoutError:
            await event.send(MessageChain([Comp.Plain(
                "⏰ 输入超时（5分钟），批量查询已取消\n"
                "请重新使用 /osu mapsets 开始查询"
            )]))

    @osu.command("friend")
    async def get_friends(self, event: AstrMessageEvent):
        """
        获取好友列表
        显示每个好友的头像、昵称和在线状态
        """
        # 检查用户认证状态（需要 friends.read 权限）
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.FRIENDS])
        if not auth_ok:
            return
        
        try:
            await event.send(MessageChain([Comp.Plain("🔄 正在获取好友列表...")]))
            
            # 获取好友列表
            friends = await self.osu_client.get_friends(platform_id)
            
            if not friends:
                await event.send(MessageChain([Comp.Plain(
                    "👥 您的好友列表为空\n"
                    "可以在 OSU 官网添加好友后再查看"
                )]))
                return
            
            # OSU API 的 /friends 端点返回的是用户信息列表，不是好友关系对象
            # 所有返回的用户都是好友，我们直接显示他们
            
            # 发送好友总数概览
            total_count = len(friends)
            
            overview_message = (
                f"👥 好友列表 (共 {total_count} 个)\n"
                f"正在逐个发送好友信息..."
            )
            await event.send(MessageChain([Comp.Plain(overview_message)]))
            
            # 发送所有好友信息
            for i, friend in enumerate(friends, 1):
                await self._send_friend_info(event, friend, i, total_count, "👥")
                if i < total_count:  # 最后一个不需要延迟
                    await asyncio.sleep(0.3)  # 避免发送过快
            
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 获取好友列表失败: {str(e)}\n"
                "请检查您是否有 friends.read 权限，或稍后重试"
            )]))

    @osu.group("search")
    def search(self, event: AstrMessageEvent):
        pass

    @search.command("map")
    async def search_map(self, event: AstrMessageEvent, query: str, num_per_page: int, page_num: int, flag: str = None):
        """
        搜索谱面

        Args:
            query: 搜索关键词
            num_per_page: 每页显示的谱面数量
            page_num: 页码
            flag: 启用高级搜索flag
        """
        
        auth_ok, platform_id, osu_id = await self._check_user_authentication(event, [Scopes.PUBLIC])
        if not auth_ok:
            return
        
        # 参数验证
        if not query:
            await event.send(MessageChain([Comp.Plain(
                "❌ 请提供搜索关键词\n"
                "用法: /osu search map <关键词> <每页数量> <页码> [advanced]\n"
                "示例: /osu search map xi 10 1"
            )]))
            return
        
        if num_per_page <= 0 or num_per_page > 50:
            await event.send(MessageChain([Comp.Plain(
                "❌ 每页数量必须在 1-50 之间"
            )]))
            return
        
        if page_num < 1:
            await event.send(MessageChain([Comp.Plain(
                "❌ 页码必须大于 0"
            )]))
            return
        
        try:
            if flag == "advanced":
                # 处理高级搜索逻辑
                await event.send(MessageChain([Comp.Plain(
                    "🔍 高级谱面搜索\n\n"
                    "请按以下格式提供高级搜索参数（每行一个参数，可跳过不需要的参数）：\n\n"
                    "🎵 艺术家（artist）: \n"
                    "🎤 创建者（creator）: \n"
                    "⭐ 最小星级（min_stars）: \n"
                    "⭐ 最大星级（max_stars）: \n"
                    "🎮 游戏模式（mode，osu/taiko/fruits/mania）: \n"
                    "📋 状态（status，ranked/loved/pending/qualified）: \n"
                    "📅 年份（year）: \n"
                    "🏷️ 类型（genre_id，1-未指定 2-视频游戏 3-动漫 4-摇滚 5-流行 6-其他 7-新奇 9-嘻哈 10-电子 11-金属 12-古典 13-民俗 14-爵士）: \n"
                    "🌐 语言（language_id，1-未指定 2-英语 3-日语 4-中文 5-韩语 6-法语 7-德语 8-瑞典语 9-西班牙语 10-意大利语 11-俄语 12-波兰语 13-其他）: \n\n"
                    "示例：\n"
                    "artist=xi\n"
                    "min_stars=5.0\n"
                    "max_stars=7.0\n"
                    "mode=osu\n"
                    "status=ranked\n\n"
                    "⏰ 请在 5 分钟内发送，超时将取消搜索"
                )]))
                
                # 设置会话等待高级搜索参数
                search_params = {"query": query}
                
                @session_waiter(timeout=300)  # 5分钟超时
                async def handle_advanced_search(controller: SessionController, event: AstrMessageEvent):
                    try:
                        user_input = event.message_str.strip()
                        
                        # 检查是否取消
                        if user_input.lower() in ['取消', 'cancel', '退出', 'quit']:
                            await event.send(MessageChain([Comp.Plain("❌ 已取消高级搜索")]))
                            controller.stop()
                            return
                        
                        # 解析高级搜索参数
                        lines = user_input.split('\n')
                        for line in lines:
                            line = line.strip()
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if value:  # 只处理有值的参数
                                    search_params[key] = value
                        
                        # 如果没有额外参数，只使用基础查询
                        if len(search_params) == 1:  # 只有query
                            await event.send(MessageChain([Comp.Plain(
                                "ℹ️ 未提供额外搜索参数，将使用基础搜索"
                            )]))
                        
                        await event.send(MessageChain([Comp.Plain(f"🔄 正在进行高级搜索...")]))
                        
                        # 准备搜索参数
                        search_kwargs = {"platform_id": platform_id}
                        
                        # 映射基础查询
                        if "query" in search_params:
                            search_kwargs["query"] = search_params["query"]
                        
                        # 映射其他参数
                        param_mapping = {
                            "mode": "mode",
                            "status": "category", 
                            "genre_id": "genre",
                            "language_id": "language",
                        }
                        
                        for user_param, api_param in param_mapping.items():
                            if user_param in search_params:
                                search_kwargs[api_param] = search_params[user_param]
                        
                        # 执行高级搜索
                        search_results = await self.osu_client.search_beatmapsets(**search_kwargs)
                        
                        # 处理搜索结果（限制返回数量和分页）
                        if search_results and hasattr(search_results, 'beatmapsets'):
                            beatmapsets = search_results.beatmapsets
                            # 计算分页
                            start_idx = (page_num - 1) * num_per_page
                            end_idx = start_idx + num_per_page
                            paginated_beatmapsets = beatmapsets[start_idx:end_idx]
                            
                            # 创建分页后的结果对象
                            try:
                                paginated_results = type(search_results)(
                                    beatmapsets=paginated_beatmapsets,
                                    cursor=getattr(search_results, 'cursor', None),
                                    search=getattr(search_results, 'search', None),
                                    recommended_difficulty=getattr(search_results, 'recommended_difficulty', None),
                                    error=getattr(search_results, 'error', None),
                                    total=getattr(search_results, 'total', None)
                                )
                            except Exception:
                                # 如果无法创建相同类型的对象，创建一个简单的对象
                                class SimpleSearchResult:
                                    def __init__(self, beatmapsets, cursor=None):
                                        self.beatmapsets = beatmapsets
                                        self.cursor = cursor
                                
                                paginated_results = SimpleSearchResult(
                                    beatmapsets=paginated_beatmapsets,
                                    cursor=getattr(search_results, 'cursor', None)
                                )
                            
                            await self._process_search_results(event, paginated_results, num_per_page, page_num, "高级搜索")
                        else:
                            await self._process_search_results(event, search_results, num_per_page, page_num, "高级搜索")
                        
                        controller.stop()
                        
                    except Exception as e:
                        logger.error(f"高级搜索失败: {e}")
                        await event.send(MessageChain([Comp.Plain(
                            f"❌ 高级搜索失败: {str(e)}\n"
                            "请检查搜索参数格式是否正确"
                        )]))
                        controller.stop()
                
                # 开始等待用户输入
                try:
                    await handle_advanced_search(event)
                except TimeoutError:
                    await event.send(MessageChain([Comp.Plain(
                        "⏰ 输入超时（5分钟），高级搜索已取消"
                    )]))
                    
            else:
                # 处理普通搜索逻辑
                await event.send(MessageChain([Comp.Plain(f"🔄 正在搜索谱面：{query}...")]))
                
                # 执行普通搜索
                search_results = await self.osu_client.search_beatmapsets(
                    platform_id=platform_id, 
                    query=query
                )
                
                # 处理搜索结果（限制返回数量和分页）
                if search_results and hasattr(search_results, 'beatmapsets'):
                    beatmapsets = search_results.beatmapsets
                    # 计算分页
                    start_idx = (page_num - 1) * num_per_page
                    end_idx = start_idx + num_per_page
                    paginated_beatmapsets = beatmapsets[start_idx:end_idx]
                    
                    # 创建分页后的结果对象
                    try:
                        paginated_results = type(search_results)(
                            beatmapsets=paginated_beatmapsets,
                            cursor=getattr(search_results, 'cursor', None),
                            search=getattr(search_results, 'search', None),
                            recommended_difficulty=getattr(search_results, 'recommended_difficulty', None),
                            error=getattr(search_results, 'error', None),
                            total=getattr(search_results, 'total', None)
                        )
                    except Exception:
                        # 如果无法创建相同类型的对象，创建一个简单的对象
                        class SimpleSearchResult:
                            def __init__(self, beatmapsets, cursor=None):
                                self.beatmapsets = beatmapsets
                                self.cursor = cursor
                        
                        paginated_results = SimpleSearchResult(
                            beatmapsets=paginated_beatmapsets,
                            cursor=getattr(search_results, 'cursor', None)
                        )
                    
                    await self._process_search_results(event, paginated_results, num_per_page, page_num, "普通搜索")
                else:
                    await self._process_search_results(event, search_results, num_per_page, page_num, "普通搜索")
                
        except Exception as e:
            logger.error(f"搜索谱面失败: {e}")
            await event.send(MessageChain([Comp.Plain(
                f"❌ 搜索失败: {str(e)}\n"
                "请稍后重试"
            )]))

    async def _process_search_results(self, event: AstrMessageEvent, search_results, num_per_page: int, page_num: int, search_type: str):
        """
        处理搜索结果并发送消息
        
        Args:
            event: 消息事件
            search_results: 搜索结果对象
            num_per_page: 每页数量
            page_num: 页码
            search_type: 搜索类型（用于显示）
        """
        if not search_results or not hasattr(search_results, 'beatmapsets') or not search_results.beatmapsets:
            await event.send(MessageChain([Comp.Plain(
                f"🔍 {search_type}结果：未找到匹配的谱面"
            )]))
            return
        
        beatmapsets = search_results.beatmapsets
        total_found = len(beatmapsets)
        
        # 发送搜索概览
        cursor_info = ""
        if hasattr(search_results, 'cursor') and search_results.cursor:
            cursor_info = f"\n📄 搜索游标：{search_results.cursor}"
        
        overview_message = (
            f"🔍 {search_type}结果\n"
            f"📊 第 {page_num} 页，找到 {total_found} 个谱面集{cursor_info}\n"
            f"正在发送详细信息..."
        )
        await event.send(MessageChain([Comp.Plain(overview_message)]))
        
        # 逐个发送谱面集信息
        for i, beatmapset in enumerate(beatmapsets, 1):
            try:
                # 格式化谱面集信息
                cover_url, beatmapset_message = self._format_beatmapset_info(beatmapset)
                
                # 构建消息链
                chain = []
                if cover_url:
                    chain.append(Comp.Image.fromURL(cover_url))
                
                # 添加序号前缀
                prefixed_message = f"【{i}/{total_found}】\n{beatmapset_message}"
                chain.append(Comp.Plain(prefixed_message))
                
                # 发送单个谱面集信息
                await event.send(MessageChain(chain))
                
                # 稍微延迟避免发送过快
                if i < total_found:  # 最后一个不需要延迟
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"发送谱面集 {i} 信息失败: {e}")
                await event.send(MessageChain([Comp.Plain(
                    f"❌ 【{i}/{total_found}】发送谱面集信息失败: {str(e)}"
                )]))
        
        # 发送翻页提示
        if total_found == num_per_page:
            next_page_tip = f"\n💡 可能还有更多结果，使用 /osu search map <关键词> {num_per_page} {page_num + 1} 查看下一页"
            await event.send(MessageChain([Comp.Plain(
                f"✅ 搜索完成！{next_page_tip}"
            )]))
        else:
            await event.send(MessageChain([Comp.Plain("✅ 搜索完成！")]))

    async def _send_friend_info(self, event: AstrMessageEvent, friend, index: int, total: int, prefix: str):
        """
        发送单个好友的信息
        
        Args:
            event: 消息事件
            friend: 好友用户数据（UserExtended对象）
            index: 当前索引
            total: 总数
            prefix: 前缀图标
        """
        # 处理 UserExtended 对象
        if hasattr(friend, 'username'):
            # 直接从 UserExtended 对象获取用户信息
            username = friend.username or '未知'
            user_id = friend.id or '未知'
            is_online = friend.is_online
            avatar_url = friend.avatar_url
        elif isinstance(friend, dict):
            # 兼容字典格式
            username = friend.get('username', '未知')
            user_id = friend.get('id', '未知')
            is_online = friend.get('is_online', None)
            avatar_url = friend.get('avatar_url', None)
        else:
            # 其他格式兼容
            username = getattr(friend, 'username', '未知')
            user_id = getattr(friend, 'id', '未知')
            is_online = getattr(friend, 'is_online', None)
            avatar_url = getattr(friend, 'avatar_url', None)
        
        # 构建在线状态
        if is_online is True:
            online_status = "🟢 在线"
        elif is_online is False:
            online_status = "🔴 离线"
        else:
            online_status = "❓ 未知"
        
        # 检查好友是否在本机器人中绑定了账号
        friend_platform_id = self.link_account_manager.get_platform_id_by_osu(str(user_id))
        bind_status = f"🔗 已绑定: {friend_platform_id}" if friend_platform_id else "❌ 未绑定"
        
        friend_message = (
            f"{prefix} 【{index}/{total}】\n"
            f"🎮 用户名: {username}\n"
            f"📡 状态: {online_status}\n"
            f"{bind_status}"
        )
        
        # 构建消息链
        chain = []
        
        # 添加头像
        if avatar_url:
            chain.append(Comp.Image.fromURL(avatar_url))
        
        chain.append(Comp.Plain(friend_message))
        
        # 发送消息
        await event.send(MessageChain(chain))

    def _format_beatmap_info(self, beatmap_info) -> str:
        """
        格式化谱面信息为可读文本
        
        Args:
            beatmap_info: BeatmapExtended 对象
            
        Returns:
            str: 格式化后的谱面信息文本
        """
        # 基本信息
        basic_info = [
            "🗺️ 谱面信息:",
            f"🎵 标题: {beatmap_info.beatmapset.title if beatmap_info.beatmapset else '未知'}",
            f"👤 作者: {beatmap_info.beatmapset.artist if beatmap_info.beatmapset else '未知'}",
            f"⭐ 难度: {beatmap_info.version}",
            f"🆔 谱面ID: {beatmap_info.id}",
            f"🎯 谱面集ID: {beatmap_info.beatmapset_id}",
        ]
        
        # 制作者信息
        if beatmap_info.beatmapset and beatmap_info.beatmapset.creator:
            basic_info.append(f"🎨 制作者: {beatmap_info.beatmapset.creator}")
        
        # 难度统计
        if beatmap_info.difficulty_rating:
            basic_info.append(f"⭐ 星级: {beatmap_info.difficulty_rating:.2f}")
        
        # 谱面统计
        stats_info = []
        if beatmap_info.bpm:
            stats_info.append(f"🎼 BPM: {beatmap_info.bpm}")
        if beatmap_info.total_length:
            minutes = beatmap_info.total_length // 60
            seconds = beatmap_info.total_length % 60
            stats_info.append(f"⏱️ 长度: {minutes}:{seconds:02d}")
        if beatmap_info.count_circles is not None:
            stats_info.append(f"⭕ 圆圈: {beatmap_info.count_circles}")
        if beatmap_info.count_sliders is not None:
            stats_info.append(f"🔗 滑条: {beatmap_info.count_sliders}")
        if beatmap_info.count_spinners is not None:
            stats_info.append(f"🌀 转盘: {beatmap_info.count_spinners}")
        
        if stats_info:
            basic_info.append("")
            basic_info.append("📊 谱面统计:")
            basic_info.extend(stats_info)
        
        # 状态信息
        if hasattr(beatmap_info, 'status') and beatmap_info.status:
            status_map = {
                'graveyard': '⚰️ 坟场',
                'wip': '🚧 制作中',
                'pending': '⏳ 待审核',
                'ranked': '✅ Ranked',
                'approved': '👑 Approved',
                'qualified': '🔰 Qualified',
                'loved': '❤️ Loved'
            }
            status_text = status_map.get(beatmap_info.status, beatmap_info.status)
            basic_info.append(f"📋 状态: {status_text}")
        
        # 模式信息
        if hasattr(beatmap_info, 'mode') and beatmap_info.mode:
            mode_map = {
                'osu': '🎯 osu!',
                'taiko': '🥁 taiko',
                'fruits': '🍎 catch',
                'mania': '🎹 mania'
            }
            mode_text = mode_map.get(beatmap_info.mode, beatmap_info.mode)
            basic_info.append(f"🎮 模式: {mode_text}")
        
        return "\n".join(basic_info)

    def _format_beatmapset_info(self, beatmapset_info) -> tuple[str, str]:
        """
        格式化谱面集信息为可读文本
        
        Args:
            beatmapset_info: BeatmapsetExtended 对象
            
        Returns:
            tuple[str, str]: (cover_url, formatted_text) 封面URL和格式化后的谱面集信息文本
        """
        # 基本信息
        basic_info = [
            "🗂️ 谱面集信息:",
            f"🎵 标题: {beatmapset_info.title}",
            f"👤 艺术家: {beatmapset_info.artist}",
            f"🎨 制作者: {beatmapset_info.creator}",
            f"🆔 谱面集ID: {beatmapset_info.id}",
        ]
        
        # 状态信息
        if hasattr(beatmapset_info, 'status') and beatmapset_info.status:
            status_map = {
                'graveyard': '⚰️ 坟场',
                'wip': '🚧 制作中',
                'pending': '⏳ 待审核',
                'ranked': '✅ Ranked',
                'approved': '👑 Approved',
                'qualified': '🔰 Qualified',
                'loved': '❤️ Loved'
            }
            status_text = status_map.get(beatmapset_info.status, beatmapset_info.status)
            basic_info.append(f"📋 状态: {status_text}")
        
        # 日期信息
        if hasattr(beatmapset_info, 'submitted_date') and beatmapset_info.submitted_date:
            basic_info.append(f"📅 提交日期: {beatmapset_info.submitted_date[:10]}")
        if hasattr(beatmapset_info, 'ranked_date') and beatmapset_info.ranked_date:
            basic_info.append(f"🏆 Ranked日期: {beatmapset_info.ranked_date[:10]}")
        
        # 谱面统计
        if hasattr(beatmapset_info, 'beatmaps') and beatmapset_info.beatmaps:
            beatmaps = beatmapset_info.beatmaps
            basic_info.append("")
            basic_info.append(f"🗺️ 包含谱面数: {len(beatmaps)}")
            
            # 按模式分组统计
            mode_counts = {}
            difficulty_range = {'min': float('inf'), 'max': 0}
            
            for beatmap in beatmaps:
                mode = beatmap.get('mode', 'osu') if isinstance(beatmap, dict) else getattr(beatmap, 'mode', 'osu')
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
                
                # 统计难度范围
                diff_rating = beatmap.get('difficulty_rating', 0) if isinstance(beatmap, dict) else getattr(beatmap, 'difficulty_rating', 0)
                if diff_rating:
                    difficulty_range['min'] = min(difficulty_range['min'], diff_rating)
                    difficulty_range['max'] = max(difficulty_range['max'], diff_rating)
            
            # 显示模式分布
            mode_map = {
                'osu': '🎯 osu!',
                'taiko': '🥁 taiko', 
                'fruits': '🍎 catch',
                'mania': '🎹 mania'
            }
            
            mode_info = []
            for mode, count in mode_counts.items():
                mode_text = mode_map.get(mode, mode)
                mode_info.append(f"  {mode_text}: {count}个")
            
            if mode_info:
                basic_info.extend(mode_info)
            
            # 显示难度范围
            if difficulty_range['min'] != float('inf'):
                basic_info.append(f"⭐ 难度范围: {difficulty_range['min']:.2f} - {difficulty_range['max']:.2f}")
        
        # 统计信息
        stats_info = []
        if hasattr(beatmapset_info, 'play_count') and beatmapset_info.play_count:
            stats_info.append(f"▶️ 游玩次数: {beatmapset_info.play_count:,}")
        if hasattr(beatmapset_info, 'favourite_count') and beatmapset_info.favourite_count:
            stats_info.append(f"❤️ 收藏数: {beatmapset_info.favourite_count:,}")
        
        if stats_info:
            basic_info.append("")
            basic_info.append("📊 统计信息:")
            basic_info.extend(stats_info)
        
        # 获取封面图片URL
        cover_url = None
        if hasattr(beatmapset_info, 'covers') and beatmapset_info.covers:
            # 优先使用 cover_2x，其次 cover，最后 list_2x
            covers = beatmapset_info.covers
            cover_url = (covers.cover_2x or 
                        covers.cover or 
                        covers.list_2x or 
                        covers.list)
        
        return cover_url, "\n".join(basic_info)

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
                "  /osu users - 批量查询用户信息（对话模式）\n"
                "  /osu friend - 查看好友列表\n"
                "  /osu map <谱面ID> - 查看谱面信息\n"
                "  /osu mapset <谱面集ID> - 查看谱面集信息\n"
                "  /osu mapsets - 批量查询谱面集信息（对话模式）\n\n"
                "搜索功能:\n"
                "  /osu search map <关键词> [单页数量] [页码] [高级搜索] - 查询谱面\n"
                "成绩统计功能:\n"
                "  /osu update [模式] - 上传成绩到 OSU!track（默认 osu 模式）\n\n"
                "帮助:\n"
                "  /osu help [命令] - 查看帮助信息\n"
            )
        await event.send(MessageChain([Comp.Plain(help_text)]))

    async def terminate(self):
        return await super().terminate()