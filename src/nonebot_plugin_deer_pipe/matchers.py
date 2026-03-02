from .constants import PLUGIN_VERSION
from .database import check_in, get_deer_map
from .image import generate_calendar
from .utils import dl_img
from datetime import datetime
from nonebot_plugin_alconna import Alconna, AlconnaMatcher, Args, Match, on_alconna
from nonebot_plugin_alconna.uniseg import At, UniMessage
from nonebot_plugin_uninfo import Member, QryItrface, Uninfo


# Matchers
deer: type[AlconnaMatcher] = on_alconna(
    Alconna("🦌", Args["target?", At]), aliases={"鹿"}
)
deer_past: type[AlconnaMatcher] = on_alconna(
    Alconna("补🦌", Args["day", int]), aliases={"补鹿"}
)
deer_calendar: type[AlconnaMatcher] = on_alconna(
    Alconna("🦌历", Args["target?", At]), aliases={"鹿历"}
)
deer_help: type[AlconnaMatcher] = on_alconna(Alconna("🦌帮助"), aliases={"鹿帮助"})


# Handlers
@deer.handle()
async def _(session: Uninfo, interface: QryItrface, target: Match[At]) -> None:
    now: datetime = datetime.now()

    # Get user ID and avatar
    if target.available:
        user_id: str = target.result.target
        member: Member | None = await interface.get_member(
            session.scene.type, session.scene.id, user_id
        )
        avatar: bytes | None = (
            None
            if member is None or member.user.avatar is None
            else await dl_img(member.user.avatar)
        )
    else:
        user_id: str = session.user.id
        avatar: bytes | None = (
            None if session.user.avatar is None else await dl_img(session.user.avatar)
        )

    # Check in
    _, deer_map = await check_in(session, now, user_id)
    img: bytes = generate_calendar(now, deer_map, avatar)

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


@deer_past.handle()
async def _(session: Uninfo, day: Match[int]) -> None:
    now: datetime = datetime.now()

    # Get user ID and avatar
    user_id: str = session.user.id
    avatar: bytes | None = (
        None if session.user.avatar is None else await dl_img(session.user.avatar)
    )

    # Validate day
    if day.result < 1 or day.result >= now.day:
        await UniMessage.text("不是合法的补🦌日期捏").finish(reply_to=True)

    # Check in
    ok, deer_map = await check_in(session, now, user_id, day.result)
    img: bytes = generate_calendar(now, deer_map, avatar)

    # Reply
    if ok:
        await UniMessage.text("成功补🦌").image(raw=img).finish(reply_to=True)
    else:
        await (
            UniMessage.text("不能补🦌已经🦌过的日子捏")
            .image(raw=img)
            .finish(reply_to=True)
        )


@deer_calendar.handle()
async def _(session: Uninfo, interface: QryItrface, target: Match[At]) -> None:
    now: datetime = datetime.now()

    # Get user ID and avatar
    if target.available:
        user_id: str = target.result.target
        member: Member | None = await interface.get_member(
            session.scene.type, session.scene.id, user_id
        )
        avatar: bytes | None = (
            None
            if member is None or member.user.avatar is None
            else await dl_img(member.user.avatar)
        )
    else:
        user_id: str = session.user.id
        avatar: bytes | None = (
            None if session.user.avatar is None else await dl_img(session.user.avatar)
        )

    # Get image
    deer_map: dict[int, int] = await get_deer_map(session, now, user_id)
    img: bytes = generate_calendar(now, deer_map, avatar)

    # Reply
    await UniMessage.image(raw=img).finish(reply_to=True)


@deer_help.handle()
async def _() -> None:
    await (
        UniMessage.text(f"== 🦌管插件 v{PLUGIN_VERSION} 帮助 ==\n")
        .text("[🦌] 🦌管1次\n")
        .text("[🦌 @xxx] 帮xxx🦌管1次\n")
        .text("[补🦌 x] 补🦌本月x日\n")
        .text("[🦌历] 看本月🦌日历\n")
        .text("[🦌历 @xxx] 看xxx的本月🦌日历\n")
        .text("[🦌帮助] 打开帮助\n\n")
        .text("* 以上命令中的“🦌”均可换成“鹿”字\n\n")
        .text("== 插件代码仓库 ==\n")
        .text("https://github.com/SamuNatsu/nonebot-plugin-deer-pipe")
        .finish(reply_to=True)
    )
