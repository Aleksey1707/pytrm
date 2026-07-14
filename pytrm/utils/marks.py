import sys
from typing import Any, Final, TypeVar, Union, final

if sys.version_info < (3, 13):
    from typing_extensions import TypeIs
else:
    from typing import TypeIs

T = TypeVar("T")


@final
class NotSet:
    __slots__ = ()


def is_set(value: Union[T, NotSet]) -> TypeIs[T]:
    """Не является `NotSet` значением"""
    return not isinstance(value, NotSet)


def is_any_set(*args: Any) -> bool:
    """Является ли какой-нибудь аргумент не `NotSet` значением"""
    return any(filter(is_set, args))


def value_or(value: Union[T, NotSet], fallback: T) -> T:
    """Вернуть значение или запасной вариант, если передан `NotSet`"""
    if is_set(value):
        return value

    return fallback


NOT_SET: Final = NotSet()
