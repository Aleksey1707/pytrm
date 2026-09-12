# Долг: осознанные отступления от сводов

Здесь фиксируются места, где код **осознанно** расходится со сводом. Всё, чего в этом файле
нет, — нарушение, а не долг.

Формат записи: правило → место → причина → условие выхода.

Дата ревизии: 2026-09-12 (по итогам аудита проекта: закрыты `NEVER` без транзакции,
`exclude` для наследников `BaseException`, `ClassVar`-кеш `sessionmaker`, незакрытая сессия
SQLAlchemy, `end_session` мимо `finally` у Mongo, мёртвый `_set_new_transaction` и
расхождение docstring `Registry` с сигнатурами).

## Аннотация `in_transaction` в motor (`13-impls.md`)

`13-impls.md` требует, чтобы `is_active()` читал состояние драйвера напрямую. Общая обёртка
`BaseMongoTransaction` объявляет сессию протоколом `MongoSession`, где `in_transaction` —
свойство типа `bool`. Так оно и работает в рантайме: интеграционные тесты обоих драйверов
на этом и держатся.

Но motor объявляет `AgnosticClientSession.in_transaction` как `Callable[[], bool]` — метод,
а не свойство. Аннотация драйвера расходится с его же поведением, поэтому сборка обёртки
в `impls/mongo/motor.py` помечена `# type: ignore[arg-type]`.

Причина, по которой не чинится здесь: править чужие аннотации можно только заглушками
(`stubs/`) на весь пакет motor, а это дороже одной строки подавления. Само подавление
точечное и именованное — `warn_unused_ignores` снимет его, как только motor исправит тип.

Условие выхода: motor публикует `in_transaction` как свойство, либо проект переезжает
на `pymongo.AsyncMongoClient` целиком и модуль motor удаляется.

## Непоследовательный инфикс `Trm` в исключениях (`12-errors.md`)

`12-errors.md` требует от нового исключения следовать соседям по подсистеме. Сейчас сами
соседи расходятся: инфикс есть у всех баз и у `PropagationMandatoryTrmException`,
`PropagationNeverTrmException`, `NestedTransactionsNotSupportedTrmException`, но отсутствует
у `TransactionNotFoundInContextException`, `UnknownValueInContextException`,
`RegistryIsNotInitializedException`, `RegistryIsAlreadyInitializedException`,
`SettingsNotFoundException` и `NoSettingsException`.

Причина, по которой не чинится сейчас: имена исключений — публичный API, их ловит
прикладной код. Переименование шести классов — отдельная правка с мажорной версией и
периодом совместимости через алиасы, а не побочный эффект аудита.

Условие выхода: ближайшее изменение публичного API, при котором заводятся алиасы старых
имён и объявляется срок их удаления.

## Связанные правила

- Реализации под конкретную БД — `13-impls.md`
- Исключения — `12-errors.md`
- Ведение свода — `00-index.md`
