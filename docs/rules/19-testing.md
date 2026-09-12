# Тесты

- **Область.** `tests/**`, секция `[tool.pytest.ini_options]` в `pyproject.toml`, `tox.ini`.
- **Читать перед.** Новым тестом; правкой `conftest.py` и общей обвязки; добавлением набора
  тестов для новой реализации.
- **Словарь.** Плейсхолдеры и модальность — `00-index.md`.

## Обвязка

Корневой `tests/conftest.py` даёт три фикстуры и автоиспользуемую инициализацию реестра
по умолчанию:

| Фикстура | Область | Что даёт |
|---|---|---|
| `context` | function | пустой тестовый контекст |
| `settings` | session | `UniqSettings` с `id="test"` и `Propagation.REQUIRED` |
| `registry` | session | отдельный реестр через `get_configurated_reg` |
| `init_default_registry` | session, autouse | конфигурация реестра по умолчанию |

- Фикстура `transaction_manager` MUST объявляться в `conftest.py` конкретной реализации:
  это шов, за счёт которого общие наборы тестов работают для любой БД.
- Менеджер в этой фикстуре MUST собираться через `create(..., settings.id, reg=registry)` —
  с явным реестром, а не с реестром по умолчанию.
- Реестр по умолчанию инициализируется один раз на сессию; вызывать `configurate` в тесте
  MUST NOT — повторный вызов бросит `RegistryIsAlreadyInitializedException`.
- Тестовая реализация контекста живёт в `tests/contexts.py`, стабы транзакций и менеджеров —
  в `tests/stubs.py`, репозитории — в `tests/repositories.py`. Копировать их в файл теста
  MUST NOT.

## Общие наборы

Набор тестов, одинаковый для нескольких реализаций одного контракта, живёт в отдельном
модуле (`tests/shared_test_propagation.py`, `tests/mongo/shared_test_propagation.py`) и
подключается явным ре-экспортом по одному тесту на строку:

```python
from tests.shared_test_propagation import test_mandatory_propagation as test_mandatory_propagation
from tests.shared_test_propagation import test_never_propagation as test_never_propagation
```

- Форма `as` MUST сохраняться: без неё ре-экспорт считается приватным импортом.
- Подключаются MUST только те тесты, которые для этой реализации осмысленны: реализация без
  вложенных транзакций не ре-экспортирует `test_nested_propagation`, а пишет свой тест на
  `NestedTransactionsNotSupportedTrmException`.
- Копировать файл набора целиком MUST NOT; расхождение копий не заметит ни один линтер.

## Маркеры и разделение

Тест, которому нужна живая БД, MUST помечаться маркером `integration` — он объявлен в
`pyproject.toml`, и `--strict-markers` не даст опечататься.

```python
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]
```

- Контейнер поднимается через `testcontainers` в `conftest.py` реализации, с областью
  `session`: контейнер на тест — это минуты вместо секунд.
- `make test-fast` гоняет `pytest -m "not integration"` и MUST оставаться зелёным без Docker.
- Полный прогон — `make test` (`tox -p auto`) по всем поддерживаемым версиям Python.

Проверяется: `uv run pytest --strict-markers` (незарегистрированный маркер — ошибка).

## Структура теста

- В тесте с несколькими логическими шагами блоки MUST размечаться комментариями
  `# given`, `# when`, `# then` (`# and` — дополнительный шаг внутри блока).
- В тривиальном тесте (один вызов, одна проверка) такие комментарии MUST NOT добавляться.
- Ожидаемое исключение MUST проверяться через `pytest.raises`, а не через `try/except`
  с проверками внутри `except`: такой тест проходит молча, если исключение не возникло.

```python
# плохо — тест зелёный, даже если исключения не было
try:
    async with trm.do(ctx, settings=mandatory) as new_ctx:
        pass
except exceptions.PropagationMandatoryTrmException:
    assert True

# хорошо
with pytest.raises(exceptions.PropagationMandatoryTrmException):
    async with trm.do(ctx, settings=mandatory) as new_ctx:
        pass
```

## Данные и фикстуры

- Имя параметра-фикстуры MUST NOT переиспользоваться под её модифицированную копию — заводится
  отдельное описательное имя.
- Модификация неизменяемой структуры MUST идти штатным copy-with-changes
  (`dataclasses.replace`, `Settings.with_propagation`), а не ручной пересборкой полей.

## Покрытие

- Для каждого нового публичного класса или метода MUST быть тест на happy path и на каждое
  задокументированное в `:raises` исключение.
- Внутренние building-block компоненты (утилиты, хранилища, реестр) MUST иметь собственные
  unit-тесты, а не проверяться только опосредованно через интеграционные.
- Новая реализация MUST закрывать все семь правил распространения — своими тестами либо
  ре-экспортом общего набора.
- Тест без содержательных проверок MUST NOT существовать без явного назначения: либо удалить,
  либо задокументировать, зачем он нужен.

## Связанные правила

- Правила распространения — `11-propagation.md`
- Реализации под конкретную БД — `13-impls.md`
- Соглашения по коду и пайплайн — `20-agreements.md`
