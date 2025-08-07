"""
OSU API Beatmapset 搜索相关的枚举和数据模型
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from .beatmapset import BeatmapsetExtended


class BeatmapsetSearchMode(Enum):
    """谱面搜索模式"""
    ANY = -1
    OSU = 0
    TAIKO = 1
    FRUITS = 2
    MANIA = 3


class BeatmapsetSearchCategory(Enum):
    """谱面搜索类别"""
    ANY = "any"
    LEADERBOARD = "leaderboard"
    RANKED = "ranked"
    QUALIFIED = "qualified"
    LOVED = "loved"
    FAVOURITES = "favourites"
    PENDING = "pending"
    WIP = "wip"
    GRAVEYARD = "graveyard"
    MY_MAPS = "mine"


class BeatmapsetSearchExplicitContent(Enum):
    """显式内容过滤"""
    HIDE = "false"
    SHOW = "true"


class BeatmapsetSearchGenre(Enum):
    """音乐类型"""
    ANY = 0
    UNSPECIFIED = 1
    VIDEO_GAME = 2
    ANIME = 3
    ROCK = 4
    POP = 5
    OTHER = 6
    NOVELTY = 7
    HIP_HOP = 8
    ELECTRONIC = 9
    METAL = 10
    CLASSICAL = 11
    FOLK = 12
    JAZZ = 13


class BeatmapsetSearchLanguage(Enum):
    """语言"""
    ANY = 0
    UNSPECIFIED = 1
    ENGLISH = 2
    JAPANESE = 3
    CHINESE = 4
    INSTRUMENTAL = 5
    KOREAN = 6
    FRENCH = 7
    GERMAN = 8
    SWEDISH = 9
    SPANISH = 10
    ITALIAN = 11
    RUSSIAN = 12
    POLISH = 13
    OTHER = 14


class BeatmapsetSearchSort(Enum):
    """排序方式"""
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    ARTIST_ASC = "artist_asc"
    ARTIST_DESC = "artist_desc"
    DIFFICULTY_ASC = "difficulty_asc"
    DIFFICULTY_DESC = "difficulty_desc"
    RANKED_ASC = "ranked_asc"
    RANKED_DESC = "ranked_desc"
    RATING_ASC = "rating_asc"
    RATING_DESC = "rating_desc"
    PLAYS_ASC = "plays_asc"
    PLAYS_DESC = "plays_desc"
    FAVOURITES_ASC = "favourites_asc"
    FAVOURITES_DESC = "favourites_desc"


@dataclass
class BeatmapsetSearchCursor:
    """搜索分页游标"""
    
    cursor_string: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetSearchCursor":
        """从字典创建 BeatmapsetSearchCursor 对象"""
        return cls(
            cursor_string=data.get("cursor_string")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.cursor_string is not None:
            result["cursor_string"] = self.cursor_string
        return result


@dataclass
class BeatmapsetSearchResult:
    """谱面搜索结果"""
    
    beatmapsets: List[BeatmapsetExtended]
    cursor: Optional[BeatmapsetSearchCursor] = None
    search: Optional[Dict[str, Any]] = None
    recommended_difficulty: Optional[float] = None
    error: Optional[str] = None
    total: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetSearchResult":
        """从字典创建 BeatmapsetSearchResult 对象"""
        # 处理 beatmapsets 列表
        beatmapsets = []
        if "beatmapsets" in data and isinstance(data["beatmapsets"], list):
            for beatmapset_data in data["beatmapsets"]:
                beatmapset = BeatmapsetExtended.from_dict(beatmapset_data)
                beatmapsets.append(beatmapset)
        
        # 处理 cursor
        cursor = None
        if "cursor" in data and data["cursor"]:
            cursor = BeatmapsetSearchCursor.from_dict(data["cursor"])
        
        return cls(
            beatmapsets=beatmapsets,
            cursor=cursor,
            search=data.get("search"),
            recommended_difficulty=data.get("recommended_difficulty"),
            error=data.get("error"),
            total=data.get("total")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "beatmapsets": [beatmapset.to_dict() for beatmapset in self.beatmapsets]
        }
        
        if self.cursor is not None:
            result["cursor"] = self.cursor.to_dict()
        if self.search is not None:
            result["search"] = self.search
        if self.recommended_difficulty is not None:
            result["recommended_difficulty"] = self.recommended_difficulty
        if self.error is not None:
            result["error"] = self.error
        if self.total is not None:
            result["total"] = self.total
        
        return result
