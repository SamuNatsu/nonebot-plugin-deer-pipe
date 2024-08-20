import calendar
import os
import secrets

from .constants import CHECK_IMG, DEERPIPE_IMG, MISANS_FONT, PLUGIN_PATH

from PIL import Image, ImageDraw
from datetime import datetime
from pathlib import Path


def generate_image(now: datetime, name: str, deer: dict[int, int]) -> bytes:
  cal: list[list[int]] = calendar.monthcalendar(now.year, now.month)

  IMG_W, IMG_H = 700, 100 * (len(cal) + 1)
  BOX_W, BOX_H = 100, 100

  img: Image.Image = Image.new("RGBA", (IMG_W, IMG_H), "white")
  drw: ImageDraw.ImageDraw = ImageDraw.Draw(img)

  for week_idx, week in enumerate(cal):
    for day_idx, day in enumerate(week):
      x0: int = day_idx * BOX_W
      y0: int = (week_idx + 1) * BOX_H
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
            txt: str = "x99+" if deer[day] > 99 else f"x{deer[day]}"
            tlen: float = drw.textlength(txt, font=MISANS_FONT)
            drw.text(
              (x0 + BOX_W - tlen - 5, y0 + BOX_H - 35),
              txt,
              fill="red",
              font=MISANS_FONT,
              stroke_width=1
            )

  drw.text((5, 5), f"{now.year}-{now.month:02} 签到", fill="black", font=MISANS_FONT)
  drw.text((5, 50), name, fill="black", font=MISANS_FONT)

  img_path: Path = PLUGIN_PATH / f"{secrets.token_hex()}.png"
  img.save(img_path)

  with open(img_path, "rb") as f:
    raw: bytes = f.read()
  os.remove(img_path)

  return raw
