import aiohttp
import json
import asyncio
from typing import Tuple, Optional, Dict, Any
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

class OsuTrackAPI:
    """
    OsuTrack API
    """
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
    """
    Osu API
    """
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
        """
        更新用户成绩至 osu!track
        Args:
            user_id (str): 用户ID
            mode (int): 模式，0: osu!, 1: osu!taiko, 2: osu!catch, 3: osu!mania
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: 
                - 成功标志
                - 用户名
                - API响应数据
        Raises:
            ValueError: 如果模式参数转换失败
            Exception: 如果发生未知错误
        """
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
        
    async def search_beatmap(self, since: str = None, limit: int = 5, m: int = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        查询谱面，需要api_key
        Args:
            since (str): 查询时间
            limit (int): 返回数量
            m (int): 模式，0: osu!, 1: osu!taiko, 2: osu!catch, 3: osu!mania
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: 
                - 成功标志
                - 经过处理后的API响应数据
        Raises:
            ValueError: 如果模式参数转换失败
            aiohttp.ClientError: 如果网络请求失败
            json.JSONDecodeError: 如果JSON解析失败
            Exception: 如果发生未知错误
        """
        try:
            response = await self.osu.get_beatmaps(since=since, limit=limit, m=m, k=self.osu.api_key)
            if not response:
                logger.error(f"查询谱面失败: API返回空响应")
                return False, None, None
            # 将响应数据简化为需要的字段
            # 同一个"beatmapset_id"的谱面只保留一条
            beatmap_data = {}
            for beatmap in response:
                beatmapset_id = beatmap.get("beatmapset_id")
                if beatmapset_id not in beatmap_data:
                    beatmap_data[beatmapset_id] = {
                        "beatmapset_id": beatmap.get("beatmapset_id"),
                        "approved": beatmap.get("approved"),
                        "title": beatmap.get("title"),
                        "artist": beatmap.get("artist"),
                        "creator": beatmap.get("creator"),
                        "creator_id": beatmap.get("creator_id"),
                        "total_length": beatmap.get("total_length"),
                        "bpm": beatmap.get("bpm"),
                        "tags": beatmap.get("tags"),
                        "cover_url": f"https://assets.ppy.sh/beatmaps/{beatmapset_id}/covers/cover.jpg"
                    }
            return True, beatmap_data
        except ValueError as e:
            logger.error(f"查询谱面失败: 模式参数转换错误 - {str(e)}")
            return False, None
        except aiohttp.ClientError as e:
            logger.error(f"查询谱面失败: 网络请求错误 - {str(e)}")
            return False, None
        except json.JSONDecodeError as e:
            logger.error(f"查询谱面失败: JSON解析错误 - {str(e)}")
            return False, None         
        except Exception as e:
            logger.error(f"查询谱面时发生未知错误: {str(e)}")
            return False, None

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
        """
        上传成绩
        """
        result = await self.functions.update_user_score(user_id=user_id, mode=mode)
        if result[0]:
            newhs_count = len(result[2].get("newhs", []))
            osu_username = result[1]
            logger.info(f"成功更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩")
            yield event.plain_result(f"成功帮主人更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩喵~ 更新了 {newhs_count} 条新成绩喵呜")
        else:
            logger.warning(f"更新用户成绩失败: 用户ID {user_id}, 模式 {mode}, API返回空响应")
            yield event.plain_result(f"帮主人更新用户成绩失败了喵 用户ID {user_id}, 模式 {mode}, 不知道这个玩家玩过osu了没喵~")

    @filter.command("osu_beatmap")
    async def osu_beatmap(self, event: AstrMessageEvent, limit: int = 5, m: int = None, since: str = None):
        """
        查询谱面 需要api_key
        """
        if not self.api_key:
            logger.error("查询谱面失败: 未提供API密钥")
            yield event.plain_result("查询谱面失败了喵: 主人要提供API密钥小夜才可以查询谱面喵~")

        result = await self.functions.search_beatmap(since=since, limit=limit, m=m)
        if result[0]:
            beatmap_data = result[1]
            if beatmap_data:
                beatmap_list = []
                for beatmap in beatmap_data.values():
                    chain = [
                        Comp.Image.fromURL(beatmap["cover_url"]),
                        Comp.Plain("标题: " + beatmap["title"]),
                        Comp.Plain("艺术家: " + beatmap["artist"]),
                        Comp.Plain("作者: " + beatmap["creator"]+" (ID: " + str(beatmap["creator_id"]) + ")"),
                        Comp.Plain("谱面链接: " + f"https://osu.ppy.sh/beatmapsets/{beatmap['beatmapset_id']}"),
                        Comp.Plain("总时长: " + str(beatmap["total_length"]) + "秒"),
                        Comp.Plain("BPM: " + str(beatmap["bpm"])),
                        Comp.Plain("标签: " + beatmap["tags"]),
                        Comp.Plain("谱面状态: " + str(beatmap["approved"]))
                    ]
                    yield event.chain_result(chain)
                yield event.plain_result("查询谱面成功了喵~")
            else:
                yield event.plain_result("没有找到符合条件的谱面喵~")
        else:
            logger.warning(f"查询谱面失败: API返回空响应")
            yield event.plain_result("查询谱面失败了喵~")

    async def terminate(self):
        return await super().terminate()