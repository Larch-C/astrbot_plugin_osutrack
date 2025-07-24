"""
OSU API 模式转换工具

提供 OSU API 与 OSU Track API 之间的模式转换功能
"""

from .enumtype import OsuModes
from ..osutrackapi.enums import GameMode


def convert_osu_mode_to_track_mode(osu_mode: str) -> GameMode:
    """
    将 OSU API 模式转换为 OSU Track API 模式
    
    Args:
        osu_mode: OSU API 模式字符串 ("osu", "taiko", "fruits", "mania")
        
    Returns:
        GameMode: OSU Track 游戏模式枚举
        
    Raises:
        ValueError: 如果模式不支持
    """
    mode_mapping = {
        "osu": GameMode.OSU,
        "taiko": GameMode.TAIKO, 
        "fruits": GameMode.CTB,
        "mania": GameMode.MANIA
    }
    
    if osu_mode not in mode_mapping:
        raise ValueError(f"不支持的游戏模式: {osu_mode}")
    
    return mode_mapping[osu_mode]


def validate_osu_mode(mode: str) -> str:
    """
    验证并标准化 OSU 模式字符串
    
    Args:
        mode: 用户输入的模式字符串
        
    Returns:
        str: 标准化的模式字符串
        
    Raises:
        ValueError: 如果模式不支持
    """
    if not mode:
        return "osu"  # 默认模式
    
    mode = mode.lower()
    valid_modes = ["osu", "taiko", "fruits", "mania"]
    
    if mode not in valid_modes:
        raise ValueError(f"不支持的游戏模式: {mode}，支持的模式: {', '.join(valid_modes)}")
    
    return mode


def get_supported_modes() -> list[str]:
    """
    获取支持的所有游戏模式列表
    
    Returns:
        list[str]: 支持的游戏模式列表
    """
    return ["osu", "taiko", "fruits", "mania"]


def osu_mode_to_enum(mode: str) -> OsuModes:
    """
    将模式字符串转换为 OSU API 枚举
    
    Args:
        mode: 模式字符串
        
    Returns:
        OsuModes: OSU 模式枚举
        
    Raises:
        ValueError: 如果模式不支持
    """
    validated_mode = validate_osu_mode(mode)
    
    mode_mapping = {
        "osu": OsuModes.OSU,
        "taiko": OsuModes.TAIKO,
        "fruits": OsuModes.FRUITS,
        "mania": OsuModes.MANIA
    }
    
    return mode_mapping[validated_mode]


def track_mode_to_osu_mode(track_mode: GameMode) -> str:
    """
    将 OSU Track 模式转换为 OSU API 模式字符串
    
    Args:
        track_mode: OSU Track 游戏模式枚举
        
    Returns:
        str: OSU API 模式字符串
        
    Raises:
        ValueError: 如果模式不支持
    """
    mode_mapping = {
        GameMode.OSU: "osu",
        GameMode.TAIKO: "taiko",
        GameMode.CTB: "fruits",
        GameMode.MANIA: "mania"
    }
    
    if track_mode not in mode_mapping:
        raise ValueError(f"不支持的 OSU Track 游戏模式: {track_mode}")
    
    return mode_mapping[track_mode]
