from .database import attend, reattend
from .image import generate_image

from datetime import datetime
from nonebot.plugin import PluginMetadata, inherit_supported_adapters, require

require("nonebot_plugin_alconna")
require("nonebot_plugin_userinfo")

from nonebot_plugin_alconna import (
  Alconna, AlconnaMatcher, AlconnaMatches, Args, Arparma, UniMessage, on_alconna
)
from nonebot_plugin_userinfo import EventUserInfo, UserInfo


# Plugin meta
__plugin_meta__: PluginMetadata = PluginMetadata(
  name="🦌管签到",
  description="一个🦌管签到插件",
  usage="发送🦌以进行签到",
  type="application",
  homepage="https://github.com/SamuNatsu/nonebot-plugin-deer-pipe",
  supported_adapters=inherit_supported_adapters(
    "nonebot_plugin_alconna", "nonebot_plugin_userinfo"
  )
)

# Matchers
deer_matcher: AlconnaMatcher   = on_alconna("🦌")
redeer_matcher: AlconnaMatcher = on_alconna(Alconna("补🦌", Args["day", int]))

# Handlers
@deer_matcher.handle()
async def _(user_info: UserInfo = EventUserInfo()) -> None:
  name: str = (
    user_info.user_remark or
    user_info.user_displayname or
    user_info.user_name
  )
  now: datetime = datetime.now()

  deer: dict[int, int] = await attend(now, user_info.user_id)
  img: bytes = generate_image(now, name, deer)

  await UniMessage.text("成功🦌了").image(raw=img).finish(reply_to=True)

@redeer_matcher.handle()
async def _(
  user_info: UserInfo = EventUserInfo(),
  result: Arparma = AlconnaMatches()
) -> None:
  name: str = (
    user_info.user_remark or
    user_info.user_displayname or
    user_info.user_name
  )
  day: int = result.main_args["day"]
  now: datetime = datetime.now()

  if day <= 0 or day >= now.day:
    await UniMessage.text(f"不是合法的补🦌日期捏").finish(reply_to=True)

  ok, deer = await reattend(now, day, user_info.user_id)
  img: bytes = generate_image(now, name, deer)

  await (
    UniMessage
      .text("成功补🦌" if ok else "只能补🦌没有🦌的日子捏" )
      .image(raw=img)
      .send(reply_to=True)
  )
