import nonebot_plugin_localstore as localstore

from PIL import Image, ImageFont
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont
from importlib_metadata import version
from pathlib import Path


# Plugin info
PLUGIN_PATH: Path = Path(__file__).parent.resolve()
PLUGIN_VERSION: str = version("nonebot_plugin_deer_pipe")

# Assets
ASSETS_PATH: Path = PLUGIN_PATH / "assets"
ASSETS_FNT_MISANS: FreeTypeFont = ImageFont.truetype(
    ASSETS_PATH / "MiSans-Regular.ttf", 25
)
ASSETS_IMG_CHECK: ImageFile = Image.open(ASSETS_PATH / "check@96x100.png").convert(
    "RGBA"
)
ASSETS_IMG_DEERPIPE: ImageFile = Image.open(
    ASSETS_PATH / "deerpipe@100x82.png"
).convert("RGBA")

# Database
DATABASE_VERSION: int = 2
DATABASE_NAME: str = f"userdata-v{DATABASE_VERSION}.db"
DATABASE_PATH: Path = localstore.get_plugin_data_file(DATABASE_NAME)
DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"
