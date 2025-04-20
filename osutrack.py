# 调用osu!track的API的方法，API文档：https://github.com/Ameobea/osutrack-api
# 调用osu!api的API的方法，API文档：https://github.com/ppy/osu-api/wiki#apiget_scores
import aiohttp
import json
import asyncio
from astrbot import logger

class OsuTrackAPI:
    def __init__(self):
        self.api_url = "https://osutrack-api.ameo.dev/"

    # 更新用户信息
    # @param user: 用户ID 必填
    # @param mode: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 必填
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
        
    # 获取所有上传的历史结果
    # @param user: 用户ID 必填
    # @param mode: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 必填
    # @param from: 起始时间戳YYYY-MM-DD
    # @param to: 结束时间戳YYYY-MM-DD
    async def stats_history(self, user: str, mode: int = 0, from_date: str = None, to_date: str = None):
        url = f"{self.api_url}stats_history"
        params = {
            "user": user,
            "mode": str(mode)
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"OsuTrack API stats_history失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"OsuTrack API stats_history请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取用户的历史高分
    # @param user: 用户ID或用户名，由userMode决定 必填
    # @param mode: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 必填
    # @param from: 起始时间戳YYYY-MM-DD
    # @param to: 结束时间戳YYYY-MM-DD
    # @param userMode: 用户ID或用户名的模式 id 或 username 默认为id
    async def hiscores(self, user: str, mode: int = 0, from_date: str = None, to_date: str = None, userMode: str = "id"):
        url = f"{self.api_url}hiscores"
        params = {
            "user": user,
            "mode": str(mode),
            "userMode": userMode
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"OsuTrack API hiscores失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"OsuTrack API hiscores请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取历史记录最佳排名和准确率
    # @param user: 用户ID 必填
    # @param mode: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 必填
    async def peak(self, user: str, mode: int = 0):
        url = f"{self.api_url}peak"
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
                        logger.error(f"OsuTrack API peak失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"OsuTrack API peak请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取根据pp值的某模式的前limit名玩家的成绩
    # @param mode: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 必填
    # @param from: 起始时间戳YYYY-MM-DD
    # @param to: 结束时间戳YYYY-MM-DD
    # @param limit: 数量限制 1~10000 必填
    async def bestplays(self, mode: int = 0, from_date: str = None, to_date: str = None, limit: int = 1):
        url = f"{self.api_url}bestplays"
        params = {
            "mode": str(mode),
            "limit": str(limit)
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"OsuTrack API bestplays失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"OsuTrack API bestplays请求异常: {str(e)}, 参数: {params}")
            return None
        
class OsuAPI:
    def __init__(self, api_key: str = None):
        self.api_key = api_key # 需要osu!api的key才能使用
        self.api_url = "https://osu.ppy.sh/p/api/" # osu!api的v1版本，未来可能废弃

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    # 获取谱面
    # @param k: osu!api的key 必填
    # @param since: 返回所有在该时间之后的rank谱面或社区喜爱谱面，MySQL的时间戳格式，UTC时间
    # @param s: 谱面集ID
    # @param b: 谱面ID
    # @param u: 用户ID或用户名
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认返回所有模式地图
    # @param a: 指定是否包含转谱图，仅在m被指定且不为0时有效，0: 不包含 1: 包含 默认为0
    # @param h: 指定返回谱面的hash值，默认情况下所有谱面都返回hash值
    # @param limit: 返回的谱面数量限制，默认和最大值均为500
    # @param mods: 指定谱面使用的mod，默认为0
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
        # 移除None值的参数
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
        
    # 获取谱面封面图
    # @param s: 谱面集ID
    def cover_img(self, s: int):
        # 直接返回封面图的url
        return f"https://assets.ppy.sh/beatmaps/{s}/covers/cover.jpg"
        
    # 获取谱面封面缩略图
    # @param s: 谱面集ID
    def cover_thumb_img(self, s: int):
        # 直接返回封面缩略图的url
        return f"https://b.ppy.sh/thumb/{s}l.jpg"
    
    # 获取用户信息
    # @param k: osu!api的key 必填
    # @param u: 用户ID或用户名 必填
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认为0
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    # @param event_days: 指定从现在开始最大的天数范围内的活动，范围1～31，默认1
    async def get_user(self, k: str = None, u: str = None, m: int = 0, type: str = None, event_days: int = 1):
        url = f"{self.api_url}get_user"
        params = {
            "k": self.api_key if k is None else k,
            "u": u,
            "m": m,
            "type": type,
            "event_days": event_days
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_user失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_user请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取用户配置图像
    # @param uid: 用户ID
    def user_profile_img(self, uid: int):
        # 直接返回用户配置图像的url
        return f"https://a.ppy.sh/{uid}"
    
    # 获取谱面分数排行
    # @param k: osu!api的key 必填
    # @param b: 谱面ID 必填
    # @param u: 用户ID或用户名
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认为0
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    # @param limit: 返回的谱面数量限制，范围1~100，默认为50
    async def get_scores(self, k: str = None, b: int = None, u: str = None, m: int = 0, type: str = None, limit: int = 50):
        url = f"{self.api_url}get_scores"
        params = {
            "k": self.api_key if k is None else k,
            "b": b,
            "u": u,
            "m": m,
            "type": type,
            "limit": limit
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_scores失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_scores请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取用户最近的高分
    # @param k: osu!api的key 必填
    # @param u: 用户ID或用户名 必填
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认为0
    # @param limit: 返回的谱面数量限制，范围1~100，默认为10
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    async def get_user_best(self, k: str = None, u: str = None, m: int = 0, limit: int = 10, type: str = None):
        url = f"{self.api_url}get_user_best"
        params = {
            "k": self.api_key if k is None else k,
            "u": u,
            "m": m,
            "limit": limit,
            "type": type
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_user_best失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_user_best请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取用户最近一天内的成绩
    # @param k: osu!api的key 必填
    # @param u: 用户ID或用户名 必填
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认为0
    # @param limit: 返回的谱面数量限制，范围1~50，默认为10
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    async def get_user_recent(self, k: str = None, u: str = None, m: int = 0, limit: int = 10, type: str = None):
        url = f"{self.api_url}get_user_recent"
        params = {
            "k": self.api_key if k is None else k,
            "u": u,
            "m": m,
            "limit": limit,
            "type": type
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_user_recent失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_user_recent请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取多人游戏信息
    # @param k: osu!api的key 必填
    # @param mp: 多人游戏ID 必填
    async def get_match(self, k: str = None, mp: str = None):
        url = f"{self.api_url}get_match"
        params = {
            "k": self.api_key if k is None else k,
            "mp": mp
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_match失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_match请求异常: {str(e)}, 参数: {params}")
            return None
        
    # 获取回放数据
    # @param k: osu!api的key 必填
    # @param b: 谱面ID 必填
    # @param u: 用户ID或用户名 必填
    # @param m: 模式 0: osu! 1: osu!taiko 2: osu!catch 3: osu!mania 默认自动解析
    # @param type: 指明u的类型为 id 或 string，默认自动解析，用于处理用户名完全为数字的情况
    # @param mods: 指定谱面使用的mod，默认自动解析
    async def get_replay(self, k: str = None, b: int = None, u: str = None, m: int = 0, type: str = None, mods: int = 0):
        url = f"{self.api_url}get_replay"
        params = {
            "k": self.api_key if k is None else k,
            "b": b,
            "u": u,
            "m": m,
            "type": type,
            "mods": mods
        }
        # 移除None值的参数
        params = {k: v for k, v in params.items() if v is not None}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Osu API get_replay失败: 状态码 {response.status}, 参数: {params}, 响应: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Osu API get_replay请求异常: {str(e)}, 参数: {params}")
            return None