from enum import Enum

class HelpCommandInfo(Enum):
    LINK = (
        "参数: 无\n\n"
        "关联平台账号到 OSU! 账号\n"
    )
    UNLINK = (
        "参数: 无\n\n"
        "解除平台账号与 OSU! 账号的关联\n"
    )
    ME = (
        "参数: [模式]\n"
        "[模式] 可选值: osu, taiko, fruits, mania\n\n"
        "查看自己的 OSU! 账号信息\n"
    )
    USER = (
        "参数: <用户名/用户ID> [模式] [类型]\n"
        "<用户名/用户ID> - 用户名或用户ID\n"
        "[模式] 可选值: osu, taiko, fruits, mania\n"
        "[类型] 可选值: id, name\n\n"
        "查看指定用户的 OSU! 账号信息\n"
    )
    USERS = (
        "参数: 无\n\n"
        "批量查询用户信息（对话模式）\n"
        "提示: 在对话中提供需要查询的用户ID，以空格分隔\n"
    )
    HELP = (
        "参数: [命令]\n"
        "[命令] 可选值: 命令名称\n\n"
        "查看帮助信息\n"
        "提示: 如果不指定命令，将显示所有可用命令的简要信息\n"
    )
    UPDATE = (
        "参数: [模式]\n"
        "[模式] 可选值: osu, taiko, fruits, mania\n\n"
        "上传成绩到 OSU!track（默认 osu 模式）\n"
    )

    @classmethod
    def get(cls, command: str) -> str:
        """获取指定命令的帮助信息"""
        try:
            return cls[command].value
        except KeyError:
            return "未知命令或无帮助信息"