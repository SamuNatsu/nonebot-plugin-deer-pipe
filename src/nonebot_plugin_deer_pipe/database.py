from .contants import DATABASE_URL

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Sequence


# Model
class User(SQLModel, table=True):
  user_id: str = Field(primary_key=True)
  year: int
  month: int
  mask: str    = "0"

# Async engine
engin: AsyncEngine = create_async_engine(DATABASE_URL)
initialized: bool = False

# Attendance
def get_seq(mask: str) -> list[int]:
  return list(
    map(
      lambda x: x[0] + 1,
      filter(
        lambda x: x[1] == '1',
        enumerate(mask)
      )
    )
  )

async def attend(now: datetime, user_id: str) -> tuple[bool, Sequence[int]]:
  if not initialized:
    async with engin.begin() as conn:
      await conn.run_sync(SQLModel.metadata.create_all)
  
  async with AsyncSession(engin) as session:
    user: User | None = (
      await session.exec(select(User).where(User.user_id == user_id))
    ).one_or_none()

    if user == None or user.year != now.year or user.month != now.month:
      user = User(user_id=user_id, year=now.year, month=now.month)
    
    mask: int = int(user.mask)
    if (mask >> (now.day - 1)) & 1 == 1:
      return (False, get_seq(user.mask))
    else:
      mask |= (1 << (now.day - 1))
      user.mask = str(mask)

      session.add(user)
      await session.commit()

      return (True, get_seq(str(mask)))
