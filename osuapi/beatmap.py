"""
OSU API Beatmap 数据模型

包含 Beatmap、BeatmapExtended 和相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class Beatmap:
    """OSU Beatmap 基础信息"""
    
    beatmapset_id: int
    difficulty_rating: float
    id: int
    mode: str
    status: str
    total_length: int
    user_id: int
    version: str
    accuracy: Optional[float] = None
    ar: Optional[float] = None  # Approach Rate
    bpm: Optional[float] = None
    convert: Optional[bool] = None
    count_circles: Optional[int] = None
    count_sliders: Optional[int] = None
    count_spinners: Optional[int] = None
    cs: Optional[float] = None  # Circle Size
    deleted_at: Optional[str] = None
    drain: Optional[float] = None  # HP Drain
    hit_length: Optional[int] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[str] = None
    mode_int: Optional[int] = None
    passcount: Optional[int] = None
    playcount: Optional[int] = None
    ranked: Optional[int] = None
    url: Optional[str] = None
    checksum: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Beatmap":
        """从字典创建 Beatmap 对象"""
        return cls(
            beatmapset_id=data["beatmapset_id"],
            difficulty_rating=data["difficulty_rating"],
            id=data["id"],
            mode=data["mode"],
            status=data["status"],
            total_length=data["total_length"],
            user_id=data["user_id"],
            version=data["version"],
            accuracy=data.get("accuracy"),
            ar=data.get("ar"),
            bpm=data.get("bpm"),
            convert=data.get("convert"),
            count_circles=data.get("count_circles"),
            count_sliders=data.get("count_sliders"),
            count_spinners=data.get("count_spinners"),
            cs=data.get("cs"),
            deleted_at=data.get("deleted_at"),
            drain=data.get("drain"),
            hit_length=data.get("hit_length"),
            is_scoreable=data.get("is_scoreable"),
            last_updated=data.get("last_updated"),
            mode_int=data.get("mode_int"),
            passcount=data.get("passcount"),
            playcount=data.get("playcount"),
            ranked=data.get("ranked"),
            url=data.get("url"),
            checksum=data.get("checksum")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "beatmapset_id": self.beatmapset_id,
            "difficulty_rating": self.difficulty_rating,
            "id": self.id,
            "mode": self.mode,
            "status": self.status,
            "total_length": self.total_length,
            "user_id": self.user_id,
            "version": self.version
        }
        
        # 添加可选字段
        optional_fields = [
            "accuracy", "ar", "bpm", "convert", "count_circles", "count_sliders",
            "count_spinners", "cs", "deleted_at", "drain", "hit_length",
            "is_scoreable", "last_updated", "mode_int", "passcount", "playcount",
            "ranked", "url", "checksum"
        ]
        
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        
        return result


@dataclass
class BeatmapFailtimes:
    """Beatmap 失败时间统计"""
    
    fail: Optional[List[int]] = None
    exit: Optional[List[int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapFailtimes":
        """从字典创建 BeatmapFailtimes 对象"""
        return cls(
            fail=data.get("fail"),
            exit=data.get("exit")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.fail is not None:
            result["fail"] = self.fail
        if self.exit is not None:
            result["exit"] = self.exit
        return result


@dataclass
class BeatmapsetRatings:
    """Beatmapset 评分统计"""
    
    ratings: Optional[List[int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetRatings":
        """从字典创建 BeatmapsetRatings 对象"""
        return cls(
            ratings=data.get("ratings")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.ratings is not None:
            result["ratings"] = self.ratings
        return result


@dataclass
class BeatmapsetCompact:
    """Beatmapset 简化信息"""
    
    artist: str
    artist_unicode: str
    covers: Dict[str, str]
    creator: str
    favourite_count: int
    hype: Optional[Dict[str, Any]]
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
    track_id: Optional[int]
    user_id: int
    video: bool
    availability: Optional[Dict[str, Any]] = None
    bpm: Optional[float] = None
    can_be_hyped: Optional[bool] = None
    deleted_at: Optional[str] = None
    discussion_enabled: Optional[bool] = None
    discussion_locked: Optional[bool] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[str] = None
    legacy_thread_url: Optional[str] = None
    nominations_summary: Optional[Dict[str, Any]] = None
    ranked: Optional[int] = None
    ranked_date: Optional[str] = None
    storyboard: Optional[bool] = None
    submitted_date: Optional[str] = None
    tags: Optional[str] = None
    ratings: Optional[List[int]] = None  # 当包含 ratings 属性时

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapsetCompact":
        """从字典创建 BeatmapsetCompact 对象"""
        return cls(
            artist=data["artist"],
            artist_unicode=data["artist_unicode"],
            covers=data["covers"],
            creator=data["creator"],
            favourite_count=data["favourite_count"],
            hype=data.get("hype"),
            id=data["id"],
            nsfw=data["nsfw"],
            offset=data["offset"],
            play_count=data["play_count"],
            preview_url=data["preview_url"],
            source=data["source"],
            spotlight=data["spotlight"],
            status=data["status"],
            title=data["title"],
            title_unicode=data["title_unicode"],
            track_id=data.get("track_id"),
            user_id=data["user_id"],
            video=data["video"],
            availability=data.get("availability"),
            bpm=data.get("bpm"),
            can_be_hyped=data.get("can_be_hyped"),
            deleted_at=data.get("deleted_at"),
            discussion_enabled=data.get("discussion_enabled"),
            discussion_locked=data.get("discussion_locked"),
            is_scoreable=data.get("is_scoreable"),
            last_updated=data.get("last_updated"),
            legacy_thread_url=data.get("legacy_thread_url"),
            nominations_summary=data.get("nominations_summary"),
            ranked=data.get("ranked"),
            ranked_date=data.get("ranked_date"),
            storyboard=data.get("storyboard"),
            submitted_date=data.get("submitted_date"),
            tags=data.get("tags"),
            ratings=data.get("ratings")
        )


@dataclass
class BeatmapExtended(Beatmap):
    """OSU Beatmap 扩展信息，包含额外属性"""
    
    beatmapset: Optional[BeatmapsetCompact] = None
    failtimes: Optional[BeatmapFailtimes] = None
    max_combo: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatmapExtended":
        """从字典创建 BeatmapExtended 对象"""
        # 先创建基础 Beatmap 字段
        beatmap_data = {k: v for k, v in data.items() 
                       if k not in ["beatmapset", "failtimes", "max_combo"]}
        
        # 创建基础对象
        base_beatmap = Beatmap.from_dict(beatmap_data)
        
        # 处理扩展字段
        beatmapset = None
        if "beatmapset" in data and data["beatmapset"]:
            beatmapset = BeatmapsetCompact.from_dict(data["beatmapset"])
        
        failtimes = None
        if "failtimes" in data and data["failtimes"]:
            failtimes = BeatmapFailtimes.from_dict(data["failtimes"])
        
        max_combo = data.get("max_combo")
        
        # 创建扩展对象
        return cls(
            # 基础字段
            beatmapset_id=base_beatmap.beatmapset_id,
            difficulty_rating=base_beatmap.difficulty_rating,
            id=base_beatmap.id,
            mode=base_beatmap.mode,
            status=base_beatmap.status,
            total_length=base_beatmap.total_length,
            user_id=base_beatmap.user_id,
            version=base_beatmap.version,
            accuracy=base_beatmap.accuracy,
            ar=base_beatmap.ar,
            bpm=base_beatmap.bpm,
            convert=base_beatmap.convert,
            count_circles=base_beatmap.count_circles,
            count_sliders=base_beatmap.count_sliders,
            count_spinners=base_beatmap.count_spinners,
            cs=base_beatmap.cs,
            deleted_at=base_beatmap.deleted_at,
            drain=base_beatmap.drain,
            hit_length=base_beatmap.hit_length,
            is_scoreable=base_beatmap.is_scoreable,
            last_updated=base_beatmap.last_updated,
            mode_int=base_beatmap.mode_int,
            passcount=base_beatmap.passcount,
            playcount=base_beatmap.playcount,
            ranked=base_beatmap.ranked,
            url=base_beatmap.url,
            checksum=base_beatmap.checksum,
            # 扩展字段
            beatmapset=beatmapset,
            failtimes=failtimes,
            max_combo=max_combo
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        
        if self.beatmapset is not None:
            result["beatmapset"] = self.beatmapset.to_dict()
        if self.failtimes is not None:
            result["failtimes"] = self.failtimes.to_dict()
        if self.max_combo is not None:
            result["max_combo"] = self.max_combo
        
        return result


def format_beatmap_difficulty(difficulty_rating: float) -> str:
    """
    格式化难度等级为可读文本
    
    Args:
        difficulty_rating: 难度评级
        
    Returns:
        str: 格式化后的难度文本
    """
    if difficulty_rating < 2.0:
        return f"Easy ({difficulty_rating:.2f}⭐)"
    elif difficulty_rating < 2.7:
        return f"Normal ({difficulty_rating:.2f}⭐)"
    elif difficulty_rating < 4.0:
        return f"Hard ({difficulty_rating:.2f}⭐)"
    elif difficulty_rating < 5.3:
        return f"Insane ({difficulty_rating:.2f}⭐)"
    elif difficulty_rating < 6.5:
        return f"Expert ({difficulty_rating:.2f}⭐)"
    else:
        return f"Expert+ ({difficulty_rating:.2f}⭐)"


def format_beatmap_length(total_length: int) -> str:
    """
    格式化谱面长度为可读格式
    
    Args:
        total_length: 总长度（秒）
        
    Returns:
        str: 格式化后的时间字符串
    """
    minutes = total_length // 60
    seconds = total_length % 60
    return f"{minutes}:{seconds:02d}"


def format_beatmap_bpm(bpm: Optional[float]) -> str:
    """
    格式化 BPM 为可读格式
    
    Args:
        bpm: BPM 值
        
    Returns:
        str: 格式化后的 BPM 字符串
    """
    if bpm is None:
        return "N/A"
    return f"{bpm:.0f} BPM"
