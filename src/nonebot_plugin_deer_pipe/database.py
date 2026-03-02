from .constants import DATABASE_URL
from .utils import NotSet
from contextlib import asynccontextmanager
from datetime import datetime
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_uninfo import Session
from sqlalchemy import Row, select, tuple_
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import Field, Index, SQLModel, col, delete, func, update
from uuid import UUID, uuid4
from typing import AsyncGenerator, Sequence


# ORM models
class User(SQLModel, table=True):
    adapter: str = Field(primary_key=True)
    scope: str = Field(primary_key=True)
    id: str = Field(primary_key=True)
    can_be_helped: bool = True
    no_deer_until: datetime | None = None


class UserGroup(SQLModel, table=True):
    adapter: str = Field(primary_key=True)
    scope: str = Field(primary_key=True)
    user_id: str = Field(primary_key=True)
    group_id: str = Field(primary_key=True)


class UserDeer(SQLModel, table=True):
    __table_args__ = (
        Index("ix_userdeer_adapter_scope_user_id", "adapter", "scope", "user_id"),
    )

    uuid: UUID = Field(primary_key=True, default_factory=uuid4)
    adapter: str
    scope: str
    user_id: str
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
    async with get_session() as db:
        now: datetime = datetime.now()

        # Find expired deer data
        res1: Sequence[Row[tuple[str, str, str]]] = (
            await db.execute(
                select(
                    col(UserDeer.adapter), col(UserDeer.scope), col(UserDeer.user_id)
                )
                .distinct()
                .where(col(UserDeer.month) != now.month)
            )
        ).all()
        set1: set[tuple[str, str, str]] = {
            i.tuple() for i in res1
        }  # Users who has expired deer data

        # Cleanup expired deer data
        await db.execute(delete(UserDeer).where(col(UserDeer.month) != now.month))

        # Find active users from deer data
        res2: Sequence[Row[tuple[str, str, str]]] = (
            await db.execute(
                select(
                    col(UserDeer.adapter),
                    col(UserDeer.scope),
                    col(UserDeer.user_id),
                ).distinct()
            )
        ).all()
        set2: set[tuple[str, str, str]] = {i.tuple() for i in res2}

        # Cleanup inactive users
        set3: set[tuple[str, str, str]] = set1 - set2
        await db.execute(
            delete(User).where(
                tuple_(col(User.adapter), col(User.scope), col(User.id)).in_(set3)
            )
        )

        # Commit trascation
        await db.commit()


async def _get_deer_map(
    session: Session, db: AsyncSession, now: datetime, user_id: str
) -> dict[int, int]:
    # Fetch records
    result: Sequence[Row[tuple[int, int]]] = (
        await db.execute(
            select(col(UserDeer.day), col(UserDeer.count))
            .where(col(UserDeer.adapter) == session.adapter)
            .where(col(UserDeer.scope) == session.scope)
            .where(col(UserDeer.user_id) == user_id)
            .where(col(UserDeer.month) == now.month)
        )
    ).all()

    # Return map
    return {i[0]: i[1] for i in result}


async def get_deer_map(session: Session, now: datetime, user_id: str) -> dict[int, int]:
    """
    Get user deer map

    :param user_id: User ID
    :param now: Current time
    """
    async with get_session() as db:
        return await _get_deer_map(session, db, now, user_id)


async def check_in(
    session: Session, now: datetime, user_id: str, day: int | None = None
) -> tuple[bool, dict[int, int]]:
    """
    Attend

    :param session: Uninfo session
    :param user_id: User ID
    :param now: Current time
    :param day: Past day of current month
    """
    async with get_session() as db:
        # Get deer map
        deer_map: dict[int, int] = await _get_deer_map(session, db, now, user_id)

        # If check today && today is checked
        if day is None and now.day in deer_map:
            deer_map[now.day] += 1
            await db.execute(
                update(UserDeer)
                .where(col(UserDeer.adapter) == session.adapter)
                .where(col(UserDeer.scope) == session.scope)
                .where(col(UserDeer.user_id) == user_id)
                .where(col(UserDeer.month) == now.month)
                .where(col(UserDeer.day) == now.day)
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
            db.add(
                UserDeer(
                    adapter=session.adapter,
                    scope=session.scope,
                    user_id=user_id,
                    month=now.month,
                    day=day or now.day,
                )
            )
            await db.commit()
            return (True, deer_map)


async def update_user(
    session: Session,
    user_id: str,
    *,
    can_be_helped: bool | NotSet = NotSet.NOT_SET,
    no_deer_until: datetime | None | NotSet = NotSet.NOT_SET,
):
    """
    Update user fields

    :param session: Uninfo session
    :param user_id: User ID
    """
    async with get_session() as db:
        # Fetch user
        user: User = (
            (
                await db.execute(
                    select(User)
                    .where(col(User.adapter) == session.adapter)
                    .where(col(User.scope) == session.scope)
                    .where(col(User.id) == user_id)
                )
            )
            .one()
            .tuple()[0]
        )

        # Update fields
        if not isinstance(can_be_helped, NotSet):
            user.can_be_helped = can_be_helped
        if not isinstance(no_deer_until, NotSet):
            user.no_deer_until = no_deer_until
        db.add(user)

        # Update user
        await db.commit()


async def get_rank(session: Session, now: datetime) -> list[tuple[str, int]]:
    async with get_session() as db:
        # Fetch rank of top 5
        res: Sequence[Row[tuple[str, int]]] = (
            await db.execute(
                select(col(UserDeer.user_id), func.sum(UserDeer.count))
                .where(col(UserDeer.adapter) == session.adapter)
                .where(col(UserDeer.scope) == session.scope)
                .where(
                    col(UserDeer.user_id).in_(
                        select(col(UserGroup.user_id))
                        .where(col(UserGroup.adapter) == session.adapter)
                        .where(col(UserGroup.scope) == session.scope)
                        .where(col(UserGroup.group_id) == session.scene.id)
                    )
                )
                .where(col(UserDeer.month) == now.month)
                .group_by(UserDeer.user_id)
                .order_by(func.sum(UserDeer.count).desc())
                .limit(5)
            )
        ).all()

        # Return rank
        return [i.tuple() for i in res]
