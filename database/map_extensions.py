from Interface import Category as CategoryView, User as UserView, Group as GroupView
from .models import Category, User, Group


def category_map(cat: Category):
    return CategoryView(
        id=cat.id,
        name=cat.name
    )


def group_map(gr: Group, cat: CategoryView, holder: UserView):
    return GroupView(
        name=gr.name,
        link=gr.link,
        is_private=gr.is_private,
        holder=holder,
        category=cat
    )
