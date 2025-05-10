from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_name: Mapped[str] = mapped_column(String(120), nullable=True)
    tg_id = mapped_column(BigInteger)
    state: Mapped[str] = mapped_column(String, nullable=True)
    is_banned: Mapped[int] = mapped_column(default=0)
    attempts: Mapped[int] = mapped_column(default=3)

class Info(Base):
    __tablename__ = 'info'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    fio: Mapped[str] = mapped_column(String(70))
    number: Mapped[int] = mapped_column()
    email: Mapped[str] = mapped_column(String(100))
    adres: Mapped[str] = mapped_column(String(150))
    dr: Mapped[str] = mapped_column(String(10))
    info: Mapped[str] = mapped_column(String(300))

async def async_mane():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

