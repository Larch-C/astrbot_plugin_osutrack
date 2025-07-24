import json
import os
from typing import Dict, List, Optional, Union

class LinkAccountManager:
    def __init__(self):
        """
        初始化关联账户管理器
        在二级父目录下维护 osuaccount.json 文件
        """
        # 获取当前文件所在目录的二级父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_parent_dir = os.path.dirname(os.path.dirname(current_dir))
        self.json_file_path = os.path.join(parent_parent_dir, "osuaccount.json")
        
        # 确保 JSON 文件存在
        self._ensure_json_file()
    
    def _ensure_json_file(self):
        """确保 JSON 文件存在，如果不存在则创建"""
        if not os.path.exists(self.json_file_path):
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
            # 创建初始 JSON 文件
            initial_data = {
                "osu_to_platforms": {},  # osu_id -> [platform_ids]
                "platform_to_osu": {}   # platform_id -> osu_id
            }
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def _load_data(self) -> Dict:
        """加载 JSON 数据"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保数据结构正确
                if "osu_to_platforms" not in data:
                    data["osu_to_platforms"] = {}
                if "platform_to_osu" not in data:
                    data["platform_to_osu"] = {}
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件损坏或不存在，重新创建
            self._ensure_json_file()
            return self._load_data()
    
    def _save_data(self, data: Dict):
        """保存数据到 JSON 文件"""
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def link_account(self, osu_id: Union[str, int], platform_id: Union[str, int]) -> bool:
        """
        关联 OSU 账号和平台 ID
        
        Args:
            osu_id: OSU 账号 ID
            platform_id: 平台 ID（如 QQ 号）
            
        Returns:
            bool: 成功返回 True，失败返回 False
        """
        osu_id = str(osu_id)
        platform_id = str(platform_id)
        
        data = self._load_data()
        
        # 检查平台 ID 是否已经关联了其他 OSU 账号
        if platform_id in data["platform_to_osu"]:
            existing_osu_id = data["platform_to_osu"][platform_id]
            if existing_osu_id != osu_id:
                return False  # 一个平台 ID 只能对应一个 OSU 账号
        
        # 添加关联
        if osu_id not in data["osu_to_platforms"]:
            data["osu_to_platforms"][osu_id] = []
        
        if platform_id not in data["osu_to_platforms"][osu_id]:
            data["osu_to_platforms"][osu_id].append(platform_id)
        
        data["platform_to_osu"][platform_id] = osu_id
        
        self._save_data(data)
        return True
    
    def unlink_account(self, platform_id: Union[str, int]) -> bool:
        """
        解除平台 ID 的关联
        
        Args:
            platform_id: 平台 ID
            
        Returns:
            bool: 成功返回 True，失败返回 False
        """
        platform_id = str(platform_id)
        
        data = self._load_data()
        
        if platform_id not in data["platform_to_osu"]:
            return False  # 平台 ID 未关联任何 OSU 账号
        
        osu_id = data["platform_to_osu"][platform_id]
        
        # 从 OSU 账号的平台列表中移除该平台 ID
        if osu_id in data["osu_to_platforms"]:
            if platform_id in data["osu_to_platforms"][osu_id]:
                data["osu_to_platforms"][osu_id].remove(platform_id)
            
            # 如果 OSU 账号没有关联任何平台 ID，则删除该记录
            if not data["osu_to_platforms"][osu_id]:
                del data["osu_to_platforms"][osu_id]
        
        # 删除平台到 OSU 的映射
        del data["platform_to_osu"][platform_id]
        
        self._save_data(data)
        return True
    
    def get_osu_id_by_platform(self, platform_id: Union[str, int]) -> Optional[str]:
        """
        根据平台 ID 获取关联的 OSU 账号 ID
        
        Args:
            platform_id: 平台 ID
            
        Returns:
            Optional[str]: OSU 账号 ID，如果未关联则返回 None
        """
        platform_id = str(platform_id)
        data = self._load_data()
        return data["platform_to_osu"].get(platform_id)
    
    def get_platform_ids_by_osu(self, osu_id: Union[str, int]) -> List[str]:
        """
        根据 OSU 账号 ID 获取关联的平台 ID 列表
        
        Args:
            osu_id: OSU 账号 ID
            
        Returns:
            List[str]: 平台 ID 列表
        """
        osu_id = str(osu_id)
        data = self._load_data()
        return data["osu_to_platforms"].get(osu_id, [])
    
    def is_platform_linked(self, platform_id: Union[str, int]) -> bool:
        """
        检查平台 ID 是否已关联 OSU 账号
        
        Args:
            platform_id: 平台 ID
            
        Returns:
            bool: 已关联返回 True，未关联返回 False
        """
        return self.get_osu_id_by_platform(platform_id) is not None
    
    def is_osu_linked(self, osu_id: Union[str, int]) -> bool:
        """
        检查 OSU 账号是否已关联平台 ID
        
        Args:
            osu_id: OSU 账号 ID
            
        Returns:
            bool: 已关联返回 True，未关联返回 False
        """
        return len(self.get_platform_ids_by_osu(osu_id)) > 0
    
    def get_all_links(self) -> Dict:
        """
        获取所有关联信息
        
        Returns:
            Dict: 包含所有关联信息的字典
        """
        return self._load_data()
    
    def clear_all_links(self):
        """清除所有关联信息"""
        initial_data = {
            "osu_to_platforms": {},
            "platform_to_osu": {}
        }
        self._save_data(initial_data)