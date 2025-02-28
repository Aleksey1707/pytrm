import copy
import sys
from typing import Any, Hashable, MutableMapping, Optional

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


Key = Hashable
Value = Any


class Context:

    __slots__ = ("_data",)

    def __init__(self, data: MutableMapping[Key, Value]) -> None:
        self._data = data

    @classmethod
    def empty(cls) -> Self:
        return cls(dict())

    def find(self, key: Key) -> Optional[Value]:
        """Получить значение по ключу"""
        return self._data.get(key)

    def set(self, key: Key, value: Value) -> Self:
        """Задать значение по ключу"""
        data = copy.copy(self._data)
        data[key] = value
        return self.__class__(data)

    def remove(self, key: Key) -> Self:
        """Удалить значение по ключу"""
        data = copy.copy(self._data)
        del data[key]
        return self.__class__(data)
