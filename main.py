import aiohttp
import json
import asyncio
from typing import Tuple, Optional, Dict, Any
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

class OsuTrackAPI:
    def __init__(self):
        self.api_url = "https://osutrack-api.ameo.dev/"

    async def update(self, user: str, mode: int = 0):
        url = f"{self.api_url}update"
        params = {
            "user": user,
            "mode": str(mode)
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"OsuTrack API update失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"OsuTrack API update请求异常: {str(e)}, 参数: {params}")
            return None

class OsuAPI:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.api_url = "https://osu.ppy.sh/p/api/"

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    async def get_beatmaps(self, k: str = None, since: str = None, s: int = None, b: int = None, u: str = None, type: str = None, m: int = None, a: int = 0, h: str = None, limit: int = 500, mods: int = 0):
        url = f"{self.api_url}get_beatmaps"
        params = {
            "k": self.api_key if k is None else k,
            "since": since,
            "s": s,
            "b": b,
            "u": u,
            "type": type,
            "m": m,
            "a": a,
            "h": h,
            "limit": limit,
            "mods": mods
        }
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_beatmaps失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_beatmaps请求异常: {str(e)}, 参数: {params}")
            return None

class PluginFunctions:
    def __init__(self):
        self.osutrack = OsuTrackAPI()
        self.osu = OsuAPI(api_key=None)

    def set_api_key(self, api_key):
        self.osu.set_api_key(api_key)

    async def update_user_score(self, user_id: str, mode: int = 0) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        if not user_id:
            logger.error("更新用户成绩失败: 未提供用户ID")
            return False, None, None
            
        try:
            mode_int = int(mode)
            if mode_int not in [0, 1, 2, 3]:
                logger.warning(f"更新用户成绩: 无效的模式值 {mode}，将使用默认模式 0")
                mode_int = 0
                
            response: Optional[Dict[str, Any]] = await self.osutrack.update(user_id, mode_int)
            
            if not response:
                logger.error(f"更新用户成绩失败: 用户ID {user_id}, 模式 {mode_int}, API返回空响应")
                return False, None, None
                
            username = response.get("username")
            exists = response.get("exists", False)
            
            if exists:
                logger.info(f"成功更新用户 {username} (ID: {user_id}) 在模式 {mode_int} 的成绩")
                return True, username, response
            else:
                logger.warning(f"用户 {username or user_id} 在模式 {mode_int} 无成绩更新")
                return False, username, response
                
        except ValueError as e:
            logger.error(f"更新用户成绩失败: 模式参数转换错误 - {str(e)}")
            return False, None, None
        except Exception as e:
            logger.error(f"更新用户成绩时发生未知错误: {str(e)}")
            return False, None, None

@register("osutrack","gameswu","基于osu!track与osu!api的osu!成绩查询插件","0.1.0","https://github.com/gameswu/astrbot_plugin_osutrack")
class OsuTrackPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        self.api_key = self.config.get("api_key")
        self.functions = PluginFunctions()
        self.functions.set_api_key(api_key=self.api_key)

    @filter.command("osu_update")
    async def osu_update(self, event: AstrMessageEvent, user_id: str, mode: int):
        result = await self.functions.update_user_score(user_id=user_id, mode=mode)
        if result[0]:
            newhs_count = len(result[2].get("newhs", []))
            osu_username = result[1]
            logger.info(f"成功更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩")
            yield event.plain_result(f"成功帮主人更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩喵~ 更新了 {newhs_count} 条新成绩喵呜")
        else:
            logger.warning(f"更新用户成绩失败: 用户ID {user_id}, 模式 {mode}, API返回空响应")
            yield event.plain_result(f"帮主人更新用户成绩失败了喵 用户ID {user_id}, 模式 {mode}, API返回没有响应喵")

    async def terminate(self):
        return await super().terminate()