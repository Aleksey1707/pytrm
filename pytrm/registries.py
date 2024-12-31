from typing import Final, NamedTuple, Optional

from pytrm import exceptions, interfaces


class _RegistryData(NamedTuple):
    """Данные реестра"""

    default_settings: interfaces.Settings  # настройки по умолчанию
    settings_storage: interfaces.SettingsStorage  # хранилище настроек
    ctx_manager: interfaces.ContextManager  # менеджер контекста


class Registry:

    __slots__ = ("_data",)

    _data: Optional[_RegistryData]

    def __init__(self) -> None:
        self._data = None

    def initialize(
        self,
        default_settings: interfaces.Settings,
        settings_storage: interfaces.SettingsStorage,
        ctx_manager: interfaces.ContextManager,
    ) -> None:
        """
        Инициализировать реестр

        :param default_settings: настройки по умолчанию
        :param settings_storage: хранилище настроек
        :param ctx_manager: менеджер контекста
        :return: None
        :raises RegistryIsAlreadyInitializedException: если реестр уже инициализирован
        """
        if self._data is not None:
            raise exceptions.RegistryIsAlreadyInitializedException

        self._data = _RegistryData(
            default_settings=default_settings,
            settings_storage=settings_storage,
            ctx_manager=ctx_manager,
        )

    def get_default_settings(self) -> interfaces.Settings:
        """
        Получить настройки по умолчанию

        :return: настройки по умолчанию
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        """
        data = self._get_registry_data()
        return data.default_settings

    def get_settings_by_id(self, id_: interfaces.SettingsID) -> interfaces.Settings:
        """
        Получить настройки по идентификатору

        :param id_: идентификатор настроек
        :return: настройки по умолчанию
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        :raises SettingsNotFoundException: если настройки не найдены
        """
        data = self._get_registry_data()
        settings = data.settings_storage.get(id_)
        return settings

    def get_ctx_manager(self) -> interfaces.ContextManager:
        """
        Получить контекстный менеджер

        :return: настройки по умолчанию
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        """
        data = self._get_registry_data()
        return data.ctx_manager

    def _get_registry_data(self) -> _RegistryData:
        if self._data is None:
            raise exceptions.RegistryIsNotInitializedException

        return self._data


DEFAULT_REGISTRY: Final = Registry()
