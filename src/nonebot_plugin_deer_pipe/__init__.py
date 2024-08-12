from .database import attend
from .image import generate_image

from datetime import datetime
from nonebot.plugin import PluginMetadata, inherit_supported_adapters, require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage, on_alconna

require("nonebot_plugin_userinfo")
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
deer_matcher = on_alconna("🦌")

# Handlers
@deer_matcher.handle()
async def handle(user_info: UserInfo = EventUserInfo()) -> None:
  name: str = (
    user_info.user_remark or
    user_info.user_displayname or
    user_info.user_name
  )

  now: datetime = datetime.now()
  ok, deer = await attend(now, user_info.user_id)
  img: bytes = generate_image(now, name, deer)

  await UniMessage.text(
      f"{name} 刚刚🦌了" if ok else f"{name} 今天已经🦌过了"
    ).image(raw=img).send()
