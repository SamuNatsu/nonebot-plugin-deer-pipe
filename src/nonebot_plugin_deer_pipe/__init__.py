import json
import os

from .contants import USERDATA_PATH
from .image import generate_image
from datetime import datetime
from nonebot.plugin import PluginMetadata, require
from typing import Any, Sequence

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
  supported_adapters={
    "~console",
    "~discord",
    "~dodo",
    "~feishu",
    "~kaiheila",
    "~onebot.v11",
    "~onebot.v12",
    "~qq",
    "~red",
    "~satori",
    "~telegram",
    }
)

# Attendance
def attendance(now: datetime, user_id: str) -> tuple[bool, Sequence[int]]:
  if not os.path.exists(USERDATA_PATH):
    raw_data: str = "{}"
  else:
    with open(USERDATA_PATH) as f:
      raw_data: str = f.read()
  
  data: dict[str, Any] = json.loads(raw_data)
  userdata: dict[str, Any] | None = data.get(user_id)
  if userdata == None:
    userdata = { "year": now.year, "month": now.month, "deer": [] }
    data[user_id] = userdata
  
  if userdata["year"] != now.year or userdata["month"] != now.month:
    userdata = { "year": now.year, "month": now.month, "deer": [] }
    data[user_id] = userdata
  
  if now.day in userdata["deer"]:
    with open(USERDATA_PATH, "w") as f:
      json.dump(data, f)
    return (False, userdata["deer"])
  
  userdata["deer"].append(now.day)
  with open(USERDATA_PATH, "w") as f:
    json.dump(data, f)
  return (True, userdata["deer"])

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
  ok, deer = attendance(now, user_info.user_id)
  img: bytes = generate_image(now, name, deer)

  await UniMessage.text(
      f"{name} 刚刚🦌了" if ok else f"{name} 今天已经🦌过了"
    ).image(raw=img).send()
