import functions
import osutrack
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

@register("osutrack","gameswu","基于osu!track与osu!api的osu!成绩查询插件","0.1.0","https://github.com/gameswu/astrbot_plugin_osutrack")
class OsuTrackPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        self.api_key = self.config.get("api_key")
        self.functions = functions.PluginFunctions()
        self.functions.set_api_key(api_key=self.api_key)

    @filter.command("osu_update")
    async def osu_update(self, event: AstrMessageEvent, user_id: str, mode: int):
        """
        更新用户成绩至osu!track并返回详细结果
        """
        result = await self.functions.update_user_score(user_id=user_id, mode=mode)
        if result[0]:
            # 获取更新成绩数量"newhs"数组的元素数量
            newhs_count = len(result[2].get("newhs", []))
            osu_username = result[1]
            logger.info(f"成功更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩")
            yield event.plain_result(f"成功帮主人更新用户 {osu_username} (ID: {user_id}) 在模式 {mode} 的成绩喵~ 更新了 {newhs_count} 条新成绩喵呜")
        else:
            logger.warning(f"更新用户成绩失败: 用户ID {user_id}, 模式 {mode}, API返回空响应")
            yield event.plain_result(f"帮主人更新用户成绩失败了喵 用户ID {user_id}, 模式 {mode}, API返回没有响应喵")

    async def terminate(self):
        return await super().terminate()