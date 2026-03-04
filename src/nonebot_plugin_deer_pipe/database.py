from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot_plugin_uninfo import Session


from .constants import DATABASE_URL
from contextlib import asynccontextmanager
from datetime import datetime
from nonebot_plugin_apscheduler import scheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Field, Index, SQLModel, col, delete, func, update
from uuid import UUID, uuid4


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
_engine = create_async_engine(DATABASE_URL)
_initialized = False


@asynccontextmanager
async def _get_session():
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
async def _():
    """
    Cleanup expired data
    """
    async with _get_session() as db:
        now = datetime.now()

        # Find expired deer data
        res1 = (
            await db.execute(
                select(col(DeerRecord.user_uuid))
                .distinct()
                .where(col(DeerRecord.month) != now.month)
            )
        ).all()
        set1 = {i.tuple()[0] for i in res1}

        # Cleanup expired deer data
        await db.execute(delete(DeerRecord).where(col(DeerRecord.month) != now.month))

        # Find active users from deer data
        res2 = (await db.execute(select(col(DeerRecord.user_uuid)).distinct())).all()
        set2 = {i.tuple()[0] for i in res2}

        # Cleanup inactive users
        set3 = set1 - set2
        await db.execute(delete(User).where(col(User.uuid).in_(set3)))

        # Commit trascation
        await db.commit()


async def _get_records(db: AsyncSession, now: datetime, user: User):
    # Fetch records
    result = (
        await db.execute(
            select(col(DeerRecord.day), col(DeerRecord.count))
            .where(col(DeerRecord.user_uuid) == user.uuid)
            .where(col(DeerRecord.month) == now.month)
        )
    ).all()

    # Return map
    return {i.tuple()[0]: i.tuple()[1] for i in result}


async def get_user(session: Session, user_id: str):
    """
    Get user

    :param session: Uninfo session
    :param user_id: User ID
    :return: User
    """
    async with _get_session() as db:
        # Fetch user
        user = await db.scalar(
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


async def update_user(user: User):
    """
    Update user fields

    :param user: User
    """
    async with _get_session() as db:
        db.add(user)
        await db.commit()


async def get_records(now: datetime, user: User):
    """
    Get user deer record map

    :param now: Current time
    :param user: User
    :return: dict[day of month, count]
    """
    async with _get_session() as db:
        return await _get_records(db, now, user)


async def check_in(now: datetime, user: User, day: int | None = None):
    """
    Check in

    :param now: Current time
    :param user: User
    :param day: Past day of current month
    :return: tuple[is success, dict[day of month, count]]
    """
    async with _get_session() as db:
        # Get deer records
        records = await _get_records(db, now, user)

        # If check today && today is checked
        if day is None and now.day in records:
            records[now.day] += 1
            await db.execute(
                update(DeerRecord)
                .where(col(DeerRecord.user_uuid) == user.uuid)
                .where(col(DeerRecord.month) == now.month)
                .where(col(DeerRecord.day) == now.day)
                .values(count=records[now.day])
            )
            await db.commit()
            return (True, records)

        # If check past && past is checked
        elif day is not None and day in records:
            return (False, records)

        # If check today && today is not checked || check past and past is not checked
        else:
            records[day or now.day] = 1
            db.add(DeerRecord(user_uuid=user.uuid, month=now.month, day=day or now.day))
            await db.commit()
            return (True, records)


async def get_rank(session: Session, now: datetime):
    """
    Get rank

    :param session: Uninfo session
    :param now: Current time
    :return: list[tuple[user ID, count]]
    """
    async with _get_session() as db:
        # Fetch rank of top 5
        res = (
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
