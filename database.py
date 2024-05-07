from sqlalchemy import create_engine, Column, Integer, String, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from interface import Category, Group

Base = declarative_base()

group_category_table = Table('group_category', Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('category.id'), primary_key=True)
)

user_group_table = Table('user_category', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), primary_key=True)
)

class CategoryTable(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    #Is_preset = Column(Boolean) непонятно зачем это нужно пока что
    groups = relationship('GroupTable',secondary=group_category_table, back_populates='categories')

class GroupTable(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    link = Column(String)
    holder_id = Column(Integer, ForeignKey='user.id')
    is_private = Column(Boolean)
    categories = relationship('CategoryTable', secondary=group_category_table, back_populates='groups')
    holder = relationship('UserTable', back_populates='user')


class UserTable(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    groups = relationship('GroupTable', order_by=Group.id, back_populates='holder')


engine = create_engine('sqlite:///FacYou_bot.db')
Base.metadata.create_all(engine)

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

    def get_categories(self):
        session = self.Session()
        categories = session.query(CategoryTable).all()
        session.close()

        return [Category(id=cat.id, name=cat.name) for cat in categories]
    
    def get_user_groups(self, user_id: int):
        session = self.Session()
        user = session.query(UserTable).filter_by(id=user_id).first()
        if not user:
            session.close()
            return []
        
        groups = user.groups
        group_view_models = [Group(
            name=g.name, 
            link = g.link,
            holder_id=g.holder_id,
            is_private=g.is_private,
            categories=g.categories) for g in groups]
        session.close()

        return group_view_models
    
    def get_group_caterogies(self, group_id):
        session = self.Session()
        categories = session.query(GroupTable).filter_by(id=group_id).first().categories
        session.close()

        return categories
    
    def add_validated_group(self, group_model : Group):
        session = self.Session()

        group = GroupTable(
            name = group_model.name,
            link = group_model.link,
            is_privavte = group_model.is_private,
        )
        session.add(group)

        for cat_model in group_model.categories:
            category = session.query(Category).filter_by(name = cat_model.name).first()
            if not category:
                category = CategoryTable(name = cat_model.name)
                session.add(category)
            
            group.categories.append(category)

        session.commit()
        


        # еще пользователя добавить
        
    
