from typing import Any, Final, TypeGuard, TypeVar

T = TypeVar("T")


class NotSetType:
    __slots__ = ()


def is_any_set(*args: Any) -> bool:
    return any(filter(lambda item: not isinstance(item, NotSetType), args))


def is_notset(value: Any | NotSetType) -> TypeGuard[NotSetType]:
    return isinstance(value, NotSetType)


def is_set(value: T | NotSetType) -> TypeGuard[T]:
    return not is_notset(value)


NOT_SET: Final = NotSetType()
