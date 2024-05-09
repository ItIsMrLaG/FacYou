from returns.result import Result, Success, Failure
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from Interface import Category as CategoryView, User as UserView, Group as GroupView
from .models import Category, User, Group
from .map_extensions import *

class DatabaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_categories(self):
        session = self.session
        res = await session.execute(select(Category))
        categories = res.scalars().all()
        return [category_map(cat) for cat in categories]
    
    async def get_category(self, cat_id) -> Result[CategoryView, str]:
        session = self.session
        res = await session.execute(select(Category).filter_by(id=cat_id))
        cat = res.scalars().first()
        if not cat:
            Failure("Похоже, что такой категории еще нет.")

        return Success(category_map(cat))
    
    async def get_group_caterogy(self, group_id) -> CategoryView:
        session = self.session
        group = await session.get(Group, group_id)
        category = await session.get(Category, group.category_id)
        return category_map(category)
    
    async def add_category(self, category_name):
        session = self.session
        session.add(Category(name = category_name))
        await session.commit()
    
    async def get_user_groups(self, user_id: int) -> Result[list[list[Group]], str]:
        session = self.session
        res = await session.execute(select(User).filter_by(id = user_id))
        user = res.scalars().first()

        if not user:
            return Failure("У вас еще нет групп")
        
        groups = (await session.execute(select(Group).filter_by(holder_id = user.id))).scalars().all()
        validated_groups = []
        unvalidated_groups = []
        for g in groups:
            if g.is_validated:
                category = await self.get_category(g.category_id)
                if isinstance(category, Success):
                    validated_groups.append(group_map(g, category.unwrap()))
            elif not g.is_validated:
                category = await self.get_category(g.category_id)
                if isinstance(category, Success):
                    unvalidated_groups.append(group_map(g, category.unwrap()))

        return Success([validated_groups, unvalidated_groups])
    
    async def get_validated_groups_by_category(self, cat_id) -> list[GroupView]:
        session = self.session
        result = await session.execute(select(Group).filter_by(category_id = cat_id))
        groups = result.scalars().all()

        groups_view = []
        for g in groups:
            cat = await self.get_category(g.category_id)
            if isinstance(cat, Success):
                groups_view.append(group_map(g, cat.unwrap()))

        return groups_view
    
    async def add_unvalidated_group(self, group_model : GroupView) -> Result[bool, str]:
        session = self.session
        result = await session.execute(select(User).filter_by(id=group_model.holder.id))
        user = result.scalars().first()

        if not user:
            user = User(id = group_model.holder.id,)
            session.add(user)
            await session.commit()

        res = await session.execute(select(Category).filter_by(name=group_model.category.name))
        category = res.scalars().first()
        if not category:
            Failure("Указанной категории не существует")

        group = Group(
            name = group_model.name,
            link = group_model.link,
            holder_id = group_model.holder.id,
            category_id = category.id,
            is_private = group_model.is_private,
            is_validated = False)
        session.add(group)

        await session.commit()
        Success(True)

    async def delete_group(self, group_name: str, user_id: int) -> Result[str, str]:
        session = self.session
        result = await session.execute(select(Group).filter_by(name=group_name))
        group = result.scalars().first()
        if group and group.holder_id == user_id:
            await session.delete(group)
            await session.commit()
            return Success("Группа успешно удалена")
        elif group:
            return Failure("Вы не обладаете правами для удаления данной группы")
        else:
            return Failure("Данной группы не существует")
        
            
         