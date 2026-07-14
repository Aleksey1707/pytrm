import functools
import sys
from typing import (
    Any,
    Callable,
    Coroutine,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from pytrm import share
from pytrm.utils import marks

P = ParamSpec("P")
T = TypeVar("T")

F = Callable[P, Coroutine[Any, Any, T]]


def transactional_with(
    trm_attr_name: Union[str, marks.NotSet] = marks.NOT_SET,
    trm_settings_attr_name: Union[Optional[str], marks.NotSet] = marks.NOT_SET,
    propagation: Optional[share.Propagation] = None,
    exclude: Tuple[Type[BaseException], ...] = (),
) -> Callable[[F[P, T]], F[P, T]]:
    """
    Декоратор выполнения метода в транзакции с указанием параметров

    :param trm_attr_name: имя атрибута, содержащего менеджер транзакций
    :param trm_settings_attr_name: имя атрибута, содержащего настройки менеджера транзакций
    :param propagation: правило распространения транзакции (переопределяет значение из настроек)
    :param exclude: типы исключений, при которых требуется фиксация изменений вместо отката
    :return: декоратор метода
    :raises RegistryIsNotInitializedException: если реестр не инициализирован
    :raises TrmAttrNameNoAtRegistryException: если имя атрибута менеджера не задано в реестре
    :raises TrmSettingsAttrNameNoAtRegistryException: если имя атрибута настроек не задано в реестре
    """

    def wrapped(func: F[P, T]) -> F[P, T]:

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            this = args[0]
            context = kwargs["context"]

            trm_attr_name_ = marks.value_or(
                trm_attr_name,
                share.DEFAULT_REGISTRY.get_trm_attr_name(),
            )

            trm = getattr(this, trm_attr_name_)

            trm_settings_attr_name_ = marks.value_or(
                trm_settings_attr_name,
                share.DEFAULT_REGISTRY.get_trm_settings_attr_name(),
            )

            if trm_settings_attr_name_ is not None:
                trm_settings = getattr(this, trm_settings_attr_name_)
            else:
                trm_settings = None

            async with trm.do(
                context,
                settings=trm_settings,
                exclude=exclude,
                propagation=propagation,
            ) as new_context:
                kwargs["context"] = new_context
                return await func(*args, **kwargs)

        return wrapper

    return wrapped


def transactional(func: F[P, T]) -> F[P, T]:
    """
    Декоратор выполнения метода в транзакции

    Имена атрибутов менеджера транзакций и настроек берутся из реестра по умолчанию.

    :param func: декорируемый асинхронный метод
    :return: обёрнутый метод
    :raises RegistryIsNotInitializedException: если реестр не инициализирован
    :raises TrmAttrNameNoAtRegistryException: если имя атрибута менеджера не задано в реестре
    :raises TrmSettingsAttrNameNoAtRegistryException: если имя атрибута настроек не задано в реестре
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        trm_attr_name = share.DEFAULT_REGISTRY.get_trm_attr_name()
        trm_settings_attr_name = share.DEFAULT_REGISTRY.get_trm_settings_attr_name()

        this = args[0]
        context = kwargs["context"]

        trm = getattr(this, trm_attr_name)
        trm_settings = getattr(this, trm_settings_attr_name, None)

        async with trm.do(context, settings=trm_settings) as new_context:
            kwargs["context"] = new_context
            return await func(*args, **kwargs)

    return wrapper
