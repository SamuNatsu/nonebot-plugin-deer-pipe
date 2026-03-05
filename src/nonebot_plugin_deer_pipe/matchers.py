from .constants import PLUGIN_VERSION
from .database import check_in, get_records, get_user, update_user
from .image import gen_calendar, gen_rank
from .schedule import latest_version
from .utils import get_member_info, get_member_rank, get_user_info
from datetime import datetime, timedelta
from nonebot_plugin_alconna import Alconna, Args, Match, on_alconna
from nonebot_plugin_alconna.uniseg import At, UniMessage
from nonebot_plugin_uninfo import QryItrface, Uninfo
from pytimeparse import parse
from typing import Literal

# Matchers
_deer = on_alconna(Alconna("🦌", Args["target?", At]), aliases={"鹿"})
_deer_past = on_alconna(Alconna("补🦌", Args["day", int]), aliases={"补鹿"})
_deer_calendar = on_alconna(Alconna("🦌历", Args["target?", At]), aliases={"鹿历"})
_deer_rank = on_alconna(Alconna("🦌榜"), aliases={"鹿榜"})
_set_can_be_helped = on_alconna(
    Alconna("帮🦌", Args["can_be_helped", Literal["on", "off"]], Args["target?", At]),
    aliases={"帮鹿"},
)
_set_no_deer_until = on_alconna(
    Alconna("禁🦌", Args["target", At], Args["duration?", str]), aliases={"禁鹿"}
)
_deer_help = on_alconna(Alconna("🦌帮助"), aliases={"鹿帮助"})


# Handlers
@_deer.handle()
async def _(session: Uninfo, interface: QryItrface, target: Match[At]):
    now = datetime.now()

    # Skip non-group scene
    if target.available and not (session.scene.is_channel or session.scene.is_group):
        _deer.skip()

    # Get user info
    if target.available:
        user_id = target.result.target
        name, avatar, user = await get_member_info(session, interface, user_id)
    else:
        user_id = session.user.id
        name, avatar, user = await get_user_info(session)

    # If can't be helped
    if target.available and not user.can_be_helped:
        await UniMessage.text("该用户不准别人帮🦌捏").finish(reply_to=True)

    # If no deer
    if (
        (session.scene.is_channel or session.scene.is_group)
        and user.no_deer_until is not None
        and user.no_deer_until > now
    ):
        await UniMessage.text(
            f"该用户已被禁🦌至{user.no_deer_until.isoformat()}"
        ).finish(reply_to=True)

    # Check in
    _, records = await check_in(now, user)
    img = gen_calendar(now, records, name, avatar)

    # Reply
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


@_deer_past.handle()
async def _(session: Uninfo, day: Match[int]):
    now = datetime.now()

    # Get user info
    name, avatar, user = await get_user_info(session)

    # Validate day
    if day.result < 1 or day.result >= now.day:
        await UniMessage.text("不是合法的补🦌日期捏").finish(reply_to=True)

    # Check in
    ok, records = await check_in(now, user, day.result)
    img = gen_calendar(now, records, name, avatar)

    # Reply
    if ok:
        await UniMessage.text("成功补🦌").image(raw=img).finish(reply_to=True)
    else:
        await (
            UniMessage.text("不能补🦌已经🦌过的日子捏")
            .image(raw=img)
            .finish(reply_to=True)
        )


@_deer_calendar.handle()
async def _(session: Uninfo, interface: QryItrface, target: Match[At]):
    now = datetime.now()

    # Skip non-group scene
    if target.available and not (session.scene.is_channel or session.scene.is_group):
        _deer_calendar.skip()

    # Get user info
    if target.available:
        user_id = target.result.target
        name, avatar, user = await get_member_info(session, interface, user_id)
    else:
        user_id = session.user.id
        name, avatar, user = await get_user_info(session)

    # Get image
    records = await get_records(now, user)
    img = gen_calendar(now, records, name, avatar)

    # Reply
    await UniMessage.image(raw=img).finish(reply_to=True)


@_deer_rank.handle()
async def _(session: Uninfo, interface: QryItrface):
    now = datetime.now()

    # Skip non-group scene
    if not (session.scene.is_channel or session.scene.is_group):
        _deer_rank.skip()

    # Get image
    rank = await get_member_rank(session, interface, now)
    img = gen_rank(rank)

    # Reply
    await UniMessage.image(raw=img).finish(reply_to=True)


@_set_can_be_helped.handle()
async def _(
    session: Uninfo, can_be_helped: Match[Literal["on", "off"]], target: Match[At]
):
    # Skip non-group scene
    if (
        not (session.scene.is_channel or session.scene.is_group)
        or session.member is None
        or session.member.role is None
    ):
        _set_can_be_helped.skip()

    # Validate admin
    if target.available and session.member.role.level <= 1:
        await UniMessage.text("权限不足").finish(reply_to=True)

    # Get user info
    user_id = target.result.target if target.available else session.user.id
    user = await get_user(session, user_id)

    # Update user
    allowed = can_be_helped.result == "on"
    user.can_be_helped = allowed
    await update_user(user)

    # Reply
    if target.available:
        await (
            UniMessage.text(f"已{'允许' if allowed else '禁止'}帮")
            .at(user_id)
            .text("🦌")
            .finish(reply_to=True)
        )
    else:
        await UniMessage.text(f"已{'允许' if allowed else '禁止'}帮🦌").finish(
            reply_to=True
        )


@_set_no_deer_until.handle()
async def _(session: Uninfo, target: Match[At], duration: Match[str]):
    now = datetime.now()
    MAX_DURATION = 30 * 86400

    # Skip non-group scene
    if (
        not (session.scene.is_channel or session.scene.is_group)
        or session.member is None
        or session.member.role is None
    ):
        _set_no_deer_until.skip()

    # Validate admin
    if session.member.role.level <= 1:
        await UniMessage.text("权限不足").finish(reply_to=True)

    # Validate duration
    if duration.available and parse(duration.result) is None:
        await UniMessage.text("时间段表达式解析错误").finish(reply_to=True)

    # Get user info
    user_id = target.result.target
    user = await get_user(session, user_id)

    # Update user
    dur = parse(duration.result) if duration.available else None

    # Validate dur
    if dur is not None:
        if dur > MAX_DURATION:
            await UniMessage.text(
                f"时间段过长：最大允许时间为 {MAX_DURATION // 86400} 天"
            ).finish(reply_to=True)

    until = None if dur is None else now + timedelta(seconds=dur)
    user.no_deer_until = until
    await update_user(user)

    # Reply
    if until is None:
        await UniMessage.text("已解禁").at(user_id).text("的🦌权").finish(reply_to=True)
    else:
        await (
            UniMessage.text("已禁止")
            .at(user_id)
            .text(f"的🦌权至{until.isoformat()}")
            .finish(reply_to=True)
        )


@_deer_help.handle()
async def _():
    await (
        UniMessage.text(f"== 🦌管插件 v{PLUGIN_VERSION} 帮助 ==\n")
        .text("[🦌] 🦌管1次\n")
        .text("[🦌 @xxx] 帮xxx🦌管1次（仅群组）\n")
        .text("[补🦌 x] 补🦌本月x日\n")
        .text("[🦌历] 看本月🦌日历\n")
        .text("[🦌历 @xxx] 看xxx的本月🦌日历（仅群组）\n")
        .text("[🦌榜] 看本月本群🦌排行榜（仅群组）\n")
        .text("[帮🦌 <on|off>] 禁止/允许别人帮🦌（仅群组）\n")
        .text("[帮🦌 <on|off> @xxx] 禁止/允许别人帮xxx🦌（仅群组管理员）\n")
        .text(
            "[禁🦌 @xxx [yyy]] xxx接下来一段时间yyy内禁止🦌，不提供yyy时视为解禁（仅群组管理员，yyy为pytimeparse时间段表达式）\n"
        )
        .text("[🦌帮助] 打开帮助\n\n")
        .text("* 以上命令中的“🦌”均可换成“鹿”字\n\n")
        .text("== 插件代码仓库 ==\n")
        .text("https://github.com/SamuNatsu/nonebot-plugin-deer-pipe")
        .text(
            ""
            if PLUGIN_VERSION == latest_version
            else f"\n\n== 插件有新版本可用：v{latest_version} =="
        )
        .finish(reply_to=True)
    )
