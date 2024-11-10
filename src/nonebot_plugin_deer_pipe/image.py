# image.py

import calendar
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from .constants import (
    CHECK_IMG, DEERPIPE_IMG, MISANS_FONT, PLUGIN_PATH
)
from .database import User, leaderboard


# image.py

from io import BytesIO

def generate_image(now: datetime, name: str, deer: dict[int, int], avatar: Optional[bytes]) -> bytes:
    """
    生成用户签到日历图片，并在指定位置添加用户头像
    """
    cal = calendar.monthcalendar(now.year, now.month)

    IMG_W, IMG_H = 700, 100 * (len(cal) + 1)
    BOX_W, BOX_H = 100, 100

    img = Image.new("RGBA", (IMG_W, IMG_H), "white")
    drw = ImageDraw.Draw(img)

    # 添加用户头像
    if avatar:
        avatar_img = Image.open(BytesIO(avatar)).convert("RGBA")
        avatar_img = avatar_img.resize((80, 80))  # 调整头像大小
        img.paste(avatar_img, (IMG_W - 90, 10), avatar_img)

    for week_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
            x0 = day_idx * BOX_W
            y0 = (week_idx + 1) * BOX_H
            if day != 0:
                img.paste(DEERPIPE_IMG, (x0, y0))
                drw.text(
                    (x0 + 5, y0 + BOX_H - 35),
                    str(day),
                    fill="black",
                    font=MISANS_FONT
                )
                if day in deer:
                    img.paste(CHECK_IMG, (x0, y0), CHECK_IMG)
                    if deer[day] > 1:
                        txt = "x99+" if deer[day] > 99 else f"x{deer[day]}"
                        tlen = drw.textlength(txt, font=MISANS_FONT)
                        drw.text(
                            (x0 + BOX_W - tlen - 5, y0 + BOX_H - 35),
                            txt,
                            fill="red",
                            font=MISANS_FONT,
                            stroke_width=1
                        )

    # 添加标题和用户名
    drw.text((5, 5), f"{now.year}-{now.month:02} 签到", fill="black", font=MISANS_FONT)
    drw.text((5, 50), name, fill="black", font=MISANS_FONT)

    # 保存临时图片并读取为字节
    img_path = PLUGIN_PATH / f"{secrets.token_hex()}.png"
    img.save(img_path)

    with open(img_path, "rb") as f:
        raw = f.read()
    os.remove(img_path)

    return raw


def generate_leaderboard_image(now: Optional[int], user_names: List[Tuple[str, int, Optional[bytes]]]) -> bytes:
    """
    生成带有用户头像的排行榜图片
    """
    IMG_W, IMG_H = 900, 100 * (len(user_names) + 1)
    BOX_H = 100

    img = Image.new("RGBA", (IMG_W, IMG_H), "white")
    drw = ImageDraw.Draw(img)

    title = "总排行榜" if now is None else f"{now}月 排行榜"
    drw.text((5, 5), title, fill="black", font=MISANS_FONT)

    for idx, (name, count, avatar) in enumerate(user_names):
        y0 = (idx + 1) * BOX_H
        if avatar:
            try:
                avatar_img = Image.open(BytesIO(avatar)).convert("RGBA")
                avatar_img = avatar_img.resize((80, 80))
                img.paste(avatar_img, (5, y0 + 10), avatar_img)
            except UnidentifiedImageError:
                pass  # Optionally log the error or use a default image
        drw.text((100, y0 + 5), f"#{idx + 1} {name}", fill="black", font=MISANS_FONT)
        drw.text((100, y0 + 50), f"次数: {count}", fill="black", font=MISANS_FONT)

    img_path = PLUGIN_PATH / f"{secrets.token_hex()}.png"
    img.save(img_path)

    with open(img_path, "rb") as f:
        raw = f.read()
    os.remove(img_path)

    return raw
