from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


class FontManager:
    def __init__(self, path: Path | tuple[Path, int]):
        self.fixed_size = path[1] if isinstance(path, tuple) else None
        self._font = ImageFont.truetype(
            path[0] if isinstance(path, tuple) else path,
            size=self.fixed_size or 25,
            layout_engine=ImageFont.Layout.RAQM,
        )
        self._cache = {self.fixed_size or 25: self._font}

    def _get(self, size: int = 25):
        size = self.fixed_size or size
        if size not in self._cache:
            self._cache[size] = self._font.font_variant(size=size)
        return self._cache[size]

    def getbbox(self, text: str, *, size: int = 25):
        font = self._get(size)
        if self.fixed_size is None:
            return font.getbbox(text)
        else:
            left, top, right, bottom = font.getbbox(text)
            w, h = right - left, bottom - top

            scale = size / self.fixed_size
            w, h = w * scale, h * scale

            return left, top, left + w, top + h

    def draw(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[float, float],
        text: str,
        *,
        size: int = 25,
        **kwargs: Any,
    ):
        font = self._get(size)
        if self.fixed_size is None:
            draw.text(xy, text, font=font, embedded_color=True, **kwargs)
        else:
            left, top, right, bottom = font.getbbox(text)
            w, h = right - left, bottom - top

            img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
            drw = ImageDraw.Draw(img)
            drw.text((0, 0), text, font=font, embedded_color=True, fill="white")

            scale = size / self.fixed_size
            w, h = int(img.width * scale), int(img.height * scale)

            img = img.resize((w, h), Image.Resampling.LANCZOS)
            draw._image.paste(img, (int(xy[0]), int(xy[1])), mask=img)


class FontDraw:
    def __init__(self, path: Path | tuple[Path, int], *paths: Path | tuple[Path, int]):
        self._managers: list[FontManager] = []
        self._mappings: dict[int, int] = {}

        existed_set: set[int] = set()
        for idx, path in enumerate((path, *paths)):
            self._managers.append(FontManager(path))

            cmap = TTFont(path[0] if isinstance(path, tuple) else path).getBestCmap()
            if cmap is not None:
                cmap_set = set(cmap.keys())
                self._mappings.update({i: idx for i in (cmap_set - existed_set)})
                existed_set |= cmap_set

    def _get_chunks(self, text: str):
        chunks = [(char, self._mappings.get(ord(char), 0)) for char in text]
        cluster = chunks[:1]
        for char, idx in chunks[1:]:
            if cluster[-1][1] == idx:
                cluster[-1] = (cluster[-1][0] + char, cluster[-1][1])
            else:
                cluster.append((char, idx))
        return cluster

    def get_width(self, text: str, *, size: int = 25):
        w = 0.0
        chunks = self._get_chunks(text)
        for text, idx in chunks:
            box = self._managers[idx].getbbox(text, size=size)
            w += box[2] - box[0]
        return w

    def draw(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[float, float],
        text: str,
        *,
        size: int = 25,
        **kwargs: Any,
    ):
        x, y = xy
        chunks = self._get_chunks(text)
        for text, idx in chunks:
            font = self._managers[idx]
            font.draw(draw, (x, y), text, size=size, **kwargs)
            box = font.getbbox(text, size=size)
            x += box[2] - box[0]
