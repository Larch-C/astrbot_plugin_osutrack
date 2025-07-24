from typing import Optional, List, Any, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HiScore:
    """高分记录"""
    beatmap_id: str
    score_id: str
    score: str
    maxcombo: str
    count50: str
    count100: str
    count300: str
    countmiss: str
    countkatu: str
    countgeki: str
    perfect: str
    enabled_mods: str
    user_id: str
    date: str
    rank: str
    pp: str
    replay_available: str
    ranking: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HiScore':
        """从字典创建 HiScore 对象"""
        return cls(
            beatmap_id=str(data.get('beatmap_id', '')),
            score_id=str(data.get('score_id', '')),
            score=str(data.get('score', '')),
            maxcombo=str(data.get('maxcombo', '')),
            count50=str(data.get('count50', '')),
            count100=str(data.get('count100', '')),
            count300=str(data.get('count300', '')),
            countmiss=str(data.get('countmiss', '')),
            countkatu=str(data.get('countkatu', '')),
            countgeki=str(data.get('countgeki', '')),
            perfect=str(data.get('perfect', '')),
            enabled_mods=str(data.get('enabled_mods', '')),
            user_id=str(data.get('user_id', '')),
            date=str(data.get('date', '')),
            rank=str(data.get('rank', '')),
            pp=str(data.get('pp', '')),
            replay_available=str(data.get('replay_available', '')),
            ranking=int(data.get('ranking', 0))
        )

@dataclass
class UpdateResponse:
    """用户更新响应"""
    username: str
    mode: int
    playcount: int
    pp_rank: int
    pp_raw: float
    accuracy: float
    total_score: int
    ranked_score: int
    count300: int
    count50: int
    count100: int
    level: float
    count_rank_a: int
    count_rank_s: int
    count_rank_ss: int
    levelup: bool
    first: bool
    exists: bool
    newhs: List[HiScore]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateResponse':
        """从字典创建 UpdateResponse 对象"""
        newhs = []
        if 'newhs' in data and isinstance(data['newhs'], list):
            for hs_data in data['newhs']:
                newhs.append(HiScore.from_dict(hs_data))

        return cls(
            username=str(data.get('username', '')),
            mode=int(data.get('mode', 0)),
            playcount=int(data.get('playcount', 0)),
            pp_rank=int(data.get('pp_rank', 0)),
            pp_raw=float(data.get('pp_raw', 0.0)),
            accuracy=float(data.get('accuracy', 0.0)),
            total_score=int(data.get('total_score', 0)),
            ranked_score=int(data.get('ranked_score', 0)),
            count300=int(data.get('count300', 0)),
            count50=int(data.get('count50', 0)),
            count100=int(data.get('count100', 0)),
            level=float(data.get('level', 0.0)),
            count_rank_a=int(data.get('count_rank_a', 0)),
            count_rank_s=int(data.get('count_rank_s', 0)),
            count_rank_ss=int(data.get('count_rank_ss', 0)),
            levelup=bool(data.get('levelup', False)),
            first=bool(data.get('first', False)),
            exists=bool(data.get('exists', True)),
            newhs=newhs
        )

@dataclass
class StatsUpdate:
    """统计更新记录"""
    count300: int
    count100: int
    count50: int
    playcount: int
    ranked_score: str
    total_score: str
    pp_rank: int
    level: float
    pp_raw: float
    accuracy: float
    count_rank_ss: int
    count_rank_s: int
    count_rank_a: int
    timestamp: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatsUpdate':
        """从字典创建 StatsUpdate 对象"""
        return cls(
            count300=int(data.get('count300', 0)),
            count100=int(data.get('count100', 0)),
            count50=int(data.get('count50', 0)),
            playcount=int(data.get('playcount', 0)),
            ranked_score=str(data.get('ranked_score', '0')),
            total_score=str(data.get('total_score', '0')),
            pp_rank=int(data.get('pp_rank', 0)),
            level=float(data.get('level', 0.0)),
            pp_raw=float(data.get('pp_raw', 0.0)),
            accuracy=float(data.get('accuracy', 0.0)),
            count_rank_ss=int(data.get('count_rank_ss', 0)),
            count_rank_s=int(data.get('count_rank_s', 0)),
            count_rank_a=int(data.get('count_rank_a', 0)),
            timestamp=str(data.get('timestamp', ''))
        )

@dataclass
class RecordedScore:
    """记录的分数"""
    beatmap_id: int
    score: int
    pp: float
    mods: int
    rank: str
    score_time: str
    update_time: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecordedScore':
        """从字典创建 RecordedScore 对象"""
        return cls(
            beatmap_id=int(data.get('beatmap_id', 0)),
            score=int(data.get('score', 0)),
            pp=float(data.get('pp', 0.0)),
            mods=int(data.get('mods', 0)),
            rank=str(data.get('rank', '')),
            score_time=str(data.get('score_time', '')),
            update_time=str(data.get('update_time', ''))
        )

@dataclass
class PeakData:
    """峰值数据"""
    best_global_rank: Optional[int]
    best_rank_timestamp: Optional[str]
    best_accuracy: Optional[float]
    best_acc_timestamp: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeakData':
        """从字典创建 PeakData 对象"""
        return cls(
            best_global_rank=data.get('best_global_rank'),
            best_rank_timestamp=data.get('best_rank_timestamp'),
            best_accuracy=data.get('best_accuracy'),
            best_acc_timestamp=data.get('best_acc_timestamp')
        )

@dataclass
class BestPlay:
    """最佳游戏"""
    user: int
    beatmap_id: int
    score: int
    pp: float
    mods: int
    rank: str
    score_time: str
    update_time: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BestPlay':
        """从字典创建 BestPlay 对象"""
        return cls(
            user=int(data.get('user', 0)),
            beatmap_id=int(data.get('beatmap_id', 0)),
            score=int(data.get('score', 0)),
            pp=float(data.get('pp', 0.0)),
            mods=int(data.get('mods', 0)),
            rank=str(data.get('rank', '')),
            score_time=str(data.get('score_time', '')),
            update_time=str(data.get('update_time', ''))
        )
