import abc
from typing import Protocol, TypeVar

from tests import contexts

IDT = TypeVar("IDT", contravariant=True)
EntityT = TypeVar("EntityT")


class BaseRepositoryException(Exception, metaclass=abc.ABCMeta):
    """Базовое исключение репозитория"""


class EntityNotFoundRepositoryException(BaseRepositoryException):
    """Не удалось найти экземпляр сущности"""


class Repository(Protocol[EntityT, IDT]):
    async def get(self, id_: IDT, *, context: contexts.Context) -> EntityT: ...

    async def save(self, entity: EntityT, *, context: contexts.Context) -> None: ...

    async def delete(self, id_: IDT, *, context: contexts.Context) -> None: ...
