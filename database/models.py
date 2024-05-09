from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, select
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    groups = relationship('Group', back_populates='category')

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    link = Column(String)
    holder_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(Integer, ForeignKey('category.id'))
    is_private = Column(Boolean)
    is_validated = Column(Boolean)
    category = relationship('Category', back_populates='groups')
    holder = relationship('User', back_populates='groups')


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=False)
    groups = relationship('Group', order_by=Group.id, back_populates='holder')

categories = ["⚽️ Спорт", "📕 Учеба", "🎭 Клубы", "🚨 Объявления", "➖ Другое"]

async def async_main(engine : AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = async_sessionmaker(engine, expire_on_commit=False)

    async with session() as session:
        async with session.begin():
            for cat in categories:
                exists = await session.execute(select(Category).filter_by(name = cat))
                if not exists.scalars().first():
                    new_cat = Category(name = cat)
                    session.add(new_cat)
            
            await session.commit()