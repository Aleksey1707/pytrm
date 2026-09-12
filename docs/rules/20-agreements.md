# Соглашения по коду

- **Область.** Весь код пакета и тестов: именование, сигнатуры, документация, иерархия
  классов, порядок функций в модуле, пайплайн проверок.
- **Читать перед.** Любой правкой кода.
- **Словарь.** Плейсхолдеры и модальность — `00-index.md`.

## Command-query separation

Функция либо читает данные и возвращает их (запрос), либо изменяет состояние и ничего
не возвращает (команда).

- Запрос MUST NOT изменять состояние и MUST вызывать только запросы.
- Команда MAY вызывать и команды, и запросы.
- Осознанное нарушение MUST быть видно в имени (`get_or_create_*`), иначе по сигнатуре
  нельзя понять, что делает вызов.

## Именование запросов

| Префикс | Контракт |
|---|---|
| `get_*` | MUST вернуть значение либо бросить исключение; возврат `None` MUST NOT |
| `find_*` | MAY вернуть значение или `None`; исключение SHOULD NOT, но допустимо |

Пара `find` / `get` строится так: `get` зовёт `find` и превращает `None` в исключение.

```python
# плохо — get молча возвращает None, вызывающий обязан проверять
def get_transaction(ctx: Context, key: Key) -> Optional[Transaction]:
    return ctx.find(key)

# хорошо
def get(self, ctx: Context, key: Key) -> Transaction:
    transaction = self.find(ctx, key)
    if transaction is None:
        raise exceptions.TransactionNotFoundInContextException

    return transaction
```

## Иерархия классов

Иерархия SHOULD быть как можно более плоской.

- Класс с наследниками MUST быть абстрактным (`abc.ABC` или `metaclass=abc.ABCMeta`).
- Класс без наследников MUST быть финальным (`@final`) либо оставаться листом по факту:
  появился наследник — класс становится абстрактным.
- Наследование ради переиспользования кода SHOULD NOT: общее поведение выносится в
  отдельный объект или функцию.

## Аннотации типов

- Каждая функция и каждый метод MUST иметь аннотации параметров и возвращаемого значения.
- `Any` MUST NOT появляться в сигнатурах. Исключение — псевдонимы на границе с драйвером,
  где тип принципиально неизвестен (`NativeTransaction`, `ContextValue`); новый такой
  псевдоним заводится только с разрешения владельца проекта.
- Публичный контракт описывается `Protocol`, а не абстрактным базовым классом, если от
  реализации не требуется общего кода.

Проверяется: `uv run mypy` (`disallow_untyped_defs`, `disallow_any_unimported`,
`warn_return_any`).

## Совместимость версий

Пакет поддерживает Python 3.9–3.14.

- Синтаксис MUST оставаться совместимым с 3.9: `Optional[X]` и `Union[X, Y]` вместо `X | Y`.
- Возможности `typing`, появившиеся позже 3.9, MUST подключаться через guard на
  `sys.version_info` с запасным импортом из `typing_extensions`:

```python
if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self
```

Проверяется: `make test` (`tox -p auto` прогоняет все поддерживаемые версии).

## Документация

- У каждого публичного класса и метода MUST быть docstring.
- Docstring метода MUST быть в формате reStructuredText: `:param:`, `:return:`, `:raises:`.
- У исключения с заполненным `default_message` docstring MAY отсутствовать — см.
  `12-errors.md`.
- Комментарии-пересказы кода MUST NOT добавляться; комментарий объясняет «почему»,
  а не «что».

## Правило понижения

Модуль читается сверху вниз как рассказ: сначала высокоуровневые функции, ниже — те,
которые они вызывают.

- Вызываемая функция SHOULD располагаться ниже вызывающей; уровень детализации растёт
  к концу файла.
- Отступление допускается там, где имя обязано быть определено раньше использования
  (разрешение имени в момент импорта), и MUST сопровождаться комментарием с причиной.

## Стиль правки

- Diff MUST быть минимальным: переписывать соседний код без запроса MUST NOT.
- Неиспользуемый код вне зоны задачи MUST NOT трогаться.
- Примеры использования в коде MUST NOT добавляться — их место в README и docstring.

## Пайплайн

```bash
make                     # format → lint → test-fast
make format              # ruff format . + ruff check --fix .
make lint                # rules-check + mypy + ruff format --check + ruff check
make rules-check         # свод docs/rules против стандарта 00-index.md
make test-fast           # pytest -m "not integration" (без Docker)
make test                # tox -p auto по всем версиям Python
make build               # uv build
uv run pytest tests/redis/test_redis_trm.py         # один файл
uv run pytest tests/redis/test_redis_trm.py::test_x # один тест
uv run pytest -m integration                        # только интеграционные
```

- Длина строки — 120 символов; форматирование делает `ruff format`, руками MUST NOT.
- Порядок импортов задаёт правило `I` у `ruff`; сортировать вручную MUST NOT.
- Интеграционные тесты требуют Docker или Podman; в `tox.ini` задан
  `DOCKER_HOST=unix:///run/user/1000/podman/podman.sock`.
- `pre-commit` гоняет `mypy`, `ruff check --fix`, `ruff format --check` и `tox`.

Проверяется: `make`.

## Связанные правила

- Архитектура пакета — `10-architecture.md`
- Исключения — `12-errors.md`
- Тесты — `19-testing.md`
- Ведение свода — `00-index.md`
