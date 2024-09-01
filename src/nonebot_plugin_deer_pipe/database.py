import uuid

from .constants import DATABASE_URL

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Field, SQLModel, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Sequence


# Model
class User(SQLModel, table=True):
  id: str = Field(primary_key=True)
  year: int
  month: int

class UserDeer(SQLModel, table=True):
  id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  user_id: str  = Field(index=True)
  day: int
  count: int    = 0

# Async engine
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
initialized: bool = False

# Initialize engine
async def init_engine() -> None:
  global initialized
  if not initialized:
    initialized = True
    async with engine.begin() as conn:
      await conn.run_sync(SQLModel.metadata.create_all)

# Fetch user deer
async def fetch_user_deer(
  session: AsyncSession,
  now: datetime,
  user_id: str
) -> Sequence[UserDeer]:
  user: User | None = (
    await session.exec(select(User).where(User.id == user_id))
  ).one_or_none()

  user_deer: Sequence[UserDeer] = []
  if user == None:
    user = User(id=user_id, year=now.year, month=now.month)
    session.add(user)
  elif user.year != now.year or user.month != now.month:
    await session.exec(delete(UserDeer).where(UserDeer.user_id == user_id))
    user.year = now.year
    user.month = now.month
    session.add(user)
  else:
    user_deer = (
      await session.exec(select(UserDeer).where(UserDeer.user_id == user_id))
    ).all()

  return user_deer

# Attendance
async def attend(now: datetime, user_id: str) -> dict[int, int]:
  await init_engine()

  async with AsyncSession(engine) as session:
    user_deer: Sequence[UserDeer] = await fetch_user_deer(
      session,
      now,
      user_id
    )
    deer_map: dict[int, int] = dict([(i.day, i.count) for i in user_deer])

    if now.day in deer_map:
      deer_map[now.day] += 1
      current: UserDeer = next(filter(lambda x: x.day == now.day, user_deer))
      current.count += 1
      session.add(current)
    else:
      deer_map[now.day] = 1
      session.add(UserDeer(user_id=user_id, day=now.day, count=1))

    await session.commit()
    return deer_map

async def reattend(
  now: datetime,
  day: int,
  user_id: str
) -> tuple[bool, dict[int, int]]:
  await init_engine()

  async with AsyncSession(engine) as session:
    user_deer: Sequence[UserDeer] = await fetch_user_deer(
      session,
      now,
      user_id
    )
    deer_map: dict[int, int] = dict([(i.day, i.count) for i in user_deer])
    ok: bool = False

    if day not in deer_map:
      deer_map[day] = 1
      session.add(UserDeer(user_id=user_id, day=day, count=1))
      ok = True

    await session.commit()
    return (ok, deer_map)
