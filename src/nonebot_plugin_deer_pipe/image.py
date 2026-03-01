import os
import nonebot_plugin_localstore as localstore
import secrets

from .constants import (
    ASSETS_FNT_MISANS,
    ASSETS_IMG_AVATAR,
    ASSETS_IMG_CHECK,
    ASSETS_IMG_DEERPIPE,
)
from PIL import Image, ImageDraw
from calendar import monthcalendar
from datetime import datetime
from io import BytesIO
from pathlib import Path


def generate_calendar(
    now: datetime, deer_map: dict[int, int], avatar: bytes | None
) -> bytes:
    """
    Generate calendar image

    :param now: Current time
    :param deer_map: A dictionary of `(day, deer_count)` pairs
    :param avatar: Optional user avatar
    """

    # Generate current month calendar
    cld: list[list[int]] = monthcalendar(now.year, now.month)

    # Image size & calendar cell size
    IMG_W, IMG_H = 700, 100 * (len(cld) + 1)
    CELL_W, CELL_H = 100, 100

    # Create image
    img: Image.Image = Image.new("RGBA", (IMG_W, IMG_H), "white")
    drw: ImageDraw.ImageDraw = ImageDraw.Draw(img)

    # Draw avatar
    if avatar is None:
        img.paste(ASSETS_IMG_AVATAR, (10, 10))
    else:
        avatar_img: Image.Image = (
            Image.open(BytesIO(avatar)).convert("RGBA").resize((80, 80))
        )
        img.paste(avatar_img, (10, 10))

    # Draw calendar info text
    drw.text(
        (100, 10),
        f"{now.year}-{now.month:02} 签到日历",
        fill="black",
        font=ASSETS_FNT_MISANS.get(),
    )

    # Draw cells
    for week_idx, week in enumerate(cld):
        for day_idx, day in enumerate(week):
            # Skip empty calendar cell
            if day == 0:
                continue

            # Cell position
            x0: int = day_idx * CELL_W
            y0: int = (week_idx + 1) * CELL_H

            # Draw cell
            img.paste(ASSETS_IMG_DEERPIPE, (x0, y0))
            drw.text(
                (x0 + 5, y0 + CELL_H - 35),
                str(day),
                fill="black",
                font=ASSETS_FNT_MISANS.get(),
            )

            # Skip day if not deered
            if day not in deer_map:
                continue

            # Draw check
            img.paste(ASSETS_IMG_CHECK, (x0, y0), ASSETS_IMG_CHECK)

            # Draw count if greater than 1
            if deer_map[day] > 1:
                font = ASSETS_FNT_MISANS.get(20)
                txt = "x999+" if deer_map[day] > 999 else f"x{deer_map[day]}"
                tlen = drw.textlength(txt, font=font)
                drw.text(
                    (x0 + CELL_W - tlen - 5, y0 + CELL_H - 25),
                    txt,
                    fill="red",
                    font=font,
                    stroke_width=1,
                )

    # Export image to bytes
    img_bytes: BytesIO = BytesIO()
    img.save(img_bytes, format="PNG")

    # Save image for development
    if os.getenv("DEER_PIPE_DEV") is not None:
        img_path: Path = localstore.get_plugin_cache_file(f"{secrets.token_hex()}.png")
        img.save(img_path)

    # Return bytes
    return img_bytes.getvalue()
