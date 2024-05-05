from typing import Protocol
import abc
from dataclasses import dataclass
from returns.result import Result


@dataclass
class Category:
    name: str
    id: str


@dataclass
class Group:
    name: str
    holder_id: str
    is_private: bool
    categories: list[Category]


class DataService(Protocol):

    # TODO: search by name

    @abc.abstractmethod
    def get_categories(self) -> list[Category]:
        ...

    @abc.abstractmethod
    def get_validated_groups(self, category: Category) -> Result[list[Group], Exception]:
        ...

    @abc.abstractmethod
    def get_unvalidated_groups(self, category: Category) -> Result[list[Group], Exception]:
        ...

    @abc.abstractmethod
    def get_user_groups(self, user_id: str) -> Result[list[Group], Exception]:
        # only validated
        ...

    @abc.abstractmethod
    def add_validated_group(self, group: Group) -> Result[str, Exception]:
        ...

    @abc.abstractmethod
    def add_unvalidated_group(self, group: Group) -> Result[str, Exception]:
        ...

    @abc.abstractmethod
    def update_group(self, group: Group) -> Result[str, Exception]:
        ...

    @abc.abstractmethod
    def delete_group(self, group: Group) -> Result[str, Exception]:
        # Delete from validated and unvalidated groups simultaneously
        ...
