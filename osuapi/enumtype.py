from enum import Enum

class Scopes(Enum):
    """
    osu! API 授权范围
    """
    PUBLIC = "public"
    IDENTIFY = "identify"
    FRIENDS = "friends.read"
    FORUM = "forum.write"
    DELEGATE = "delegate"
    CHAT_WRITE = "chat.write"
    CHAT_READ = "chat.read"
    CHAT_WRITE_MANAGE = "chat.write_manage"

class OsuModes(Enum):
    """
    osu! 游戏模式
    """
    OSU = "osu"
    TAIKO = "taiko"
    FRUITS = "fruits"
    MANIA = "mania"