import nonebot_plugin_localstore as localstore

from .font import FontDraw
from PIL import Image
from importlib_metadata import version
from pathlib import Path


# Plugin info
PLUGIN_PATH = Path(__file__).parent.resolve()
PLUGIN_VERSION = version("nonebot_plugin_deer_pipe")

# Assets
ASSETS_PATH = PLUGIN_PATH / "assets"
ASSETS_FONT = FontDraw(
    ASSETS_PATH / "MiSans-Regular.ttf", (ASSETS_PATH / "NotoColorEmoji.ttf", 109)
)
ASSETS_IMG_AVATAR = Image.open(ASSETS_PATH / "akkarin@80x80.png").convert("RGBA")
ASSETS_IMG_CHECK = Image.open(ASSETS_PATH / "check@96x100.png").convert("RGBA")
ASSETS_IMG_DEERPIPE = Image.open(ASSETS_PATH / "deerpipe@100x82.png").convert("RGBA")

# Database
DATABASE_VERSION = 3
DATABASE_NAME = f"userdata-v{DATABASE_VERSION}.db"
DATABASE_PATH = localstore.get_plugin_data_file(DATABASE_NAME)
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
