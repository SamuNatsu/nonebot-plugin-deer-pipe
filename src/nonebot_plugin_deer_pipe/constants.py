from PIL import Image, ImageFont
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont
from nonebot.plugin import require
from pathlib import Path

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store


# Plugin paths
PLUGIN_PATH: Path = Path(__file__).parent.resolve()
ASSETS_PATH: Path = PLUGIN_PATH / "assets"

# Images
CHECK_IMG: ImageFile    = Image.open(ASSETS_PATH / "check@96x100.png")
DEERPIPE_IMG: ImageFile = Image.open(ASSETS_PATH / "deerpipe@100x82.png")

# Fonts
MISANS_FONT: FreeTypeFont = ImageFont.truetype(
  str(ASSETS_PATH / "MiSans-Regular.ttf"),
  25
)

# Database
DATABASE_VERSION: int = 1
DATABASE_NAME: str    = f"userdata-v{DATABASE_VERSION}.db"
DATABASE_PATH: Path   = store.get_plugin_data_file(DATABASE_NAME)
DATABASE_URL: str     = f"sqlite+aiosqlite:///{DATABASE_PATH}"
