from app.database.models import async_session
from app.database.models import User, Info
from sqlalchemy import select, update, insert


async def set_user(tg_id, username):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id==tg_id))
        if not user:
            session.add(User(tg_id=tg_id, tg_name='@'+username, attempts=3))
            await session.commit()
        else:
            user.tg_name = '@' + username
            session.add(user)
            await session.commit()

async def set_user_state(tg_id, state):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            stmt = update(User).where(User.tg_id == tg_id).values(state=state)
            await session.execute(stmt)
            await session.commit()
        else:
            session.add(User(tg_id=tg_id, state=state))
            await session.commit()

async def get_user_state(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.state if user else None

async def update_user_state(user_id: int, new_state: str):
    async with async_session() as session:
        user = await session.execute(select(User).filter_by(id=user_id))
        user = user.scalar_one_or_none()
        if user:
            user.state = new_state
            await session.commit()

async def search_by_number(number: str):
    async with async_session() as session:
        users = await session.scalars(select(Info).where(Info.number == number))
        return users.all()

async def search_by_fio(partial_fio: str):
    async with async_session() as session:
        users = await session.scalars(select(Info).where(Info.fio.like(f"%{partial_fio}%")))
        return users.all()

async def add_user_info(data: dict):
    async with async_session() as session:
        stmt = insert(Info).values(
            fio=data['fio'],
            number=data['number'],
            email=data['email'],
            adres=data['adres'],
            dr=data['dr'],
            info=data['info']
        )
        await session.execute(stmt)
        await session.commit()

async def ban_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return False
        user.is_banned = 1
        await session.commit()
        return True

async def unban_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return False
        if user.is_banned == 0:
            return None
        user.is_banned = 0
        await session.commit()
        return True

async def banned_user(tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.is_banned == 1 if user else False


async def get_unbanned_users():
    async with async_session() as session:
        result = await session.execute(
            select(User.tg_id, User.tg_name)
            .where(User.is_banned == 0))
        return result.all()

async def get_banned_users():
    async with async_session() as session:
        result = await session.execute(
            select(User.tg_id, User.tg_name)
            .where(User.is_banned == 1))
        return result.all()

