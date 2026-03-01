import nonebot

from nonebot.adapters.console import Adapter
from nonebot.drivers import Driver


# Framework initialize
nonebot.init()

# Driver
driver: Driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# Load plugin
try:
    nonebot.load_plugin("nonebot_plugin_deer_pipe")
except Exception:
    pass

# Main entry
if __name__ == "__main__":
    nonebot.run()
