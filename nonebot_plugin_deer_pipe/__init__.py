import calendar
import json
import os
import secrets

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMessage, on_alconna
from nonebot_plugin_userinfo import EventUserInfo, UserInfo
from typing import Any, Sequence

# Plugin meta
__plugin_meta__: PluginMetadata = PluginMetadata(
  name="nonebot-plugin-deer-pipe",
  description="一个🦌管签到插件",
  usage="发送🦌以进行签到",
  type="application",
  homepage="https://github.com/SamuNatsu/nonebot-plugin-deer-pipe"
)

# Constants
PLUGIN_PATH: str = os.path.dirname(os.path.realpath(__file__))
USERDATA_PATH: str = f"{PLUGIN_PATH}/userdata.json"

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

# Generate image
def gen_img(now: datetime, title: str, deer: Sequence[int]) -> bytes:
  font = ImageFont.truetype(f"{PLUGIN_PATH}/MiSans_VF.ttf", 20)
  caln = calendar.monthcalendar(now.year, now.month)

  img_w, img_h = 700, 100 * (len(caln) + 1)
  ret_img = Image.new("RGBA", (img_w, img_h), "white")
  draw = ImageDraw.Draw(ret_img)

  box_w, box_h = 100, 100

  deer_img = Image.open(f"{PLUGIN_PATH}/deerpipe.jpg")
  deer_w, deer_h = deer_img.size
  deer_s: float = 100 / max(deer_w, deer_h)
  deer_img = deer_img.resize((int(deer_w * deer_s), int(deer_h * deer_s)))

  check_img = Image.open(f"{PLUGIN_PATH}/check.png")
  check_w, check_h = check_img.size
  check_s: float = 100 / max(check_w, check_h)
  check_img = check_img.resize((int(check_w * check_s), int(check_h * check_s)))

  for week_num, week in enumerate(caln):
    for day_num, day in enumerate(week):
      x0 = day_num * box_w
      y0 = (week_num + 1) * box_h
      if day != 0:
        ret_img.paste(deer_img, (x0, y0))
        draw.text((x0 + 5, y0 + box_h - 35), str(day), fill='black', font=font)
        if day in deer:
          ret_img.paste(check_img, (x0, y0), check_img)

  font = ImageFont.truetype(f"{PLUGIN_PATH}/MiSans_VF.ttf", 40)
  draw.text((5, 5), f"{now.year}-{now.month:02} 签到", fill="black", font=font)
  draw.text((5, 50), title, fill="black", font=font)

  img_path = f"{PLUGIN_PATH}/{secrets.token_hex()}.png"
  ret_img.save(img_path)

  with open(img_path, "rb") as f:
    ret_raw = f.read()
  os.remove(img_path)

  return ret_raw

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
  img: bytes = gen_img(now, name, deer)

  await UniMessage.text(
      f"{name} 刚刚🦌了" if ok else f"{name} 今天已经🦌过了"
    ).image(raw=img).send()
