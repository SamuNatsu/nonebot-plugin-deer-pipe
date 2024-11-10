# database.py

import uuid
from base64 import b64encode, b64decode
from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy import delete, select
from sqlmodel import Field, SQLModel

from .constants import DATABASE_URL

# ORM Models

class User(SQLModel, table=True):
    """
    用户表模型
    """
    id: str = Field(primary_key=True, description="用户唯一标识符")
    group_id: Optional[str] = Field(default=None, index=True, description="用户所在群组ID")
    avatar_data: Optional[str] = Field(default=None, description="Base64编码的用户头像数据")

    @property
    def avatar(self) -> Optional[bytes]:
        """将Base64字符串解码为字节"""
        if self.avatar_data:
            return b64decode(self.avatar_data)
        return None

    @avatar.setter
    def avatar(self, value: Optional[bytes]):
        """将字节编码为Base64字符串"""
        if value:
            self.avatar_data = b64encode(value).decode()
        else:
            self.avatar_data = None


class UserDeer(SQLModel, table=True):
    """
    用户签到记录表模型
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, description="签到记录唯一标识符")
    user_id: str = Field(index=True, description="关联的用户ID")
    year: int = Field(description="签到年份")
    month: int = Field(description="签到月份")
    day: int = Field(description="签到日期（天）")
    count: int = Field(default=0, description="签到次数")


# 异步数据库引擎初始化
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
initialized: bool = False


async def init_engine() -> None:
    """
    初始化数据库引擎，创建所有表
    """
    global initialized
    if not initialized:
        initialized = True
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


async def get_user_avatar(user_id: str) -> Optional[bytes]:
    """
    获取用户头像。如果数据库中已有头像数据，则返回；否则，从外部获取并存储。
    """
    await init_engine()
    
    async with AsyncSession(engine) as session:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user and user.avatar:
            return user.avatar
        else:
            return None


async def add_user_avatar(user_id: str, avatar: bytes) -> None:
    """
    添加用户头像
    """
    await init_engine()
    
    async with AsyncSession(engine) as session:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.avatar = avatar
            session.add(user)
            await session.commit()


async def update_user_info(
    user_id: str, 
    group_id: Optional[str] = None, 
    avatar: Optional[bytes] = None
) -> None:
    """
    更新用户信息，包括群组ID和头像
    """
    await init_engine()
    
    async with AsyncSession(engine) as session:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.first()
        
        if user:
            if group_id is not None:
                user.group_id = group_id
            if avatar is not None:
                user.avatar = avatar  # 使用property setter
            session.add(user)
            await session.commit()


async def fetch_user_deer(
    session: AsyncSession,
    now: datetime,
    user_id: str,
    group_id: Optional[str] = None,
    avatar: Optional[bytes] = None
) -> Tuple[User, Sequence[UserDeer]]:
    """
    获取用户的签到数据，如果用户不存在则创建新用户
    """
    result = await session.execute(
        select(User, UserDeer)
        .join(UserDeer, User.id == UserDeer.user_id, isouter=True)
        .where(User.id == user_id)
        .where(UserDeer.year == now.year, UserDeer.month == now.month)
    )
    user_data = result.all()

    user: Optional[User] = None
    user_deer: list[UserDeer] = []

    for u, ud in user_data:
        if user is None:
            user = u
        if ud is not None:
            user_deer.append(ud)

    if user is None:
        # 创建新用户
        user = User(
            id=user_id, 
            group_id=group_id,
            avatar_data=b64encode(avatar).decode() if avatar else None
        )
        session.add(user)


    return user, user_deer


async def attend(now: datetime, user_id: str) -> dict[int, int]:
    """
    用户签到，增加当天的签到次数
    """
    await init_engine()

    async with AsyncSession(engine) as session:
        user, user_deer = await fetch_user_deer(session, now, user_id)
        deer_map: dict[int, int] = {i.day: i.count for i in user_deer}

        if now.day in deer_map:
            deer_map[now.day] += 1
            current: UserDeer = next(filter(lambda x: x.day == now.day, user_deer))
            current.count += 1
            session.add(current)
        else:
            deer_map[now.day] = 1
            new_deer = UserDeer(
                user_id=user_id,
                year=now.year,
                month=now.month,
                day=now.day,
                count=1
            )
            session.add(new_deer)

        await session.commit()
        return deer_map


async def reattend(
    now: datetime,
    day: int,
    user_id: str
) -> Tuple[bool, dict[int, int]]:
    """
    用户补签，增加指定日期的签到次数
    """
    await init_engine()

    async with AsyncSession(engine) as session:
        query = select(UserDeer).where(
            UserDeer.user_id == user_id,
            UserDeer.year == now.year,
            UserDeer.month == now.month,
            UserDeer.day == day
        )
        result = await session.execute(query)
        deer = result.scalar_one_or_none()
        ok: bool = False

        if deer is None:
            new_deer = UserDeer(
                user_id=user_id,
                year=now.year,
                month=now.month,
                day=day,
                count=1
            )
            session.add(new_deer)
            ok = True
        else:
            deer.count += 1
            session.add(deer)

        result = await session.execute(
            select(UserDeer).where(
                UserDeer.user_id == user_id,
                UserDeer.year == now.year,
                UserDeer.month == now.month
            )
        )
        deer_map: dict[int, int] = {d.day: d.count for d in result.scalars().all()}

        await session.commit()
        return ok, deer_map


async def leaderboard(month: Optional[int] = None) -> Sequence[Tuple[str, Optional[str], int]]:
    """
    获取排行榜数据，可以按月筛选，返回用户ID、头像数据（base64编码）和签到次数
    Returns a sequence of tuples containing (user_id, avatar_data_base64, count)
    """
    await init_engine()

    async with AsyncSession(engine) as session:
        from sqlalchemy import func

        query = select(User.id, User.avatar_data, func.sum(UserDeer.count).label('total_count'))\
                .join(UserDeer, User.id == UserDeer.user_id)\
                .group_by(User.id, User.avatar_data)
        
        if month is not None:
            # 按月份筛选并指定年份为当前年份
            now = datetime.now()
            query = query.where(UserDeer.month == month, UserDeer.year == now.year)
            
        result = await session.execute(query)
        user_deer_data = result.all()

        leaderboard_data: dict[str, Tuple[Optional[str], int]] = {}
        for user_id, avatar_data, count in user_deer_data:
            if user_id in leaderboard_data:
                current_avatar, current_count = leaderboard_data[user_id]
                leaderboard_data[user_id] = (current_avatar, current_count + count)
            else:
                leaderboard_data[user_id] = (avatar_data, count)

        # 按签到次数排序
        sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1][1], reverse=True)
        return [(user_id, data[0], data[1]) for user_id, data in sorted_leaderboard]
