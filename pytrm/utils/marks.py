import sys
from typing import Any, Final, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import TypeGuard
else:
    from typing import TypeGuard

T = TypeVar("T")


class NotSetType:
    __slots__ = ()


def is_any_set(*args: Any) -> bool:
    return any(filter(lambda item: not isinstance(item, NotSetType), args))


def is_notset(value: Union[Any, NotSetType]) -> TypeGuard[NotSetType]:
    return isinstance(value, NotSetType)


def is_set(value: Union[T, NotSetType]) -> TypeGuard[T]:
    return not is_notset(value)


NOT_SET: Final = NotSetType()
