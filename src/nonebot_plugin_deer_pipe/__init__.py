# __init__.py

from base64 import b64decode
from datetime import datetime

from nonebot import on_command
from nonebot.plugin import PluginMetadata, inherit_supported_adapters, require
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event

from .database import attend, leaderboard, reattend, get_user_avatar,add_user_avatar
from .image import generate_image, generate_leaderboard_image
from .constants import PLUGIN_PATH

# 引入依赖插件
require("nonebot_plugin_alconna")
require("nonebot_plugin_userinfo")

from nonebot_plugin_alconna import (
    Alconna, AlconnaMatcher, AlconnaMatches, Args, Arparma, on_alconna
)
from nonebot_plugin_userinfo import EventUserInfo, UserInfo, get_user_info
from nonebot_plugin_alconna.uniseg import UniMessage, At, at_me


# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="🦌管签到",
    description="一个🦌管签到插件",
    usage="发送🦌以进行签到",
    type="application",
    homepage="https://github.com/SamuNatsu/nonebot-plugin-deer-pipe",
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna", "nonebot_plugin_userinfo"
    )
)

# 定义指令匹配器
deer_matcher: AlconnaMatcher = on_alconna(Alconna("🦌"), aliases={"鹿", "撸"})
redeer_matcher: AlconnaMatcher = on_alconna(Alconna("补🦌", Args["day", int]), aliases={"补鹿", "补撸"})
help_deer_matcher: AlconnaMatcher = on_alconna(
    Alconna("帮🦌", Args["target", At, at_me]),
    aliases={"帮鹿", "帮撸"}
)
leader_board: AlconnaMatcher = on_alconna(Alconna("🦌排行榜", Args["month?", int]))


# 处理签到指令
@deer_matcher.handle()
async def handle_deer_signin(user_info: UserInfo = EventUserInfo()) -> None:
    """
    处理用户发送🦌指令进行签到
    """

    # 获取头像
    user_avatar = await get_user_avatar(user_info.user_id)
    if not user_avatar:
        user_avatar = await user_info.user_avatar.get_image()
        await add_user_avatar(user_info.user_id, user_avatar)

    name = user_info.user_remark or user_info.user_displayname or user_info.user_name
    now = datetime.now()

    # 执行签到逻辑
    deer = await attend(now, user_info.user_id)
    img = generate_image(now, name, deer, user_avatar)

    await UniMessage.text("成功🦌了").image(raw=img).finish(reply_to=True)


# 处理补签指令
@redeer_matcher.handle()
async def handle_deer_reattend(
    user_info: UserInfo = EventUserInfo(),
    result: Arparma = AlconnaMatches()
) -> None:
    """
    处理用户发送补🦌指令进行补签
    """

    # 获取头像
    user_avatar = await get_user_avatar(user_info.user_id)
    if not user_avatar:
        user_avatar = await user_info.user_avatar.get_image()
        await add_user_avatar(user_info.user_id, user_avatar)

    name = user_info.user_remark or user_info.user_displayname or user_info.user_name
    day = result.main_args["day"]
    now = datetime.now()

    # 验证补签日期是否合法
    if day <= 0 or day >= now.day:
        await UniMessage.text("不是合法的补🦌日期捏").finish(reply_to=True)

    # 执行补签逻辑
    ok, deer = await reattend(now, day, user_info.user_id)
    img = generate_image(now, name, deer, user_avatar)

    message = "成功补🦌" if ok else "只能补🦌没有🦌的日子捏"
    await UniMessage.text(message).image(raw=img).send(reply_to=True)


# 处理帮助签到指令
@help_deer_matcher.handle()
async def handle_help_deer(
    bot: Bot, 
    event: Event, 
    result: Arparma = AlconnaMatches()
) -> None:
    """
    处理用户发送帮🦌指令帮助他人签到
    """
    if result.matched:
        target = result.query[At]("target")
        uid = target.target

        if not uid:
            await UniMessage.text("似乎出了什么问题").finish(reply_to=True)
        else:
            # 获取目标用户信息
            user_info = await get_user_info(bot, event, uid)
            name = user_info.user_remark or user_info.user_displayname or user_info.user_name
            now = datetime.now()

            # 获取头像
            user_avatar = await get_user_avatar(user_info.user_id)
            if not user_avatar:
                user_avatar = await user_info.user_avatar.get_image()
                await add_user_avatar(user_info.user_id, user_avatar)

            # 执行签到逻辑
            deer = await attend(now, uid)
            img = generate_image(now, name, deer, user_avatar)
            await UniMessage.text(f"成功帮{name}🦌出来了").image(raw=img).finish(reply_to=True)
    else:
        await UniMessage.text("似乎出了什么问题").finish(reply_to=True)


# 处理排行榜指令
@leader_board.handle()
async def handle_leaderboard(
    bot: Bot, 
    event: Event, 
    result: Arparma = AlconnaMatches()
) -> None:
    """
    处理用户发送🦌排行榜指令查看排行榜
    """
    month = result.main_args.get("month")

    # 验证月份是否合法
    if month is not None:
        if month <= 0 or month > 12:
            await UniMessage.text("不是合法的月份捏").finish(reply_to=True)
        leaderboard_data = await leaderboard(month)
    else:
        leaderboard_data = await leaderboard()
    
    # 获取每个用户的显示名称和头像
    user_names = []
    for user_id, avatar_data, count in leaderboard_data:
        try:
            user_info = await get_user_info(bot, event, user_id)
            name = user_info.user_remark or user_info.user_displayname or user_info.user_name
            user_names.append((name, count, b64decode(avatar_data) if avatar_data else None))
        except:
            user_names.append((str(user_id), count, None))  # 获取失败时使用ID并无头像
    
    # 生成排行榜图片
    img = generate_leaderboard_image(month, user_names)
    await UniMessage.image(raw=img).finish(reply_to=True)


# 处理更新头像指令
update_avatar_matcher: AlconnaMatcher = on_alconna(Alconna("更新头像"),aliases={"更新头像", "修改头像"})

@update_avatar_matcher.handle()
async def handle_update_avatar(
    user_info: UserInfo = EventUserInfo(),
    result: Arparma = AlconnaMatches()
) -> None:
    """
    处理用户发送更新头像指令
    """
    # 获取头像

    user_avatar = await user_info.user_avatar.get_image()
    await add_user_avatar(user_info.user_id, user_avatar)
    if user_avatar:
        await UniMessage.text("头像更新成功").finish(reply_to=True)
    else:
        await UniMessage.text("头像更新失败").finish(reply_to=True)
