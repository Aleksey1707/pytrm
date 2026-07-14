from pytrm import share


def configurate(
    trm_attr_name: str,
    trm_settings_attr_name: str,
    *settings: share.UniqSettings,
) -> None:
    """
    Сконфигурировать реестр по умолчанию

    :param trm_attr_name: имя атрибута, содержащего менеджер транзакций
    :param trm_settings_attr_name: имя атрибута, содержащего настройки менеджера транзакций
    :param settings: настройки менеджера транзакций
    :raises NoSettingsException: если не переданы настройки
    :raises RegistryIsAlreadyInitializedException: если реестр уже инициализирован
    """
    settings_storage = share.SettingsStorage.create(settings)

    share.DEFAULT_REGISTRY.initialize(
        settings_storage,
        share.DEFAULT_CONTEXT_MANAGER,
        trm_attr_name,
        trm_settings_attr_name,
    )


def get_configurated_reg(
    trm_attr_name: str,
    trm_settings_attr_name: str,
    *settings: share.UniqSettings,
) -> share.Registry:
    """
    Получить сконфигурированный реестр

    :param trm_attr_name: имя атрибута, содержащего менеджер транзакций
    :param trm_settings_attr_name: имя атрибута, содержащего настройки менеджера транзакций
    :param settings: настройки менеджера транзакций
    :return: инициализированный реестр
    :raises NoSettingsException: если не переданы настройки
    """
    settings_storage = share.SettingsStorage.create(settings)

    reg = share.Registry()
    reg.initialize(
        settings_storage,
        share.DEFAULT_CONTEXT_MANAGER,
        trm_attr_name,
        trm_settings_attr_name,
    )
    return reg
