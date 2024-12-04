from .constants import PLUGIN_VERSION
from .database import (
    attend,
    attend_past,
    get_avatar,
    update_avatar,
    get_deer_map,
)
from .image import generate_calendar

from datetime import datetime
from nonebot_plugin_alconna import (
    Alconna,
    AlconnaMatcher,
    Args,
    Match,
    on_alconna,
)
from nonebot_plugin_alconna.uniseg import At, UniMessage
from nonebot_plugin_userinfo import EventUserInfo, UserInfo


# Matchers
deer: AlconnaMatcher = on_alconna(Alconna("🦌", Args["target?", At]), aliases={"鹿"})
deer_past: AlconnaMatcher = on_alconna(
    Alconna("补🦌", Args["day", int]), aliases={"补鹿"}
)
deer_calendar: AlconnaMatcher = on_alconna(
    Alconna("🦌历", Args["target?", At]), aliases={"鹿历"}
)
# deer_top: AlconnaMatcher = on_alconna(Alconna("🦌榜"), aliases={"鹿榜"})
deer_help: AlconnaMatcher = on_alconna(Alconna("🦌帮助"), aliases={"鹿帮助"})


# Handlers
@deer.handle()
async def _(target: Match[At], user_info: UserInfo = EventUserInfo()) -> None:
    now: datetime = datetime.now()

    if target.available:
        user_id: str = target.result.target
        avatar: bytes | None = await get_avatar(user_id)
    else:
        user_id: str = user_info.user_id
        avatar: bytes | None = (
            await user_info.user_avatar.get_image()
            if user_info.user_avatar is not None
            else None
        )
        await update_avatar(user_id, avatar)

    deer_map: dict[int, int] = await attend(user_id, now)
    img: bytes = generate_calendar(now, deer_map, avatar)

    if target.available:
        await (
            UniMessage.text("成功帮")
            .at(user_id)
            .text("🦌了")
            .image(raw=img)
            .finish(reply_to=True)
        )
    else:
        await UniMessage.text("成功🦌了").image(raw=img).finish(reply_to=True)


@deer_past.handle()
async def _(day: Match[int], user_info: UserInfo = EventUserInfo()) -> None:
    now: datetime = datetime.now()
    user_id = user_info.user_id
    avatar: bytes | None = (
        await user_info.user_avatar.get_image()
        if user_info.user_avatar is not None
        else None
    )
    await update_avatar(user_id, avatar)

    if day.result < 1 or day.result >= now.day:
        await UniMessage.text("不是合法的补🦌日期捏").finish(reply_to=True)

    ok, deer_map = await attend_past(user_id, now, day.result)
    img: bytes = generate_calendar(now, deer_map, avatar)

    if ok:
        await UniMessage.text("成功补🦌").image(raw=img).finish(reply_to=True)
    else:
        await (
            UniMessage.text("不能补🦌已经🦌过的日子捏")
            .image(raw=img)
            .finish(reply_to=True)
        )


@deer_calendar.handle()
async def _(target: Match[At], user_info: UserInfo = EventUserInfo()) -> None:
    now: datetime = datetime.now()

    if target.available:
        user_id: str = target.result.target
        avatar: bytes | None = await get_avatar(user_id)
    else:
        user_id: str = user_info.user_id
        avatar: bytes | None = (
            await user_info.user_avatar.get_image()
            if user_info.user_avatar is not None
            else None
        )
        await update_avatar(user_id, avatar)

    deer_map: dict[int, int] = await get_deer_map(user_id, now)
    img: bytes = generate_calendar(now, deer_map, avatar)

    await UniMessage.image(raw=img).finish(reply_to=True)


# @deer_top.handle()
# async def _() -> None:
#     pass


@deer_help.handle()
async def _() -> None:
    await (
        UniMessage.text(f"== 🦌管插件 v{PLUGIN_VERSION} 帮助 ==\n")
        .text("[🦌] 🦌管1次\n")
        .text("[🦌 @xxx] 帮xxx🦌管1次\n")
        .text("[补🦌 x] 补🦌本月x日\n")
        .text("[🦌历] 看本月🦌日历\n")
        .text("[🦌历 @xxx] 看xxx的本月🦌日历\n")
        # .text("[🦌榜] 看本月🦌排行榜\n")
        .text("[🦌帮助] 打开帮助\n\n")
        .text("* 以上命令中的“🦌”均可换成“鹿”字\n\n")
        .text("== 插件代码仓库 ==\n")
        .text("https://github.com/SamuNatsu/nonebot-plugin-deer-pipe")
        .finish(reply_to=True)
    )
