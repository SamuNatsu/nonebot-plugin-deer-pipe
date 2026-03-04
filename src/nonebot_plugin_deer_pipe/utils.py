import asyncio

from .database import User, get_rank, get_user
from aiocache import cached
from aiohttp import ClientSession
from datetime import datetime
from nonebot.log import logger
from nonebot_plugin_uninfo import Member, QryItrface, Session


@cached(ttl=86400)
async def dl_img(url: str):
    """
    Download image by URL with 1h caching

    :param url: Image URL
    """
    async with ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()
            except Exception as e:
                logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                await asyncio.sleep(1)


async def get_user_info(session: Session) -> tuple[str, bytes | None, User]:
    """
    Get user info from session

    :param session: Uninfo session
    :return: tuple[name, avatar, User]
    """
    name: str = (
        (None if session.member is None else session.member.nick)
        or session.user.nick
        or session.user.name
        or session.user.id
    )
    avatar: bytes | None = (
        None if session.user.avatar is None else await dl_img(session.user.avatar)
    )
    user: User = await get_user(session, session.user.id)
    return (name, avatar, user)


async def get_member_info(
    session: Session, interface: QryItrface, user_id: str
) -> tuple[str, bytes | None, User]:
    """
    Get member info from session

    :param session: Uninfo session
    :param interface: Uninfo query interface
    :param user_id: User ID
    :return: tuple[name, avatar, User]
    """
    member: Member | None = await interface.get_member(
        session.scene.type, session.scene.id, user_id
    )
    name: str = (
        (None if member is None else member.nick)
        or (None if member is None else member.user.nick)
        or (None if member is None else member.user.name)
        or user_id
    )
    avatar_url: str | None = None if member is None else member.user.avatar
    avatar: bytes | None = None if avatar_url is None else await dl_img(avatar_url)
    user: User = await get_user(session, user_id)
    return (name, avatar, user)


async def get_member_rank(
    session: Session, interface: QryItrface, now: datetime
) -> list[tuple[str, bytes | None, int]]:
    """
    Get rank with member info

    :param session: Uninfo session
    :param interface: Uninfo query interface
    :param now: Current time
    :return: list[tuple[name, avatar, count]]
    """

    async def get_info(user_id: str) -> tuple[str, bytes | None]:
        member: Member | None = await interface.get_member(
            session.scene.type, session.scene.id, user_id
        )
        name: str = (
            (None if member is None else member.nick)
            or (None if member is None else member.user.nick)
            or (None if member is None else member.user.name)
            or user_id
        )
        avatar_url: str | None = None if member is None else member.user.avatar
        avatar: bytes | None = None if avatar_url is None else await dl_img(avatar_url)
        return (name, avatar)

    rank: list[tuple[str, int]] = await get_rank(session, now)
    return [(*(await get_info(i[0])), i[1]) for i in rank]
