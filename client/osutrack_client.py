from astrbot.api import logger

from typing import Optional, List, Union
from datetime import datetime
import aiohttp

from ..osutrackapi import (
    GameMode, UserMode, UpdateResponse, StatsUpdate, 
    RecordedScore, PeakData, BestPlay
)


class OsuTrackClient:
    """OSU Track API 客户端"""
    
    def __init__(self):
        """初始化 OSU Track 客户端"""
        self.base_url = "https://osutrack-api.ameo.dev"
    
    async def _make_request(self, endpoint: str, method: str = "GET", 
                           params: Optional[dict] = None) -> dict:
        """
        发起 API 请求的通用方法
        
        Args:
            endpoint: API 端点路径
            method: HTTP 方法，默认为 GET
            params: URL 查询参数
            
        Returns:
            dict: API 响应数据
            
        Raises:
            Exception: API 请求失败
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"OSU Track API request failed: {response.status} - {error_text}")
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                elif method.upper() == "POST":
                    async with session.post(url, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"OSU Track API request failed: {response.status} - {error_text}")
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
        except Exception as e:
            logger.error(f"Error making OSU Track API request to {url}: {e}")
            raise

    async def update_user(self, user: Union[int, str], mode: Union[GameMode, int]) -> UpdateResponse:
        """
        更新用户数据
        
        Args:
            user: 用户 ID
            mode: 游戏模式（GameMode 枚举或整数）
            
        Returns:
            UpdateResponse: 更新响应，包含统计差异和新的高分记录
            
        Raises:
            Exception: API 请求失败
        """
        if isinstance(mode, GameMode):
            mode_value = mode.value
        else:
            mode_value = int(mode)
        
        params = {
            'user': str(user),
            'mode': str(mode_value)
        }
        
        try:
            logger.info(f"Updating user {user} for mode {mode_value}")
            response_data = await self._make_request("update", method="POST", params=params)
            
            update_response = UpdateResponse.from_dict(response_data)
            
            logger.info(f"Successfully updated user {update_response.username} (exists: {update_response.exists})")
            return update_response
            
        except Exception as e:
            logger.error(f"Failed to update user {user}: {e}")
            raise

    async def get_stats_history(self, user: Union[int, str], mode: Union[GameMode, int],
                               from_date: Optional[str] = None, 
                               to_date: Optional[str] = None) -> List[StatsUpdate]:
        """
        获取用户的统计历史记录
        
        Args:
            user: 用户 ID
            mode: 游戏模式（GameMode 枚举或整数）
            from_date: 开始日期，格式为 YYYY-MM-DD，可选
            to_date: 结束日期，格式为 YYYY-MM-DD，可选
            
        Returns:
            List[StatsUpdate]: 统计更新记录列表
            
        Raises:
            Exception: API 请求失败
        """
        if isinstance(mode, GameMode):
            mode_value = mode.value
        else:
            mode_value = int(mode)
        
        params = {
            'user': str(user),
            'mode': str(mode_value)
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        try:
            logger.info(f"Fetching stats history for user {user} in mode {mode_value}")
            response_data = await self._make_request("stats_history", params=params)
            
            stats_updates = []
            if isinstance(response_data, list):
                for update_data in response_data:
                    stats_updates.append(StatsUpdate.from_dict(update_data))
            
            logger.info(f"Successfully fetched {len(stats_updates)} stats updates")
            return stats_updates
            
        except Exception as e:
            logger.error(f"Failed to fetch stats history for user {user}: {e}")
            raise

    async def get_hiscores(self, user: Union[int, str], mode: Union[GameMode, int],
                          from_date: Optional[str] = None, to_date: Optional[str] = None,
                          user_mode: UserMode = UserMode.ID) -> List[RecordedScore]:
        """
        获取用户的所有记录分数
        
        Args:
            user: 用户 ID 或用户名
            mode: 游戏模式（GameMode 枚举或整数）
            from_date: 开始日期，格式为 YYYY-MM-DD，可选
            to_date: 结束日期，格式为 YYYY-MM-DD，可选
            user_mode: 用户查询模式，默认为 ID
            
        Returns:
            List[RecordedScore]: 记录分数列表
            
        Raises:
            Exception: API 请求失败
        """
        if isinstance(mode, GameMode):
            mode_value = mode.value
        else:
            mode_value = int(mode)
        
        params = {
            'user': str(user),
            'mode': str(mode_value),
            'userMode': user_mode.value
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        try:
            logger.info(f"Fetching hiscores for user {user} in mode {mode_value}")
            response_data = await self._make_request("hiscores", params=params)
            
            recorded_scores = []
            if isinstance(response_data, list):
                for score_data in response_data:
                    recorded_scores.append(RecordedScore.from_dict(score_data))
            
            logger.info(f"Successfully fetched {len(recorded_scores)} recorded scores")
            return recorded_scores
            
        except Exception as e:
            logger.error(f"Failed to fetch hiscores for user {user}: {e}")
            raise

    async def get_peak(self, user: Union[int, str], mode: Union[GameMode, int]) -> PeakData:
        """
        获取用户的峰值排名和准确率
        
        Args:
            user: 用户 ID
            mode: 游戏模式（GameMode 枚举或整数）
            
        Returns:
            PeakData: 峰值数据
            
        Raises:
            Exception: API 请求失败
        """
        if isinstance(mode, GameMode):
            mode_value = mode.value
        else:
            mode_value = int(mode)
        
        params = {
            'user': str(user),
            'mode': str(mode_value)
        }
        
        try:
            logger.info(f"Fetching peak data for user {user} in mode {mode_value}")
            response_data = await self._make_request("peak", params=params)
            
            # API 返回数组，取第一个元素
            if isinstance(response_data, list) and len(response_data) > 0:
                peak_data = PeakData.from_dict(response_data[0])
            else:
                # 如果没有数据，创建空的峰值数据
                peak_data = PeakData.from_dict({})
            
            logger.info(f"Successfully fetched peak data for user {user}")
            return peak_data
            
        except Exception as e:
            logger.error(f"Failed to fetch peak data for user {user}: {e}")
            raise

    async def get_best_plays(self, mode: Union[GameMode, int],
                            from_date: Optional[str] = None, to_date: Optional[str] = None,
                            limit: Optional[int] = None) -> List[BestPlay]:
        """
        获取指定模式下所有用户的最佳游戏记录
        
        Args:
            mode: 游戏模式（GameMode 枚举或整数）
            from_date: 开始日期，格式为 YYYY-MM-DD，可选
            to_date: 结束日期，格式为 YYYY-MM-DD，可选
            limit: 返回记录数量限制，1-10000，可选
            
        Returns:
            List[BestPlay]: 最佳游戏记录列表，按 PP 值降序排列
            
        Raises:
            Exception: API 请求失败
        """
        if isinstance(mode, GameMode):
            mode_value = mode.value
        else:
            mode_value = int(mode)
        
        params = {
            'mode': str(mode_value)
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        if limit is not None:
            if not (1 <= limit <= 10000):
                raise ValueError("limit must be between 1 and 10000")
            params['limit'] = str(limit)
        
        try:
            logger.info(f"Fetching best plays for mode {mode_value}")
            response_data = await self._make_request("bestplays", params=params)
            
            best_plays = []
            if isinstance(response_data, list):
                for play_data in response_data:
                    best_plays.append(BestPlay.from_dict(play_data))
            
            logger.info(f"Successfully fetched {len(best_plays)} best plays")
            return best_plays
            
        except Exception as e:
            logger.error(f"Failed to fetch best plays for mode {mode_value}: {e}")
            raise

    # 便捷方法
    async def update_user_osu(self, user: Union[int, str]) -> UpdateResponse:
        """更新用户的 osu! 模式数据"""
        return await self.update_user(user, GameMode.OSU)

    async def update_user_taiko(self, user: Union[int, str]) -> UpdateResponse:
        """更新用户的 taiko 模式数据"""
        return await self.update_user(user, GameMode.TAIKO)

    async def update_user_ctb(self, user: Union[int, str]) -> UpdateResponse:
        """更新用户的 catch the beat 模式数据"""
        return await self.update_user(user, GameMode.CTB)

    async def update_user_mania(self, user: Union[int, str]) -> UpdateResponse:
        """更新用户的 mania 模式数据"""
        return await self.update_user(user, GameMode.MANIA)