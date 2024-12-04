# Load all needed plugins in advance
from . import requirements as requirements

# Load matchers
from . import matchers as matchers

from nonebot.plugin import PluginMetadata, inherit_supported_adapters


# Plugin metadata
__plugin_meta__: PluginMetadata = PluginMetadata(
    name="🦌管签到",
    description="一个🦌管签到插件",
    usage="发送“🦌帮助”以查看插件命令",
    type="application",
    homepage="https://github.com/SamuNatsu/nonebot-plugin-deer-pipe",
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_apscheduler",
        "nonebot_plugin_localstore",
        "nonebot_plugin_userinfo",
    ),
)
