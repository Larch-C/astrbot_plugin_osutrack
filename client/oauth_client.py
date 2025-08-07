from astrbot.api import logger

import aiohttp
import time
import urllib.parse
from typing import Optional, Dict, Any, List

from .token_manager import TokenManager, TokenData
from ..osuapi.enumtype import Scopes

class OsuOAuthClient:
    """OSU OAuth 客户端"""
    
    def __init__(self, client_id: int, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_manager = TokenManager()
        
        # OSU API 端点
        self.auth_url = "https://osu.ppy.sh/oauth/authorize"
        self.token_url = "https://osu.ppy.sh/oauth/token"
        self.api_base_url = "https://osu.ppy.sh/api/v2"
    
    def get_authorization_url(self, state: str = None, scopes: List[Scopes] = None) -> str:
        """
        生成授权 URL
        
        Args:
            state: 可选的状态参数
            scopes: 权限范围列表，默认包含 PUBLIC、IDENTIFY 和 FRIENDS
        
        Returns:
            str: 授权 URL
        """
        if scopes is None:
            # 默认包含基本权限和好友权限
            scopes = [Scopes.PUBLIC, Scopes.IDENTIFY, Scopes.FRIENDS]
        
        # 将枚举转换为字符串并用空格连接
        scope_string = " ".join([scope.value for scope in scopes])
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope_string
        }
        
        if state:
            params["state"] = state
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> TokenData:
        """用授权码换取访问令牌"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Token exchange failed: {response.status} - {error_text}")
                
                token_response = await response.json()
                
                # 计算过期时间
                expires_in = token_response.get("expires_in", 86400)
                expires_at = time.time() + expires_in
                
                return TokenData(
                    access_token=token_response["access_token"],
                    refresh_token=token_response["refresh_token"],
                    expires_at=expires_at,
                    token_type=token_response.get("token_type", "Bearer"),
                    scope=token_response.get("scope", "public identify friends.read")
                )
    
    async def refresh_token(self, platform_id: str) -> Optional[TokenData]:
        """刷新访问令牌"""
        token_data = self.token_manager.get_token(platform_id)
        if not token_data or not token_data.refresh_token:
            return None
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token_data.refresh_token,
            "scope": token_data.scope or "public identify friends.read"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Token refresh failed: {response.status}")
                    return None
                
                token_response = await response.json()
                
                # 计算过期时间
                expires_in = token_response.get("expires_in", 86400)
                expires_at = time.time() + expires_in
                
                new_token_data = TokenData(
                    access_token=token_response["access_token"],
                    refresh_token=token_response["refresh_token"],
                    expires_at=expires_at,
                    token_type=token_response.get("token_type", "Bearer"),
                    scope=token_response.get("scope", token_data.scope or "public identify friends.read")
                )
                
                # 保存新的 token
                self.token_manager.save_token(platform_id, new_token_data)
                logger.info(f"Token refreshed for platform_id: {platform_id}")
                
                return new_token_data
    
    async def get_valid_token(self, platform_id: str) -> Optional[TokenData]:
        """获取有效的访问令牌（自动刷新过期的令牌）"""
        if self.token_manager.is_token_expired(platform_id):
            logger.info(f"Token expired for platform_id: {platform_id}, refreshing...")
            return await self.refresh_token(platform_id)
        
        return self.token_manager.get_token(platform_id)
    
    async def get_user_info(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        token_data = await self.get_valid_token(platform_id)
        if not token_data:
            return None
        
        headers = {
            "Authorization": f"Bearer {token_data.access_token}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/me", headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get user info: {response.status}")
                    return None
                
                return await response.json()
    
    def save_token(self, platform_id: str, token_data: TokenData):
        """保存 token"""
        self.token_manager.save_token(platform_id, token_data)
    
    def remove_token(self, platform_id: str):
        """删除 token"""
        self.token_manager.remove_token(platform_id)
