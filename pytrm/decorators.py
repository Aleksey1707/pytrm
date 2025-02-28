import functools
import sys
from typing import Awaitable, Callable, Optional, Tuple, Type, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from pytrm import share
from pytrm.utils import marks

P = ParamSpec("P")
T = TypeVar("T")

F = Callable[P, Awaitable[T]]


def transactional_with(
    trm_attr_name: Union[str, marks.NotSetType] = marks.NOT_SET,
    trm_settings_attr_name: Union[Optional[str], marks.NotSetType] = marks.NOT_SET,
    exclude: Tuple[Type[BaseException], ...] = (),
) -> Callable[[F[P, T]], F[P, T]]:
    """Выполнение метода в транзакции (с указанием параметров)"""

    def wrapped(func: F[P, T]) -> F[P, T]:

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            this = args[0]
            context = kwargs["context"]

            if marks.is_set(trm_attr_name):
                trm_attr_name_ = trm_attr_name
            else:
                trm_attr_name_ = share.DEFAULT_REGISTRY.get_trm_attr_name()

            transaction_manager = getattr(this, trm_attr_name_)

            if marks.is_set(trm_settings_attr_name):
                trm_settings_attr_name_ = trm_settings_attr_name
            else:
                trm_settings_attr_name_ = share.DEFAULT_REGISTRY.get_trm_settings_attr_name()

            if trm_settings_attr_name_ is not None:
                transaction_manager_settings = getattr(this, trm_settings_attr_name_)
            else:
                transaction_manager_settings = None

            async with transaction_manager.do(
                context,
                settings=transaction_manager_settings,
                exclude=exclude,
            ) as new_context:
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
