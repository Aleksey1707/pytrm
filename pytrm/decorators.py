import functools
from typing import Awaitable, Callable, Optional, ParamSpec, TypeAlias, TypeVar

from pytrm import share

P = ParamSpec("P")
T = TypeVar("T")

F: TypeAlias = Callable[P, Awaitable[T]]


def transactional_with_params(
    trm_attr_name: str,
    trm_settings_attr_name: Optional[str],
) -> Callable[[F[P, T]], F[P, T]]:
    """Выполнение метода в транзакции (с указанием параметров)"""

    def wrapped(func: F[P, T]) -> F[P, T]:

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            this = args[0]
            context = kwargs["context"]

            transaction_manager = getattr(this, trm_attr_name)

            if trm_settings_attr_name is not None:
                transaction_manager_settings = getattr(this, trm_settings_attr_name)
            else:
                transaction_manager_settings = None

            async with transaction_manager.do(context, settings=transaction_manager_settings) as new_context:
                kwargs["context"] = new_context
                return await func(*args, **kwargs)

        return wrapper

    return wrapped


def transactional(func: F[P, T]) -> F[P, T]:
    """Выполнение метода в транзакции"""

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        trm_attr_name = share.DEFAULT_REGISTRY.get_trm_attr_name()
        trm_settings_attr_name = share.DEFAULT_REGISTRY.get_trm_settings_attr_name()

        this = args[0]
        context = kwargs["context"]

        transaction_manager = getattr(this, trm_attr_name)
        transaction_manager_settings = getattr(this, trm_settings_attr_name, None)

        async with transaction_manager.do(context, settings=transaction_manager_settings) as new_context:
            kwargs["context"] = new_context
            return await func(*args, **kwargs)

    return wrapper
