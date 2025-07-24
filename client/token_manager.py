from astrbot.api import logger

import json
import os
import time
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class TokenData:
    """Token 数据结构"""
    access_token: str
    refresh_token: str
    expires_at: float  # Unix 时间戳
    token_type: str = "Bearer"
    scope: str = "public identify"

class TokenManager:
    """Token 存储和管理器"""
    
    def __init__(self):
        # 获取当前文件所在目录的二级父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_parent_dir = os.path.dirname(os.path.dirname(current_dir))
        self.token_file_path = os.path.join(parent_parent_dir, "osu_tokens.json")
        
        # 确保 token 文件存在
        self._ensure_token_file()
    
    def _ensure_token_file(self):
        """确保 token 文件存在"""
        if not os.path.exists(self.token_file_path):
            os.makedirs(os.path.dirname(self.token_file_path), exist_ok=True)
            initial_data = {}
            with open(self.token_file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def _load_tokens(self) -> Dict:
        """加载 token 数据"""
        try:
            with open(self.token_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._ensure_token_file()
            return {}
    
    def _save_tokens(self, data: Dict):
        """保存 token 数据"""
        with open(self.token_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_token(self, platform_id: str, token_data: TokenData):
        """保存用户的 token"""
        tokens = self._load_tokens()
        tokens[platform_id] = {
            "access_token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
            "expires_at": token_data.expires_at,
            "token_type": token_data.token_type,
            "scope": token_data.scope
        }
        self._save_tokens(tokens)
        logger.info(f"Token saved for platform_id: {platform_id}")
    
    def get_token(self, platform_id: str) -> Optional[TokenData]:
        """获取用户的 token"""
        tokens = self._load_tokens()
        token_dict = tokens.get(platform_id)
        if not token_dict:
            return None
        
        return TokenData(
            access_token=token_dict["access_token"],
            refresh_token=token_dict["refresh_token"],
            expires_at=token_dict["expires_at"],
            token_type=token_dict.get("token_type", "Bearer"),
            scope=token_dict.get("scope", "public identify")
        )
    
    def is_token_expired(self, platform_id: str) -> bool:
        """检查 token 是否过期"""
        token_data = self.get_token(platform_id)
        if not token_data:
            return True
        
        # 提前 5 分钟认为过期
        return time.time() >= (token_data.expires_at - 300)
    
    def remove_token(self, platform_id: str):
        """删除用户的 token"""
        tokens = self._load_tokens()
        if platform_id in tokens:
            del tokens[platform_id]
            self._save_tokens(tokens)
            logger.info(f"Token removed for platform_id: {platform_id}")
