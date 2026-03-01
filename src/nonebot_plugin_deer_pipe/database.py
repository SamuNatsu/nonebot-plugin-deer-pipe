from .constants import DATABASE_URL
from base64 import b64encode, b64decode
from contextlib import asynccontextmanager
from datetime import datetime
from nonebot_plugin_apscheduler import scheduler
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import Field, SQLModel, col, delete, select, update
from uuid import UUID, uuid4
from typing import AsyncGenerator, Sequence


# ORM models
class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    avatar: str | None


class UserDeer(SQLModel, table=True):
    uuid: UUID = Field(primary_key=True, default_factory=uuid4)
    user_id: str = Field(index=True)
    month: int = Field(index=True)
    day: int = Field(index=True)
    count: int = 1


# Initialize database engin
_engine: AsyncEngine = create_async_engine(DATABASE_URL)
_initialized: bool = False


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get asynchronize database session
    """
    # Initialize engine
    global _initialized
    if not _initialized:
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            _initialized = True

    # Create session
    async with AsyncSession(_engine) as session:
        yield session


@scheduler.scheduled_job(
    "cron", day_of_week="mon", hour=4, id="nonebot_plugin_deer_pipe_scheduler_cleanup"
)
async def cleanup() -> None:
    """
    Cleanup expired data
    """
    now: datetime = datetime.now()

    async with get_session() as session:
        # Find expired deer data
        result: Sequence[Row[tuple[str]]] = (
            await session.execute(
                select(UserDeer.user_id)
                .distinct()
                .where(col(UserDeer.month) != now.month)
            )
        ).all()
        set1: set[str] = {i[0] for i in result}  # Users who has expired deer data

        # Cleanup expired deer data
        await session.execute(delete(UserDeer).where(col(UserDeer.month) != now.month))

        # Find active users from deer data
        result: Sequence[Row[tuple[str]]] = (
            await session.execute(select(UserDeer.user_id).distinct())
        ).all()
        set2: set[str] = {i[0] for i in result}

        # Cleanup inactive users
        set3: set[str] = set1 - set2
        await session.execute(delete(User).where(col(User.user_id).in_(set3)))

        # Commit trascation
        await session.commit()


async def get_avatar(user_id: str) -> bytes | None:
    """
    Get avatar by user ID

    :param user_id: User ID
    """
    async with get_session() as session:
        # Fetch avatar
        result: Row[tuple[str | None]] | None = (
            await session.execute(
                select(User.avatar).where(col(User.user_id) == user_id)
            )
        ).first()

        # If user not found
        if result is None:
            return None

        # If avatar not set
        avatar: str | None = result[0]
        if avatar is None:
            return None

        # Return image data
        return b64decode(avatar)


async def update_avatar(user_id: str, avatar: bytes) -> None:
    """
    Update user avatar

    :param user_id: User ID
    :param avatar: Avatar image bytes
    """
    async with get_session() as session:
        # Find user
        result: Row[tuple[User]] | None = (
            await session.execute(select(User).where(User.user_id == user_id))
        ).first()

        # If user not exists
        if result is None:
            session.add(User(user_id=user_id, avatar=b64encode(avatar).decode()))
        else:
            result[0].avatar = b64encode(avatar).decode()
            session.add(result[0])

        # Commit transaction
        await session.commit()


async def get_deer_map(user_id: str, now: datetime) -> dict[int, int]:
    """
    Get user deer map

    :param user_id: User ID
    :param now: Current time
    """
    async with get_session() as session:
        return await _get_deer_map(session, user_id, now)


async def _get_deer_map(
    session: AsyncSession, user_id: str, now: datetime
) -> dict[int, int]:
    result: Sequence[Row[tuple[tuple[int, int]]]] = (
        await session.execute(
            select(UserDeer.day, UserDeer.count)
            .where(col(UserDeer.user_id) == user_id)
            .where(col(UserDeer.month) == now.month)
        )
    ).all()

    return {i[0]: i[1] for i in result}


async def attend(user_id: str, now: datetime) -> dict[int, int]:
    """
    Attend

    :param user_id: User ID
    :param now: Current time
    """
    async with get_session() as session:
        # Get deer map
        deer_map: dict[int, int] = await _get_deer_map(session, user_id, now)

        # Update count
        if now.day in deer_map:
            deer_map[now.day] += 1
            await session.execute(
                update(UserDeer)
                .where(col(UserDeer.user_id) == user_id)
                .where(col(UserDeer.month) == now.month)
                .where(col(UserDeer.day) == now.day)
                .values(count=deer_map[now.day])
            )
        else:
            deer_map[now.day] = 1
            session.add(UserDeer(user_id=user_id, month=now.month, day=now.day))

        # Commit transaction
        await session.commit()

        # Return map
        return deer_map


async def attend_past(
    user_id: str, now: datetime, day: int
) -> tuple[bool, dict[int, int]]:
    """
    Attend past date

    :param user_id: User ID
    :param now: Current time
    :param day: Past day of current month
    """

    async with get_session() as session:
        # Get deer map
        deer_map: dict[int, int] = await _get_deer_map(session, user_id, now)

        # Update count
        if day in deer_map:
            return (False, deer_map)
        else:
            deer_map[day] = 1
            session.add(UserDeer(user_id=user_id, month=now.month, day=day))
            await session.commit()

        # Success
        return (True, deer_map)
