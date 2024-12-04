import os
import secrets

from .constants import (
    ASSETS_FNT_MISANS,
    ASSETS_IMG_CHECK,
    ASSETS_IMG_DEERPIPE,
    PLUGIN_PATH,
)

from PIL import Image, ImageDraw
from calendar import monthcalendar
from datetime import datetime
from io import BytesIO
from pathlib import Path


# Generate calendar image
def generate_calendar(
    now: datetime, deer_map: dict[int, int], avatar: bytes | None
) -> bytes:
    cld: list[list[int]] = monthcalendar(now.year, now.month)

    IMG_W, IMG_H = 700, 100 * (len(cld) + 1)
    BOX_W, BOX_H = 100, 100

    img: Image.Image = Image.new("RGBA", (IMG_W, IMG_H), "white")
    drw: ImageDraw.ImageDraw = ImageDraw.Draw(img)

    if avatar is not None:
        avatar_img: Image.Image = (
            Image.open(BytesIO(avatar)).convert("RGBA").resize((80, 80))
        )
        img.paste(avatar_img, (10, 10))

    drw.text(
        (100, 10),
        f"{now.year}-{now.month:02} 签到日历",
        fill="black",
        font=ASSETS_FNT_MISANS,
    )
    for week_idx, week in enumerate(cld):
        for day_idx, day in enumerate(week):
            x0: int = day_idx * BOX_W
            y0: int = (week_idx + 1) * BOX_H
            if day != 0:
                img.paste(ASSETS_IMG_DEERPIPE, (x0, y0))
                drw.text(
                    (x0 + 5, y0 + BOX_H - 35),
                    str(day),
                    fill="black",
                    font=ASSETS_FNT_MISANS,
                )
                if day in deer_map:
                    img.paste(ASSETS_IMG_CHECK, (x0, y0), ASSETS_IMG_CHECK)
                    if deer_map[day] > 1:
                        txt = "x99+" if deer_map[day] > 99 else f"x{deer_map[day]}"
                        tlen = drw.textlength(txt, font=ASSETS_FNT_MISANS)
                        drw.text(
                            (x0 + BOX_W - tlen - 5, y0 + BOX_H - 35),
                            txt,
                            fill="red",
                            font=ASSETS_FNT_MISANS,
                            stroke_width=1,
                        )

    img_path: Path = PLUGIN_PATH / f"{secrets.token_hex()}.png"
    img.save(img_path)

    with open(img_path, "rb") as f:
        raw: bytes = f.read()
    os.remove(img_path)

    return raw
