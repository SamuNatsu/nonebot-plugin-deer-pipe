import nonebot

from nonebot.adapters.console import Adapter as ConsoleAdapter
from pathlib import Path


nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ConsoleAdapter)

nonebot.load_plugin(Path("src/nonebot_plugin_deer_pipe"))

if __name__ == "__main__":
  nonebot.run()
