from .constants import DATABASE_URL
from contextlib import asynccontextmanager
from datetime import datetime
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_uninfo import Session
from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import Field, Index, SQLModel, col, delete, func, update
from uuid import UUID, uuid4
from typing import AsyncGenerator, Sequence


# ORM models
class User(SQLModel, table=True):
    __table_args__ = (
        Index("ix_user_id", "adapter", "scope", "scene_id", "user_id", unique=True),
    )

    uuid: UUID = Field(primary_key=True, default_factory=uuid4)
    adapter: str
    scope: str
    scene_id: str
    user_id: str
    can_be_helped: bool = True
    no_deer_until: datetime | None = None


class DeerRecord(SQLModel, table=True):
    __table_args__ = (Index("ix_deerrecord_id", "user_uuid", "month", "day"),)

    uuid: UUID = Field(primary_key=True, default_factory=uuid4)
    user_uuid: UUID = Field(foreign_key="user.uuid")
    month: int = Field(index=True)
    day: int
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
async def _() -> None:
    """
    Cleanup expired data
    """
    async with get_session() as db:
        now: datetime = datetime.now()

        # Find expired deer data
        res1: Sequence[Row[tuple[UUID]]] = (
            await db.execute(
                select(col(DeerRecord.user_uuid))
                .distinct()
                .where(col(DeerRecord.month) != now.month)
            )
        ).all()
        set1: set[UUID] = {i.tuple()[0] for i in res1}

        # Cleanup expired deer data
        await db.execute(delete(DeerRecord).where(col(DeerRecord.month) != now.month))

        # Find active users from deer data
        res2: Sequence[Row[tuple[UUID]]] = (
            await db.execute(select(col(DeerRecord.user_uuid)).distinct())
        ).all()
        set2: set[UUID] = {i.tuple()[0] for i in res2}

        # Cleanup inactive users
        set3: set[UUID] = set1 - set2
        await db.execute(delete(User).where(col(User.uuid).in_(set3)))

        # Commit trascation
        await db.commit()


async def _get_deer_map(db: AsyncSession, now: datetime, user: User) -> dict[int, int]:
    # Fetch records
    result: Sequence[Row[tuple[int, int]]] = (
        await db.execute(
            select(col(DeerRecord.day), col(DeerRecord.count))
            .where(col(DeerRecord.user_uuid) == user.uuid)
            .where(col(DeerRecord.month) == now.month)
        )
    ).all()

    # Return map
    return {i[0]: i[1] for i in result}


async def get_user(session: Session, user_id: str) -> User:
    """
    Get user

    :param session: Uninfo session
    :param user_id: User ID
    """
    async with get_session() as db:
        # Fetch user
        user: User | None = await db.scalar(
            select(User)
            .where(col(User.adapter) == session.adapter)
            .where(col(User.scope) == session.scope)
            .where(col(User.scene_id) == session.scene.id)
            .where(col(User.user_id) == user_id)
        )

        # If user not exists
        if user is None:
            # Insert new user
            user = User(
                adapter=session.adapter,
                scope=session.scope,
                scene_id=session.scene.id,
                user_id=user_id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Return user
        return user


async def update_user(user: User) -> None:
    """
    Update user fields

    :param user: User
    """
    async with get_session() as db:
        db.add(user)
        await db.commit()


async def get_deer_map(now: datetime, user: User) -> dict[int, int]:
    """
    Get user deer map

    :param now: Current time
    :param user: User
    """
    async with get_session() as db:
        return await _get_deer_map(db, now, user)


async def check_in(
    now: datetime, user: User, day: int | None = None
) -> tuple[bool, dict[int, int]]:
    """
    Attend

    :param now: Current time
    :param user: User
    :param day: Past day of current month
    """
    async with get_session() as db:
        # Get deer map
        deer_map: dict[int, int] = await _get_deer_map(db, now, user)

        # If check today && today is checked
        if day is None and now.day in deer_map:
            deer_map[now.day] += 1
            await db.execute(
                update(DeerRecord)
                .where(col(DeerRecord.user_uuid) == user.uuid)
                .where(col(DeerRecord.month) == now.month)
                .where(col(DeerRecord.day) == now.day)
                .values(count=deer_map[now.day])
            )
            await db.commit()
            return (True, deer_map)

        # If check past && past is checked
        elif day is not None and day in deer_map:
            return (False, deer_map)

        # If check today && today is not checked || check past and past is not checked
        else:
            deer_map[day or now.day] = 1
            db.add(DeerRecord(user_uuid=user.uuid, month=now.month, day=day or now.day))
            await db.commit()
            return (True, deer_map)


async def get_rank(session: Session, now: datetime) -> list[tuple[str, int]]:
    async with get_session() as db:
        # Fetch rank of top 5
        res: Sequence[Row[tuple[int, str]]] = (
            await db.execute(
                select(func.sum(DeerRecord.count), col(User.user_id))
                .join(User)
                .where(
                    col(DeerRecord.user_uuid).in_(
                        select(col(User.uuid))
                        .where(col(User.adapter) == session.adapter)
                        .where(col(User.scope) == session.scope)
                        .where(col(User.scene_id) == session.scene.id)
                    )
                )
                .where(col(DeerRecord.month) == now.month)
                .group_by(col(DeerRecord.user_uuid))
                .order_by(func.sum(DeerRecord.count).desc())
                .limit(5)
            )
        ).all()

        # Return rank
        return [(i.tuple()[1], i.tuple()[0]) for i in res]
