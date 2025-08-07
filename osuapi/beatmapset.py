"""
OSU API Beatmapset 数据模型

包含 Beatmapset、BeatmapsetExtended 和相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class BeatmapsetCovers:
    """Beatmapset 封面图片"""
    
    cover: Optional[str] = None
    cover_2x: Optional[str] = None
    card: Optional[str] = None
    card_2x: Optional[str] = None
    list: Optional[str] = None
    list_2x: Optional[str] = None
    slimcover: Optional[str] = None
    slimcover_2x: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetCovers":
        """从字典创建 BeatmapsetCovers 对象"""
        return cls(
            cover=data.get("cover"),
            cover_2x=data.get("cover@2x"),
            card=data.get("card"),
            card_2x=data.get("card@2x"),
            list=data.get("list"),
            list_2x=data.get("list@2x"),
            slimcover=data.get("slimcover"),
            slimcover_2x=data.get("slimcover@2x")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.cover is not None:
            result["cover"] = self.cover
        if self.cover_2x is not None:
            result["cover@2x"] = self.cover_2x
        if self.card is not None:
            result["card"] = self.card
        if self.card_2x is not None:
            result["card@2x"] = self.card_2x
        if self.list is not None:
            result["list"] = self.list
        if self.list_2x is not None:
            result["list@2x"] = self.list_2x
        if self.slimcover is not None:
            result["slimcover"] = self.slimcover
        if self.slimcover_2x is not None:
            result["slimcover@2x"] = self.slimcover_2x
        return result


@dataclass
class BeatmapsetAvailability:
    """Beatmapset 可用性信息"""
    
    download_disabled: bool = False
    more_information: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetAvailability":
        """从字典创建 BeatmapsetAvailability 对象"""
        return cls(
            download_disabled=data.get("download_disabled", False),
            more_information=data.get("more_information")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"download_disabled": self.download_disabled}
        if self.more_information is not None:
            result["more_information"] = self.more_information
        return result


@dataclass
class BeatmapsetHype:
    """Beatmapset 热度信息"""
    
    current: int = 0
    required: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetHype":
        """从字典创建 BeatmapsetHype 对象"""
        return cls(
            current=data.get("current", 0),
            required=data.get("required", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current": self.current,
            "required": self.required
        }


@dataclass
class BeatmapsetNominationsSummary:
    """Beatmapset 提名总结"""
    
    current: int = 0
    required: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetNominationsSummary":
        """从字典创建 BeatmapsetNominationsSummary 对象"""
        return cls(
            current=data.get("current", 0),
            required=data.get("required", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current": self.current,
            "required": self.required
        }


@dataclass
class Beatmapset:
    """OSU Beatmapset 基础信息"""
    
    artist: str
    artist_unicode: str
    covers: BeatmapsetCovers
    creator: str
    favourite_count: int
    id: int
    nsfw: bool
    offset: int
    play_count: int
    preview_url: str
    source: str
    spotlight: bool
    status: str
    title: str
    title_unicode: str
    user_id: int
    video: bool
    availability: Optional[BeatmapsetAvailability] = None
    bpm: Optional[float] = None
    can_be_hyped: Optional[bool] = None
    deleted_at: Optional[str] = None
    discussion_enabled: Optional[bool] = None
    discussion_locked: Optional[bool] = None
    hype: Optional[BeatmapsetHype] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[str] = None
    legacy_thread_url: Optional[str] = None
    nominations_summary: Optional[BeatmapsetNominationsSummary] = None
    ranked: Optional[int] = None
    ranked_date: Optional[str] = None
    storyboard: Optional[bool] = None
    submitted_date: Optional[str] = None
    tags: Optional[str] = None
    track_id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Beatmapset":
        """从字典创建 Beatmapset 对象"""
        # 处理 covers - 如果缺失则创建空的 covers 对象
        covers_data = data.get("covers", {})
        covers = BeatmapsetCovers.from_dict(covers_data)
        
        # 处理可选的嵌套对象
        availability = None
        if "availability" in data and data["availability"]:
            availability = BeatmapsetAvailability.from_dict(data["availability"])
        
        hype = None
        if "hype" in data and data["hype"]:
            hype = BeatmapsetHype.from_dict(data["hype"])
        
        nominations_summary = None
        if "nominations_summary" in data and data["nominations_summary"]:
            nominations_summary = BeatmapsetNominationsSummary.from_dict(data["nominations_summary"])
        
        return cls(
            artist=data.get("artist", ""),
            artist_unicode=data.get("artist_unicode", ""),
            covers=covers,
            creator=data.get("creator", ""),
            favourite_count=data.get("favourite_count", 0),
            id=data.get("id", 0),
            nsfw=data.get("nsfw", False),
            offset=data.get("offset", 0),
            play_count=data.get("play_count", 0),
            preview_url=data.get("preview_url", ""),
            source=data.get("source", ""),
            spotlight=data.get("spotlight", False),
            status=data.get("status", ""),
            title=data.get("title", ""),
            title_unicode=data.get("title_unicode", ""),
            user_id=data.get("user_id", 0),
            video=data.get("video", False),
            availability=availability,
            bpm=data.get("bpm"),
            can_be_hyped=data.get("can_be_hyped"),
            deleted_at=data.get("deleted_at"),
            discussion_enabled=data.get("discussion_enabled"),
            discussion_locked=data.get("discussion_locked"),
            hype=hype,
            is_scoreable=data.get("is_scoreable"),
            last_updated=data.get("last_updated"),
            legacy_thread_url=data.get("legacy_thread_url"),
            nominations_summary=nominations_summary,
            ranked=data.get("ranked"),
            ranked_date=data.get("ranked_date"),
            storyboard=data.get("storyboard"),
            submitted_date=data.get("submitted_date"),
            tags=data.get("tags"),
            track_id=data.get("track_id")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "artist": self.artist,
            "artist_unicode": self.artist_unicode,
            "covers": self.covers.to_dict(),
            "creator": self.creator,
            "favourite_count": self.favourite_count,
            "id": self.id,
            "nsfw": self.nsfw,
            "offset": self.offset,
            "play_count": self.play_count,
            "preview_url": self.preview_url,
            "source": self.source,
            "spotlight": self.spotlight,
            "status": self.status,
            "title": self.title,
            "title_unicode": self.title_unicode,
            "user_id": self.user_id,
            "video": self.video
        }
        
        # 添加可选字段
        if self.availability is not None:
            result["availability"] = self.availability.to_dict()
        if self.bpm is not None:
            result["bpm"] = self.bpm
        if self.can_be_hyped is not None:
            result["can_be_hyped"] = self.can_be_hyped
        if self.deleted_at is not None:
            result["deleted_at"] = self.deleted_at
        if self.discussion_enabled is not None:
            result["discussion_enabled"] = self.discussion_enabled
        if self.discussion_locked is not None:
            result["discussion_locked"] = self.discussion_locked
        if self.hype is not None:
            result["hype"] = self.hype.to_dict()
        if self.is_scoreable is not None:
            result["is_scoreable"] = self.is_scoreable
        if self.last_updated is not None:
            result["last_updated"] = self.last_updated
        if self.legacy_thread_url is not None:
            result["legacy_thread_url"] = self.legacy_thread_url
        if self.nominations_summary is not None:
            result["nominations_summary"] = self.nominations_summary.to_dict()
        if self.ranked is not None:
            result["ranked"] = self.ranked
        if self.ranked_date is not None:
            result["ranked_date"] = self.ranked_date
        if self.storyboard is not None:
            result["storyboard"] = self.storyboard
        if self.submitted_date is not None:
            result["submitted_date"] = self.submitted_date
        if self.tags is not None:
            result["tags"] = self.tags
        if self.track_id is not None:
            result["track_id"] = self.track_id
        
        return result


@dataclass
class BeatmapsetExtended(Beatmapset):
    """OSU Beatmapset 扩展信息，包含额外属性"""
    
    beatmaps: Optional[List[Dict[str, Any]]] = None  # 简化的 Beatmap 对象列表
    converts: Optional[List[Dict[str, Any]]] = None
    current_nominations: Optional[List[Dict[str, Any]]] = None
    description: Optional[Dict[str, str]] = None
    genre: Optional[Dict[str, Any]] = None
    language: Optional[Dict[str, Any]] = None
    pack_tags: Optional[List[str]] = None
    ratings: Optional[List[int]] = None
    recent_favourites: Optional[List[Dict[str, Any]]] = None
    user: Optional[Dict[str, Any]] = None  # 简化的 User 对象

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetExtended":
        """从字典创建 BeatmapsetExtended 对象"""
        # 先创建基础 Beatmapset 字段
        base_data = {k: v for k, v in data.items() 
                    if k not in ["beatmaps", "converts", "current_nominations", "description", 
                                "genre", "language", "pack_tags", "ratings", "recent_favourites", "user"]}
        
        # 创建基础对象
        base_beatmapset = Beatmapset.from_dict(base_data)
        
        # 创建扩展对象
        return cls(
            # 基础字段
            artist=base_beatmapset.artist,
            artist_unicode=base_beatmapset.artist_unicode,
            covers=base_beatmapset.covers,
            creator=base_beatmapset.creator,
            favourite_count=base_beatmapset.favourite_count,
            id=base_beatmapset.id,
            nsfw=base_beatmapset.nsfw,
            offset=base_beatmapset.offset,
            play_count=base_beatmapset.play_count,
            preview_url=base_beatmapset.preview_url,
            source=base_beatmapset.source,
            spotlight=base_beatmapset.spotlight,
            status=base_beatmapset.status,
            title=base_beatmapset.title,
            title_unicode=base_beatmapset.title_unicode,
            user_id=base_beatmapset.user_id,
            video=base_beatmapset.video,
            availability=base_beatmapset.availability,
            bpm=base_beatmapset.bpm,
            can_be_hyped=base_beatmapset.can_be_hyped,
            deleted_at=base_beatmapset.deleted_at,
            discussion_enabled=base_beatmapset.discussion_enabled,
            discussion_locked=base_beatmapset.discussion_locked,
            hype=base_beatmapset.hype,
            is_scoreable=base_beatmapset.is_scoreable,
            last_updated=base_beatmapset.last_updated,
            legacy_thread_url=base_beatmapset.legacy_thread_url,
            nominations_summary=base_beatmapset.nominations_summary,
            ranked=base_beatmapset.ranked,
            ranked_date=base_beatmapset.ranked_date,
            storyboard=base_beatmapset.storyboard,
            submitted_date=base_beatmapset.submitted_date,
            tags=base_beatmapset.tags,
            track_id=base_beatmapset.track_id,
            # 扩展字段
            beatmaps=data.get("beatmaps"),
            converts=data.get("converts"),
            current_nominations=data.get("current_nominations"),
            description=data.get("description"),
            genre=data.get("genre"),
            language=data.get("language"),
            pack_tags=data.get("pack_tags"),
            ratings=data.get("ratings"),
            recent_favourites=data.get("recent_favourites"),
            user=data.get("user")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        
        # 添加扩展字段
        if self.beatmaps is not None:
            result["beatmaps"] = self.beatmaps
        if self.converts is not None:
            result["converts"] = self.converts
        if self.current_nominations is not None:
            result["current_nominations"] = self.current_nominations
        if self.description is not None:
            result["description"] = self.description
        if self.genre is not None:
            result["genre"] = self.genre
        if self.language is not None:
            result["language"] = self.language
        if self.pack_tags is not None:
            result["pack_tags"] = self.pack_tags
        if self.ratings is not None:
            result["ratings"] = self.ratings
        if self.recent_favourites is not None:
            result["recent_favourites"] = self.recent_favourites
        if self.user is not None:
            result["user"] = self.user
        
        return result


def format_beatmapset_status(status: str) -> str:
    """
    格式化谱面集状态为可读文本
    
    Args:
        status: 状态字符串
        
    Returns:
        str: 格式化后的状态文本
    """
    status_mapping = {
        "graveyard": "坟场",
        "wip": "制作中",
        "pending": "待定",
        "ranked": "排名",
        "approved": "批准",
        "qualified": "合格",
        "loved": "喜爱"
    }
    
    return status_mapping.get(status.lower(), status)
