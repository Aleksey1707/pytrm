# Реализации

- **Область.** `pytrm/impls/**`, extras и группы зависимостей в `pyproject.toml`,
  секция `deps` в `tox.ini`.
- **Читать перед.** Новой реализацией под БД; правкой существующей; добавлением extra.
- **Словарь.** Плейсхолдеры и модальность — `00-index.md`.

## Раскладка

Один модуль — одна реализация, имя модуля совпадает с именем драйвера
(`sqlalchemy.py`, `redis.py`, `mongo/motor.py`). В модуле живут три вида классов:

| Класс | Роль | Обязателен |
|---|---|---|
| `<Impl>Transaction` | обёртка над нативной транзакцией | да |
| `<Impl>NestedTransaction` | обёртка над точкой сохранения | только если драйвер её умеет |
| `<Impl>TransactionManager` | наследник `bases.BaseTransactionManager` | да |

- Модуль реализации MUST NOT импортировать другую реализацию: общий код живёт в `bases.py`
  или `share.py`.
- Импорт драйвера MUST стоять на верхнем уровне модуля: модуль и так загружается только
  тогда, когда прикладной код импортирует его явно.
- `pytrm/impls/__init__.py` MUST оставаться пустым: любой импорт в нём потянет драйвер.

## Обёртка над транзакцией

Обёртка соответствует протоколу `share.Transaction` структурно — наследовать протокол
SHOULD NOT: `runtime_checkable` проверяет только наличие методов, а наследование мешает
`__slots__`.

- MUST быть объявлены все пять методов: `is_active`, `begin`, `commit`, `rollback`, `unwrap`.
- `is_active()` MUST отражать состояние драйвера, если драйвер его отдаёт
  (`session.in_transaction()`, `savepoint.is_active`); собственный флаг MAY использоваться
  только там, где драйвер состояния не даёт.
- `unwrap()` MUST возвращать объект, через который прикладной код действительно работает
  с БД: для SQLAlchemy это сессия, для Redis — pipeline. Именно он придёт из
  `get_native_transaction`.
- У обёртки и у менеджера MUST быть `__slots__`: объекты создаются на каждый блок `do()`.
- Состояние драйвера MUST храниться на экземпляре. `ClassVar`-кеш фабрики MUST NOT:
  второй менеджер с другим подключением молча получит чужое.

```python
# плохо — фабрика в ClassVar: первый sessionmaker выигрывает навсегда
class SqlAlchemyTransaction:
    _sessionmaker: ClassVar[Optional[sessionmaker]] = None

    @classmethod
    def create(cls, sessionmaker: sessionmaker) -> Self:
        if cls._sessionmaker is None:
            cls._sessionmaker = sessionmaker
        return cls(cls._sessionmaker())

# хорошо — фабрика приходит на каждый вызов
class SqlAlchemyTransaction:
    __slots__ = ("_session",)

    @classmethod
    def create(cls, sessionmaker_: sessionmaker) -> Self:
        return cls(sessionmaker_())
```

## Менеджер транзакций

Менеджер MUST наследовать `bases.BaseTransactionManager` и реализовывать оба абстрактных
метода. Переопределять `do` и `_do` MUST NOT: там живёт общий инвариант владения транзакцией.

- `_create_transaction` возвращает новую обёртку.
- `_create_nested_transaction` получает **родительскую** транзакцию и оборачивает её
  `unwrap()`. Если драйвер вложенности не умеет — MUST бросать
  `NestedTransactionsNotSupportedTrmException`, а не открывать обычную транзакцию.
- Конструктор MUST принимать `ctx_manager` и `settings` первыми и передавать их в `super()`;
  объект драйвера идёт после них.
- Фабрика MUST быть classmethod со сигнатурой
  `create(cls, <объект драйвера>, settings_id, *, reg=share.DEFAULT_REGISTRY)` и брать
  `ctx_manager` и `settings` из реестра. Параметр `reg` MUST оставаться keyword-only.

```python
@classmethod
def create(
    cls,
    client: Redis,
    settings_id: share.SettingsID,
    *,
    reg: share.Registry = share.DEFAULT_REGISTRY,
) -> Self:
    return cls(
        client=client,
        ctx_manager=reg.get_ctx_manager(),
        settings=reg.get_settings_by_id(settings_id),
    )
```

## Ограничения драйвера

Ограничение, которое видит пользователь, MUST быть записано в docstring класса, а не только
в README: docstring — единственное, что доедет до подсказок редактора.

Так уже описаны: накопление команд в pipeline у Redis без чтения внутри блока,
отсутствие вложенности у Redis и Mongo, непригодность одного pipeline для параллельных
корутин.

## Подключение новой реализации

Новая реализация MUST приносить с собой весь набор — иначе она не соберётся ни в CI,
ни у пользователя:

- extra в `[project.optional-dependencies]` — имя `<extra>`;
- драйвер в `[dependency-groups] dev` и в `deps` секции `[testenv]` файла `tox.ini`;
- `[[tool.mypy.overrides]]` с `ignore_missing_imports = true`, если у драйвера нет типов;
- каталог `tests/<impl>/` с `conftest.py`, поднимающим контейнер, и набором тестов;
- строка в README о том, какой extra ставить.

## Связанные правила

- Архитектура пакета и публичный API — `10-architecture.md`
- Правила распространения — `11-propagation.md`
- Исключения — `12-errors.md`
- Тесты реализации — `19-testing.md`
