import asyncio

from PIL import ImageFont
from aiocache import cached
from aiohttp import ClientSession
from enum import Enum, auto
from nonebot.log import logger
from pathlib import Path


class NotSet(Enum):
    NOT_SET = auto()


class FontManager:
    def __init__(self, path: Path) -> None:
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(path, 25)
        self.cache: dict[int, ImageFont.FreeTypeFont] = {25: self.font}

    def get(self, size: int = 25) -> ImageFont.FreeTypeFont:
        if size not in self.cache:
            self.cache[size] = self.font.font_variant(size=size)
        return self.cache[size]


@cached(ttl=86400)
async def dl_img(url: str) -> bytes | None:
    """
    Download image by URL with 1h caching

    :param url: Image URL
    """
    async with ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()
            except Exception as e:
                logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                await asyncio.sleep(1)
