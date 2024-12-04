from .constants import DATABASE_URL

from base64 import b64encode, b64decode
from contextlib import asynccontextmanager
from datetime import datetime
from nonebot_plugin_apscheduler import scheduler
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import Field, SQLModel, delete, select, update
from uuid import UUID, uuid4
from typing import AsyncGenerator, Sequence


# ORM models
class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    avatar: str | None


class UserDeer(SQLModel, table=True):
    uuid: UUID = Field(primary_key=True, default_factory=uuid4)
    user_id: str = Field(index=True)
    month: int
    day: int
    count: int = 1


# Initialize database engin
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
initialized: bool = False


# Session context decorator
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    # Initialize engine
    global initialized
    if not initialized:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async with AsyncSession(engine) as session:
        yield session


# Cleanup expired data
@scheduler.scheduled_job(
    "cron", day_of_week="mon", hour=4, id="nonebot_plugin_deer_pipe_scheduler_cleanup"
)
async def cleanup() -> None:
    now: datetime = datetime.now()

    async with get_session() as session:
        result: Sequence[Row[tuple[str]]] = (
            await session.execute(
                select(UserDeer.user_id).distinct().where(UserDeer.month != now.month)
            )
        ).all()
        set1: set[str] = {i[0] for i in result}

        await session.execute(delete(UserDeer).where(UserDeer.month != now.month))

        result: Sequence[Row[tuple[str]]] = (
            await session.execute(select(UserDeer.user_id).distinct())
        ).all()
        set2: set[str] = {i[0] for i in result}

        set3: set[str] = set1 - set2
        for user_id in set3:
            await session.execute(delete(User).where(User.user_id == user_id))

        await session.commit()


# Get avatar
async def get_avatar(user_id: str) -> bytes | None:
    async with get_session() as session:
        result: Row[tuple[str | None]] | None = (
            await session.execute(select(User.avatar).where(User.user_id == user_id))
        ).first()

        if result is None:
            return None

        avatar: str | None = result[0]
        if avatar is None:
            return None

        return b64decode(avatar)


# Update avatar
async def update_avatar(user_id: str, avatar: bytes) -> None:
    async with get_session() as session:
        result: Row[tuple[User]] | None = (
            await session.execute(select(User).where(User.user_id == user_id))
        ).first()

        if result is None:
            session.add(User(user_id=user_id, avatar=b64encode(avatar).decode()))
        else:
            result[0].avatar = b64encode(avatar).decode()
            session.add(result[0])
        await session.commit()


# Get deer map
async def get_deer_map(user_id: str, now: datetime) -> dict[int, int]:
    async with get_session() as session:
        return await _get_deer_map(session, user_id, now)


async def _get_deer_map(
    session: AsyncSession, user_id: str, now: datetime
) -> dict[int, int]:
    result: Sequence[Row[tuple[int, int]]] = (
        await session.execute(
            select(UserDeer.day, UserDeer.count).where(
                UserDeer.user_id == user_id, UserDeer.month == now.month
            )
        )
    ).all()

    return {i[0]: i[1] for i in result}


# Attend
async def attend(user_id: str, now: datetime) -> dict[int, int]:
    async with get_session() as session:
        # Get deer map
        deer_map: dict[int, int] = await _get_deer_map(session, user_id, now)

        # Update count
        if now.day in deer_map:
            deer_map[now.day] += 1
            await session.execute(
                update(UserDeer)
                .where(
                    UserDeer.user_id == user_id,
                    UserDeer.month == now.month,
                    UserDeer.day == now.day,
                )
                .values(count=deer_map[now.day])
            )
        else:
            deer_map[now.day] = 1
            session.add(UserDeer(user_id=user_id, month=now.month, day=now.day))
        await session.commit()

        return deer_map


# Attend past
async def attend_past(
    user_id: str, now: datetime, day: int
) -> tuple[bool, dict[int, int]]:
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

        return (True, deer_map)
