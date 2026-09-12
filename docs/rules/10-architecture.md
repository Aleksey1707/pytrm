# Архитектура

- **Область.** Раскладка пакета `pytrm/`, граф импортов, публичный API, `Registry`,
  конфигурация и декораторы.
- **Читать перед.** Новым модулем в пакете; правкой `__init__.py`, `share.py`, `bases.py`,
  `configurations.py`, `decorators.py`.
- **Словарь.** Плейсхолдеры и модальность — `00-index.md`.

## Что это

`pytrm` — менеджер транзакций как абстракция доступа к БД. Инфраструктурная деталь
(нативная транзакция, сессия, pipeline) прячется в неизменяемый **контекст**; работать с
контекстом вправе только **менеджер контекста**. Прикладной код видит три вещи: реализацию
`TransactionManager`, функции `get_native_transaction` / `find_native_transaction` и
декораторы `transactional` / `transactional_with`.

Отсюда главный принцип: **прикладной код не знает про драйвер БД**. Он передаёт контекст,
а какую именно транзакцию открыть — решает реализация, выбранная в композиционном корне.

## Слои и граф импортов

Модули упорядочены снизу вверх; импорт MUST идти только вниз по таблице. Циклы MUST NOT.

| Модуль | Чем является | Что импортирует из пакета |
|---|---|---|
| `utils/marks.py` | сентинел `NotSet` и хелперы к нему | — |
| `exceptions.py` | иерархия исключений | — |
| `share.py` | контракты: протоколы, `Settings`, `Registry`, `ContextManager` | `exceptions` |
| `bases.py` | скелет менеджера: `BaseTransactionManager` | `exceptions`, `share` |
| `impls/mongo/base.py` | общая часть двух драйверов MongoDB | `bases`, `share`, `exceptions` |
| `impls/<impl>.py` | обёртки над конкретной БД | `bases`, `share`, `exceptions` |
| `configurations.py` | сборка реестра | `share` |
| `decorators.py` | `transactional`, `transactional_with` | `share`, `utils.marks` |
| `__init__.py` | публичный API | `configurations`, `decorators`, `share` |

Норма читается так: `share.py` MUST NOT импортировать `bases`; `bases.py` MUST NOT знать про
конкретный драйвер; `impls/<impl>.py` MUST NOT импортировать другую реализацию.

Проверяется: `uv run ruff check .` (правило `I` — порядок импортов; циклы ловит `uv run mypy`).

## Публичный API

Публичный API — это ровно то, что перечислено в `pytrm/__init__.py`. Всё остальное
внутреннее и MAY меняться без объявления.

- Ре-экспорт MUST оформляться формой `from .share import X as X`: без неё строгая проверка
  типов считает имя приватным для импортирующих.
- `pytrm/impls/**` MUST NOT попадать в `pytrm/__init__.py`: реализации тянут опциональные
  зависимости из extras, и импорт пакета сломался бы без установленного драйвера.
  Прикладной код импортирует реализацию явно: `from pytrm.impls.sqlalchemy import ...`.
- `DEFAULT_REGISTRY` из API исключён намеренно: доступ к реестру по умолчанию идёт через
  `configurate` и через параметр `reg` публичных функций.
- Версия пакета живёт в `pytrm.__version__` и оттуда же читается сборкой
  (`[tool.hatch.version]`). Дублировать её в `pyproject.toml` MUST NOT.

```python
# плохо — реализация в публичном API: импорт pytrm упадёт без установленного драйвера
from .impls.sqlalchemy import SqlAlchemyTransactionManager

# хорошо — прикладной код берёт реализацию сам
from pytrm.impls.sqlalchemy import SqlAlchemyTransactionManager
```

## Контекст неизменяем

`Context` — протокол с `find` / `set` / `remove`, где `set` и `remove` возвращают `Self`,
то есть **новый** экземпляр. Отсюда:

- реализация `Context` MUST возвращать новый объект, а не мутировать себя;
- результат `ContextManager.set` / `ContextManager.remove` MUST использоваться; вызов
  ради побочного эффекта — дефект, потому что исходный контекст не изменится;
- менять контекст вправе только `ContextManager`; прикладной код и реализации MUST NOT
  звать `ctx.set` / `ctx.remove` напрямую.

```python
# плохо — результат выброшен, ctx не изменился
self._ctx_manager.set(ctx, key, transaction)
return ctx

# хорошо
return self._ctx_manager.set(ctx, key, transaction)
```

## Реестр и конфигурация

`Registry` хранит хранилище настроек, менеджер контекста и имена атрибутов, по которым
декораторы достают менеджер транзакций и его настройки с `self`.

- `Registry.initialize` вызывается **один раз**: повторный вызов бросает
  `RegistryIsAlreadyInitializedException`. Конфигурация MUST выполняться в композиционном
  корне приложения, а не в библиотечном коде и не в момент импорта модуля.
- `configurate(...)` настраивает реестр по умолчанию — тот, который используют декораторы и
  значения `reg` по умолчанию.
- `get_configurated_reg(...)` возвращает **отдельный** реестр, не трогая глобальный. Это
  форма для тестов и для нескольких независимых конфигураций в одном процессе.
- `SettingsStorage.create` с пустым набором бросает `NoSettingsException`: реестр без
  настроек бессмысленен.

Настройки адресуются по `UniqSettings.id`. Один `id` = одна пара «ключ в контексте +
правило распространения». Реализация получает свои настройки через `create(..., settings_id)`,
а не конструированием `Settings` на месте.

## Внедрение зависимостей

Менеджер транзакций собирается фабрикой `create` и получает `ctx_manager` и `settings`
**из реестра**, а не из аргументов вызывающего кода:

```python
trm = SqlAlchemyTransactionManager.create(sessionmaker_, "orders")
```

Параметр `reg` у `create` и у `get_native_transaction` / `find_native_transaction` MUST
оставаться keyword-only с умолчанием `DEFAULT_REGISTRY`: это точка подмены в тестах,
а не штатный аргумент прикладного кода.

## Декораторы

`transactional` и `transactional_with` оборачивают **асинхронный метод** и опираются на две
вещи: `args[0]` — это `self`, а контекст приходит **именованным** аргументом `context`.

- Декорируемая функция MUST быть `async def` и MUST принимать `context` по имени; позиционная
  передача контекста сломает декоратор.
- Декоратор MUST возвращать новый контекст внутрь функции, подменяя `kwargs["context"]`;
  дальше по цепочке вызовов передаётся именно он.
- `transactional_with` различает «не передано» и «передано `None`» через сентинел
  `marks.NOT_SET`: `trm_settings_attr_name=None` означает «настроек на объекте нет, работать
  с настройками менеджера», а `NOT_SET` — «взять имя атрибута из реестра». Новые опциональные
  параметры с таким же различием MUST использовать `marks.NOT_SET`, а не `None`.

```python
# плохо — контекст позиционно, декоратор его не найдёт
@pytrm.transactional
async def create(self, context, dto): ...

# хорошо
@pytrm.transactional
async def create(self, dto, *, context: Context) -> None: ...
```

## Связанные правила

- Правила распространения транзакции — `11-propagation.md`
- Реализации под конкретную БД — `13-impls.md`
- Исключения — `12-errors.md`
- Соглашения по коду — `20-agreements.md`
