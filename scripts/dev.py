import nonebot

from nonebot.adapters.onebot.v11 import Adapter
from nonebot.drivers import Driver


# Framework initialize
nonebot.init()
app = nonebot.get_asgi()

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
    nonebot.run(app="dev:app")
