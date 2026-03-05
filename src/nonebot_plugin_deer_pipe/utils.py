from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from nonebot_plugin_uninfo import QryItrface, Session


import asyncio

from .database import get_rank, get_user
from aiohttp import ClientSession
from aiocache import cached as real_cached
from nonebot.log import logger


# Fix type hint
if TYPE_CHECKING:

    def cached(*args, **kwargs):
        def wrapper(func):
            return func

        return wrapper
else:
    cached = real_cached


@cached(ttl=86400)
async def dl_img(url: str):
    """
    Download image by URL with 1day caching

    :param url: Image URL
    """
    async with ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()
            except Exception as e:
                logger.warning(f"Error downloading '{url}', retry {i}/3: {e}")
                await asyncio.sleep(1)


async def get_user_info(session: Session):
    """
    Get user info from session

    :param session: Uninfo session
    :return: tuple[name, avatar, User]
    """
    name = (
        (None if session.member is None else session.member.nick)
        or session.user.nick
        or session.user.name
        or session.user.id
    )
    avatar = None if session.user.avatar is None else await dl_img(session.user.avatar)
    user = await get_user(session, session.user.id)
    return (name, avatar, user)


async def get_member_info(session: Session, interface: QryItrface, user_id: str):
    """
    Get member info from session

    :param session: Uninfo session
    :param interface: Uninfo query interface
    :param user_id: User ID
    :return: tuple[name, avatar, User]
    """
    member = await interface.get_member(session.scene.type, session.scene.id, user_id)
    name = (
        (None if member is None else member.nick)
        or (None if member is None else member.user.nick)
        or (None if member is None else member.user.name)
        or user_id
    )
    avatar_url = None if member is None else member.user.avatar
    avatar = None if avatar_url is None else await dl_img(avatar_url)
    user = await get_user(session, user_id)
    return (name, avatar, user)


async def get_member_rank(session: Session, interface: QryItrface, now: datetime):
    """
    Get rank with member info

    :param session: Uninfo session
    :param interface: Uninfo query interface
    :param now: Current time
    :return: list[tuple[name, avatar, count]]
    """

    async def get_info(user_id: str):
        member = await interface.get_member(
            session.scene.type, session.scene.id, user_id
        )
        name = (
            (None if member is None else member.nick)
            or (None if member is None else member.user.nick)
            or (None if member is None else member.user.name)
            or user_id
        )
        avatar_url = None if member is None else member.user.avatar
        avatar = None if avatar_url is None else await dl_img(avatar_url)
        return (name, avatar)

    rank = await get_rank(session, now)
    return [(*(await get_info(i[0])), i[1]) for i in rank]
