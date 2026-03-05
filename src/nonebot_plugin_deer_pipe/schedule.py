import asyncio

from .database import cleanup
from aiohttp import ClientSession
from importlib_metadata import version
from nonebot.log import logger
from nonebot_plugin_apscheduler import scheduler

# Global variables
latest_version = version("nonebot_plugin_deer_pipe")


# Jobs
@scheduler.scheduled_job(
    "cron", hour=4, id="nonebot_plugin_deer_pipe_scheduler_fetch_latest_version"
)
async def _():
    """Fetch latest version"""
    global latest_version

    async with ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(
                    "https://pypi.org/pypi/nonebot-plugin-deer-pipe/json"
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    latest_version = data["info"]["version"]
                    return
            except Exception as e:
                logger.warning(f"Error fetching latest version, retry {i}/3: {e}")
                await asyncio.sleep(1)
    logger.error("Fail to fetch latest version")


@scheduler.scheduled_job(
    "cron", day_of_week="mon", hour=4, id="nonebot_plugin_deer_pipe_scheduler_cleanup"
)
async def _():
    await cleanup()
