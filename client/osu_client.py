from astrbot.api import logger

from typing import Optional, Dict, Any, Union
import json
from aiohttp import ClientSession

from ..osuapi.user import UserExtended
from .token_manager import TokenManager


class OsuClient:
    """OSU API 客户端，专注于 API 调用功能"""
    
    def __init__(self, token_manager: Optional[TokenManager] = None):
        """
        初始化 OSU API 客户端
        
        Args:
            token_manager: Token 管理器实例，如果不提供会自动创建
        """
        self.token_manager = token_manager or TokenManager()
        self.api_base_url = "https://osu.ppy.sh/api/v2"

    def _get_valid_token(self, platform_id: str) -> Optional[str]:
        """
        获取有效的访问令牌
        
        Args:
            platform_id: 平台用户 ID
            
        Returns:
            Optional[str]: 有效的访问令牌，如果没有或已过期则返回 None
        """
        if self.token_manager.is_token_expired(platform_id):
            logger.warning(f"Token for platform_id {platform_id} is expired or not found")
            return None
        
        token_data = self.token_manager.get_token(platform_id)
        return token_data.access_token if token_data else None

    def _check_scope_permission(self, platform_id: str, required_scope: str) -> bool:
        """
        检查令牌是否具有所需的权限范围
        
        Args:
            platform_id: 平台用户 ID
            required_scope: 所需的权限范围
            
        Returns:
            bool: 如果具有所需权限返回 True，否则返回 False
        """
        token_data = self.token_manager.get_token(platform_id)
        if not token_data:
            return False
        
        # 检查 scope 字符串中是否包含所需权限
        token_scopes = token_data.scope.split() if token_data.scope else []
        return required_scope in token_scopes

    async def _make_api_request(self, platform_id: str, endpoint: str, method: str = "GET", 
                               params: Optional[Dict[str, Any]] = None,
                               data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发起 API 请求的通用方法
        
        Args:
            platform_id: 平台用户 ID，用于获取对应的访问令牌
            endpoint: API 端点路径（相对于 https://osu.ppy.sh/api/v2/）
            method: HTTP 方法，默认为 GET
            params: URL 查询参数
            data: 请求体数据（用于 POST/PUT 等请求）
            
        Returns:
            Dict[str, Any]: API 响应数据
            
        Raises:
            ValueError: 如果没有有效的 token
            Exception: API 请求失败
        """
        access_token = self._get_valid_token(platform_id)
        if not access_token:
            raise ValueError(f"No valid token available for platform_id {platform_id}. Please authenticate first.")
        
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with ClientSession() as session:
                if method.upper() == "GET":
                    # 处理数组参数（如 ids[]）
                    if params:
                        processed_params = []
                        for key, value in params.items():
                            if isinstance(value, list):
                                for item in value:
                                    processed_params.append((key, item))
                            else:
                                processed_params.append((key, value))
                        params = processed_params
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"API request failed: {response.status} - {error_text}")
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                elif method.upper() == "POST":
                    json_data = json.dumps(data) if data else None
                    async with session.post(url, headers=headers, params=params, data=json_data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"API request failed: {response.status} - {error_text}")
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                # 可以在这里添加其他 HTTP 方法的支持
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
        except Exception as e:
            logger.error(f"Error making API request to {url}: {e}")
            raise

    async def get_user(self, platform_id: str, user: Union[int, str], mode: Optional[str] = None, 
                      key: Optional[str] = None) -> UserExtended:
        """
        获取指定用户的详细信息（需要 public 权限）
        
        Args:
            platform_id: 平台用户 ID，用于获取对应的访问令牌
            user: 用户 ID 或用户名。如果是用户名，建议在前面加上 @ 前缀
            mode: 游戏模式，可选值：osu, taiko, fruits, mania。如果不指定，使用用户的默认模式
            key: 查找类型，可选值：id, username。已弃用，建议使用 @ 前缀代替
            
        Returns:
            UserExtended: 用户详细信息对象
            
        Raises:
            ValueError: 参数错误或没有有效 token
            Exception: API 请求失败
            
        Note:
            此 API 需要 'public' 权限范围
        """
        # 处理用户参数
        if isinstance(user, str):
            # 如果是字符串且不以 @ 开头，自动添加 @ 前缀以明确表示用户名查找
            if not user.startswith('@') and not user.isdigit():
                user = f"@{user}"
        
        # 构建端点路径
        endpoint = f"users/{user}"
        if mode:
            endpoint += f"/{mode}"
        
        # 构建查询参数
        params = {}
        if key:
            params['key'] = key
        
        try:
            logger.info(f"Fetching user info for: {user} (platform_id: {platform_id})")
            response_data = await self._make_api_request(
                platform_id, endpoint, params=params if params else None
            )
            
            # 转换为 UserExtended 对象
            user_obj = UserExtended.from_dict(response_data)
            
            logger.info(f"Successfully fetched user info for: {user_obj.username} (ID: {user_obj.id})")
            return user_obj
            
        except Exception as e:
            logger.error(f"Failed to fetch user info for {user}: {e}")
            raise

    async def get_user_by_id(self, platform_id: str, user_id: int, mode: Optional[str] = None) -> UserExtended:
        """
        通过用户 ID 获取用户信息
        
        Args:
            platform_id: 平台用户 ID
            user_id: OSU 用户 ID
            mode: 游戏模式
            
        Returns:
            UserExtended: 用户详细信息对象
        """
        return await self.get_user(platform_id, user_id, mode)

    async def get_user_by_username(self, platform_id: str, username: str, mode: Optional[str] = None) -> UserExtended:
        """
        通过用户名获取用户信息
        
        Args:
            platform_id: 平台用户 ID
            username: OSU 用户名
            mode: 游戏模式
            
        Returns:
            UserExtended: 用户详细信息对象
        """
        # 确保用户名有 @ 前缀
        if not username.startswith('@'):
            username = f"@{username}"
        return await self.get_user(platform_id, username, mode)

    async def get_users(self, platform_id: str, user_ids: list[Union[int, str]], 
                       include_variant_statistics: bool = False) -> list[UserExtended]:
        """
        批量获取用户信息（需要 public 权限）
        
        Args:
            platform_id: 平台用户 ID，用于获取对应的访问令牌
            user_ids: 用户 ID 列表，最多支持 50 个用户
            include_variant_statistics: 是否包含变体统计信息，默认为 False
            
        Returns:
            list[UserExtended]: 用户详细信息对象列表
            
        Raises:
            ValueError: 参数错误或没有有效 token
            Exception: API 请求失败
            
        Note:
            此 API 需要 'public' 权限范围
        """
        if not user_ids:
            raise ValueError("user_ids cannot be empty")
        
        if len(user_ids) > 50:
            raise ValueError("Maximum 50 users can be requested at once")
        
        # 构建查询参数
        params = {}
        # 添加用户 ID 数组参数
        params['ids[]'] = [str(user_id) for user_id in user_ids]
        
        # 添加变体统计信息参数
        if include_variant_statistics:
            params['include_variant_statistics'] = 'true'
        
        try:
            logger.info(f"Fetching {len(user_ids)} users info (platform_id: {platform_id})")
            response_data = await self._make_api_request(platform_id, "users", params=params)
            
            # 转换为 UserExtended 对象列表
            users = []
            if 'users' in response_data and isinstance(response_data['users'], list):
                for user_data in response_data['users']:
                    user_obj = UserExtended.from_dict(user_data)
                    users.append(user_obj)
            
            logger.info(f"Successfully fetched {len(users)} users info")
            return users
            
        except Exception as e:
            logger.error(f"Failed to fetch users info for {user_ids}: {e}")
            raise

    async def get_own_data(self, platform_id: str, mode: Optional[str] = None) -> UserExtended:
        """
        获取当前认证用户的数据（需要 identify 权限）
        
        Args:
            platform_id: 平台用户 ID，用于获取对应的访问令牌
            mode: 游戏模式，可选值：osu, taiko, fruits, mania。如果不指定，使用用户的默认模式
            
        Returns:
            UserExtended: 当前用户的详细信息对象
            
        Raises:
            ValueError: 没有有效 token 或权限不足
            Exception: API 请求失败
            
        Note:
            此 API 需要 'identify' 权限范围
            返回的数据包含 session_verified 属性和所有游戏模式的统计信息
        """
        # 检查是否具有 identify 权限
        if not self._check_scope_permission(platform_id, "identify"):
            raise ValueError(f"Token for platform_id {platform_id} does not have 'identify' scope required for /me endpoint")
        
        # 构建端点路径
        endpoint = "me"
        if mode:
            endpoint += f"/{mode}"
        
        try:
            logger.info(f"Fetching own user data (platform_id: {platform_id})")
            response_data = await self._make_api_request(platform_id, endpoint)
            
            # 转换为 UserExtended 对象
            user_obj = UserExtended.from_dict(response_data)
            
            logger.info(f"Successfully fetched own user data: {user_obj.username} (ID: {user_obj.id})")
            return user_obj
            
        except Exception as e:
            logger.error(f"Failed to fetch own user data: {e}")
            raise

    def has_valid_token(self, platform_id: str) -> bool:
        """
        检查指定平台用户是否有有效的访问令牌
        
        Args:
            platform_id: 平台用户 ID
            
        Returns:
            bool: 如果有有效令牌返回 True，否则返回 False
        """
        return not self.token_manager.is_token_expired(platform_id)

    def check_scope_permission(self, platform_id: str, required_scope: str) -> bool:
        """
        公开方法：检查指定平台用户是否具有所需的权限范围
        
        Args:
            platform_id: 平台用户 ID
            required_scope: 所需的权限范围（如 'identify', 'public', 'friends.read' 等）
            
        Returns:
            bool: 如果具有所需权限返回 True，否则返回 False
        """
        return self._check_scope_permission(platform_id, required_scope)

    def get_token_info(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """
        获取令牌信息
        
        Args:
            platform_id: 平台用户 ID
            
        Returns:
            Optional[Dict[str, Any]]: 令牌信息，如果没有则返回 None
        """
        token_data = self.token_manager.get_token(platform_id)
        if not token_data:
            return None
        
        return {
            "expires_at": token_data.expires_at,
            "token_type": token_data.token_type,
            "scope": token_data.scope,
            "is_expired": self.token_manager.is_token_expired(platform_id)
        }