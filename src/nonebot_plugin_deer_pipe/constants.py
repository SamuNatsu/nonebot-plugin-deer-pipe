# constants.py

from pathlib import Path
from PIL import Image, ImageFile, ImageFont
from nonebot.plugin import require

# 引入本地存储插件
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

# 插件路径
PLUGIN_PATH: Path = Path(__file__).parent.resolve()
ASSETS_PATH: Path = PLUGIN_PATH / "assets"

# 加载图片资源
CHECK_IMG: ImageFile = Image.open(ASSETS_PATH / "check@96x100.png").convert("RGBA")
DEERPIPE_IMG: ImageFile = Image.open(ASSETS_PATH / "deerpipe@100x82.png").convert("RGBA")

# 加载字体
MISANS_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    str(ASSETS_PATH / "MiSans-Regular.ttf"),
    25
)

# 数据库配置
DATABASE_VERSION: int = 1
DATABASE_NAME: str = f"userdata-v{DATABASE_VERSION}.db"
DATABASE_PATH: Path = store.get_plugin_data_file(DATABASE_NAME)
DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"
