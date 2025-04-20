# 调用osutrack.py获取的json数据进行处理
import osutrack
import json
from typing import Tuple, Optional, Dict, Any
from astrbot import logger

class PluginFunctions:
    def __init__(self):
        self.osutrack = osutrack.OsuTrackAPI()
        self.osu = osutrack.OsuAPI(api_key=None)

    def set_api_key(self, api_key):
        self.osu.set_api_key(api_key)

    async def update_user_score(self, user_id: str, mode: int = 0) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        更新用户成绩至osu!track并返回详细结果
        
        Args:
            user_id: osu!用户ID
            mode: 游戏模式 (0: osu!, 1: taiko, 2: catch, 3: mania)
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
                - 布尔值表示更新是否成功
                - 用户名（如果有）
                - 更新详情数据（如果有）
        """
        if not user_id:
            logger.error("更新用户成绩失败: 未提供用户ID")
            return False, None, None
            
        try:
            # 转换模式参数为整数，确保类型正确
            mode_int = int(mode)
            if mode_int not in [0, 1, 2, 3]:
                logger.warning(f"更新用户成绩: 无效的模式值 {mode}，将使用默认模式 0")
                mode_int = 0
                
            response: Optional[Dict[str, Any]] = await self.osutrack.update(user_id, mode_int)
            
            if not response:
                logger.error(f"更新用户成绩失败: 用户ID {user_id}, 模式 {mode_int}, API返回空响应")
                return False, None, None
                
            # 检查用户是否存在
            username = response.get("username")
            exists = response.get("exists", False)
            
            if exists:
                logger.info(f"成功更新用户 {username} (ID: {user_id}) 在模式 {mode_int} 的成绩")
                return True, username, response
            else:
                logger.warning(f"用户 {username or user_id} 在模式 {mode_int} 无成绩更新")
                return False, username, response
                
        except ValueError as e:
            # 处理模式转换错误
            logger.error(f"更新用户成绩失败: 模式参数转换错误 - {str(e)}")
            return False, None, None
        except Exception as e:
            # 处理所有其他错误
            logger.error(f"更新用户成绩时发生未知错误: {str(e)}")
            return False, None, None
        
    # 检索谱面
    async def search_beatmap(self, since: str = None, user: str = None, type: str = None, m: int = None, a: int = 0, limit: int = 1) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        检索谱面
        
        Args:
            since: 起始时间
            user: 用户名
            type: 类型
            m: 模式
            a: 是否包含转谱
            limit: 返回结果数量
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
                - 布尔值表示检索是否成功
                - 返回谱面详细数据（如果有）
                - 返回谱面封面图片url（如果有）
        """
        try:
            response: Optional[Dict[str, Any]] = await self.osu.get_beatmaps(k=self.osu.api_key, since=since, s=None, b=None, u=user, type=type, m=m, a=a, limit=limit)
            if response:
                beatmapset_id: int = response.get("beatmapset_id")
                img_url = self.osu.cover_img(beatmapset_id)
                if img_url:
                    logger.info(f"成功检索谱面: {response}, 封面图片: {img_url}")
                else:
                    logger.warning(f"检索谱面成功，但未找到封面图片: {response}")
                return True, response, img_url
            else:
                logger.warning("检索谱面失败: 无响应或数据为空")
                return False, None, None
        except ValueError as e:
            logger.error(f"检索谱面失败: 参数转换错误 - {str(e)}")
            return False, None, None
        except KeyError as e:
            logger.error(f"检索谱面失败: 缺少必要的键 - {str(e)}")
            return False, None, None
        except TypeError as e:
            logger.error(f"检索谱面失败: 类型错误 - {str(e)}")
            return False, None, None
        except Exception as e:
            logger.error(f"检索谱面时发生错误: {str(e)}")
            return False, None, None