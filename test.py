import nonebot

from nonebot.adapters.onebot.v11 import Adapter
from pathlib import Path


# Framework
nonebot.init()
app = nonebot.get_asgi()

# Driver
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# Load plugin
try:
  nonebot.load_plugin(Path("src/nonebot_plugin_deer_pipe"))
except:
  pass

# Main entry
if __name__ == "__main__":
  nonebot.run(app="test:app")
