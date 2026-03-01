import nonebot_plugin_localstore as localstore

from .utils import FontManager
from PIL import Image
from importlib_metadata import version
from pathlib import Path


# Plugin info
PLUGIN_PATH: Path = Path(__file__).parent.resolve()
PLUGIN_VERSION: str = version("nonebot_plugin_deer_pipe")

# Assets
ASSETS_PATH: Path = PLUGIN_PATH / "assets"
ASSETS_FNT_MISANS: FontManager = FontManager(ASSETS_PATH / "MiSans-Regular.ttf")
ASSETS_IMG_CHECK: Image.Image = Image.open(ASSETS_PATH / "check@96x100.png").convert(
    "RGBA"
)
ASSETS_IMG_DEERPIPE: Image.Image = Image.open(
    ASSETS_PATH / "deerpipe@100x82.png"
).convert("RGBA")

# Database
DATABASE_VERSION: int = 2
DATABASE_NAME: str = f"userdata-v{DATABASE_VERSION}.db"
DATABASE_PATH: Path = localstore.get_plugin_data_file(DATABASE_NAME)
DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"
