from pytrm import share


def configurate(
    trm_attr_name: str,
    trm_settings_attr_name: str,
    *settings: share.Settings,
) -> None:
    """Сконфигурировать (реестр по умолчанию)"""
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
    *settings: share.Settings,
) -> share.Registry:
    """Получить сконфигурированный реестр"""
    settings_storage = share.SettingsStorage.create(settings)

    reg = share.Registry()
    reg.initialize(
        settings_storage,
        share.DEFAULT_CONTEXT_MANAGER,
        trm_attr_name,
        trm_settings_attr_name,
    )
    return reg
