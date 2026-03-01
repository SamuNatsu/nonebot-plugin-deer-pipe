from PIL import ImageFont
from pathlib import Path


class FontManager:
    def __init__(self, path: Path) -> None:
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(path, 25)
        self.cache: dict[int, ImageFont.FreeTypeFont] = {25: self.font}

    def get(self, size: int = 25) -> ImageFont.FreeTypeFont:
        if size not in self.cache:
            self.cache[size] = self.font.font_variant(size=size)
        return self.cache[size]
