from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserStatistics:
    """用户统计信息"""
    count_100: Optional[int] = None
    count_300: Optional[int] = None
    count_50: Optional[int] = None
    count_miss: Optional[int] = None
    level: Optional[Dict[str, Any]] = None
    global_rank: Optional[int] = None
    global_rank_exp: Optional[int] = None
    pp: Optional[float] = None
    pp_exp: Optional[float] = None
    ranked_score: Optional[int] = None
    hit_accuracy: Optional[float] = None
    play_count: Optional[int] = None
    play_time: Optional[int] = None
    total_score: Optional[int] = None
    total_hits: Optional[int] = None
    maximum_combo: Optional[int] = None
    replays_watched_by_others: Optional[int] = None
    is_ranked: Optional[bool] = None
    grade_counts: Optional[Dict[str, int]] = None
    country_rank: Optional[int] = None
    rank: Optional[Dict[str, Any]] = None
    variants: Optional[List[Dict[str, Any]]] = None

@dataclass
class UserBadge:
    """用户徽章"""
    awarded_at: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_2x_url: Optional[str] = None
    url: Optional[str] = None

@dataclass
class UserGroup:
    """用户组"""
    colour: Optional[str] = None
    has_listing: Optional[bool] = None
    has_playmodes: Optional[bool] = None
    id: Optional[int] = None
    identifier: Optional[str] = None
    is_probationary: Optional[bool] = None
    name: Optional[str] = None
    short_name: Optional[str] = None
    playmodes: Optional[List[str]] = None

@dataclass
class User:
    """OSU 用户基础信息"""
    avatar_url: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[Dict[str, Any]] = None  # 包含国家名称等信息
    default_group: Optional[str] = None
    id: Optional[int] = None
    is_active: Optional[bool] = None
    is_bot: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_online: Optional[bool] = None
    is_supporter: Optional[bool] = None
    last_visit: Optional[str] = None
    pm_friends_only: Optional[bool] = None
    profile_colour: Optional[str] = None
    username: Optional[str] = None

@dataclass
class UserExtended(User):
    """扩展的用户信息，包含更多详细数据"""
    # 基础用户信息继承自 User
    
    # 扩展信息
    cover_url: Optional[str] = None
    discord: Optional[str] = None
    has_supported: Optional[bool] = None
    interests: Optional[str] = None
    join_date: Optional[str] = None
    kudosu: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    max_blocks: Optional[int] = None
    max_friends: Optional[int] = None
    occupation: Optional[str] = None
    playmode: Optional[str] = None
    playstyle: Optional[List[str]] = None
    post_count: Optional[int] = None
    profile_order: Optional[List[str]] = None
    title: Optional[str] = None
    title_url: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    
    # 可选的扩展属性
    account_history: Optional[List[Dict[str, Any]]] = None
    active_tournament_banner: Optional[Dict[str, Any]] = None
    badges: Optional[List[UserBadge]] = None
    beatmap_playcounts_count: Optional[int] = None
    favourite_beatmapset_count: Optional[int] = None
    follower_count: Optional[int] = None
    graveyard_beatmapset_count: Optional[int] = None
    groups: Optional[List[UserGroup]] = None
    loved_beatmapset_count: Optional[int] = None
    mapping_follower_count: Optional[int] = None
    monthly_playcounts: Optional[List[Dict[str, Any]]] = None
    page: Optional[Dict[str, Any]] = None
    pending_beatmapset_count: Optional[int] = None
    previous_usernames: Optional[List[str]] = None
    rank_highest: Optional[Dict[str, Any]] = None
    rank_history: Optional[Dict[str, Any]] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[List[Dict[str, Any]]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional[UserStatistics] = None
    support_level: Optional[int] = None
    user_achievements: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserExtended':
        """从字典创建 UserExtended 对象"""
        if not data:
            return cls()
        
        # 处理统计信息
        statistics = None
        if 'statistics' in data and data['statistics']:
            stats_data = data['statistics']
            statistics = UserStatistics(
                count_100=stats_data.get('count_100'),
                count_300=stats_data.get('count_300'),
                count_50=stats_data.get('count_50'),
                count_miss=stats_data.get('count_miss'),
                level=stats_data.get('level'),
                global_rank=stats_data.get('global_rank'),
                global_rank_exp=stats_data.get('global_rank_exp'),
                pp=stats_data.get('pp'),
                pp_exp=stats_data.get('pp_exp'),
                ranked_score=stats_data.get('ranked_score'),
                hit_accuracy=stats_data.get('hit_accuracy'),
                play_count=stats_data.get('play_count'),
                play_time=stats_data.get('play_time'),
                total_score=stats_data.get('total_score'),
                total_hits=stats_data.get('total_hits'),
                maximum_combo=stats_data.get('maximum_combo'),
                replays_watched_by_others=stats_data.get('replays_watched_by_others'),
                is_ranked=stats_data.get('is_ranked'),
                grade_counts=stats_data.get('grade_counts'),
                country_rank=stats_data.get('country_rank'),
                rank=stats_data.get('rank'),
                variants=stats_data.get('variants')
            )
        
        # 处理徽章
        badges = None
        if 'badges' in data and data['badges']:
            badges = [
                UserBadge(
                    awarded_at=badge.get('awarded_at'),
                    description=badge.get('description'),
                    image_url=badge.get('image_url'),
                    image_2x_url=badge.get('image@2x_url'),
                    url=badge.get('url')
                ) for badge in data['badges']
            ]
        
        # 处理用户组
        groups = None
        if 'groups' in data and data['groups']:
            groups = [
                UserGroup(
                    colour=group.get('colour'),
                    has_listing=group.get('has_listing'),
                    has_playmodes=group.get('has_playmodes'),
                    id=group.get('id'),
                    identifier=group.get('identifier'),
                    is_probationary=group.get('is_probationary'),
                    name=group.get('name'),
                    short_name=group.get('short_name'),
                    playmodes=group.get('playmodes')
                ) for group in data['groups']
            ]
        
        return cls(
            # 基础用户信息
            avatar_url=data.get('avatar_url'),
            country_code=data.get('country_code'),
            country=data.get('country'),
            default_group=data.get('default_group'),
            id=data.get('id'),
            is_active=data.get('is_active'),
            is_bot=data.get('is_bot'),
            is_deleted=data.get('is_deleted'),
            is_online=data.get('is_online'),
            is_supporter=data.get('is_supporter'),
            last_visit=data.get('last_visit'),
            pm_friends_only=data.get('pm_friends_only'),
            profile_colour=data.get('profile_colour'),
            username=data.get('username'),
            
            # 扩展信息
            cover_url=data.get('cover_url'),
            discord=data.get('discord'),
            has_supported=data.get('has_supported'),
            interests=data.get('interests'),
            join_date=data.get('join_date'),
            kudosu=data.get('kudosu'),
            location=data.get('location'),
            max_blocks=data.get('max_blocks'),
            max_friends=data.get('max_friends'),
            occupation=data.get('occupation'),
            playmode=data.get('playmode'),
            playstyle=data.get('playstyle'),
            post_count=data.get('post_count'),
            profile_order=data.get('profile_order'),
            title=data.get('title'),
            title_url=data.get('title_url'),
            twitter=data.get('twitter'),
            website=data.get('website'),
            
            # 可选的扩展属性
            account_history=data.get('account_history'),
            active_tournament_banner=data.get('active_tournament_banner'),
            badges=badges,
            beatmap_playcounts_count=data.get('beatmap_playcounts_count'),
            favourite_beatmapset_count=data.get('favourite_beatmapset_count'),
            follower_count=data.get('follower_count'),
            graveyard_beatmapset_count=data.get('graveyard_beatmapset_count'),
            groups=groups,
            loved_beatmapset_count=data.get('loved_beatmapset_count'),
            mapping_follower_count=data.get('mapping_follower_count'),
            monthly_playcounts=data.get('monthly_playcounts'),
            page=data.get('page'),
            pending_beatmapset_count=data.get('pending_beatmapset_count'),
            previous_usernames=data.get('previous_usernames'),
            rank_highest=data.get('rank_highest'),
            rank_history=data.get('rank_history'),
            ranked_beatmapset_count=data.get('ranked_beatmapset_count'),
            replays_watched_counts=data.get('replays_watched_counts'),
            scores_best_count=data.get('scores_best_count'),
            scores_first_count=data.get('scores_first_count'),
            scores_recent_count=data.get('scores_recent_count'),
            statistics=statistics,
            support_level=data.get('support_level'),
            user_achievements=data.get('user_achievements')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        
        # 基础用户信息
        if self.avatar_url is not None:
            result['avatar_url'] = self.avatar_url
        if self.country_code is not None:
            result['country_code'] = self.country_code
        if self.default_group is not None:
            result['default_group'] = self.default_group
        if self.id is not None:
            result['id'] = self.id
        if self.is_active is not None:
            result['is_active'] = self.is_active
        if self.is_bot is not None:
            result['is_bot'] = self.is_bot
        if self.is_deleted is not None:
            result['is_deleted'] = self.is_deleted
        if self.is_online is not None:
            result['is_online'] = self.is_online
        if self.is_supporter is not None:
            result['is_supporter'] = self.is_supporter
        if self.last_visit is not None:
            result['last_visit'] = self.last_visit
        if self.pm_friends_only is not None:
            result['pm_friends_only'] = self.pm_friends_only
        if self.profile_colour is not None:
            result['profile_colour'] = self.profile_colour
        if self.username is not None:
            result['username'] = self.username
        
        # 扩展信息
        if self.cover_url is not None:
            result['cover_url'] = self.cover_url
        if self.discord is not None:
            result['discord'] = self.discord
        if self.has_supported is not None:
            result['has_supported'] = self.has_supported
        if self.interests is not None:
            result['interests'] = self.interests
        if self.join_date is not None:
            result['join_date'] = self.join_date
        if self.kudosu is not None:
            result['kudosu'] = self.kudosu
        if self.location is not None:
            result['location'] = self.location
        if self.max_blocks is not None:
            result['max_blocks'] = self.max_blocks
        if self.max_friends is not None:
            result['max_friends'] = self.max_friends
        if self.occupation is not None:
            result['occupation'] = self.occupation
        if self.playmode is not None:
            result['playmode'] = self.playmode
        if self.playstyle is not None:
            result['playstyle'] = self.playstyle
        if self.post_count is not None:
            result['post_count'] = self.post_count
        if self.profile_order is not None:
            result['profile_order'] = self.profile_order
        if self.title is not None:
            result['title'] = self.title
        if self.title_url is not None:
            result['title_url'] = self.title_url
        if self.twitter is not None:
            result['twitter'] = self.twitter
        if self.website is not None:
            result['website'] = self.website
        
        return result
