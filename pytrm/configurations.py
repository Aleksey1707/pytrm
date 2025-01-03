from pytrm import share


def configurate(
    *settings: share.Settings,
) -> None:
    """Сконфигурировать (реестр по умолчанию)"""
    settings_storage = share.SettingsStorage.create(settings)

    share.DEFAULT_REGISTRY.initialize(settings_storage, share.DEFAULT_CONTEXT_MANAGER)


def get_configurated_reg(
    *settings: share.Settings,
) -> share.Registry:
    """Получить сконфигурированный реестр"""
    settings_storage = share.SettingsStorage.create(settings)

    reg = share.Registry()
    reg.initialize(settings_storage, share.DEFAULT_CONTEXT_MANAGER)
    return reg
