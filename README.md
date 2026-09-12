# PyTRM

Менеджер транзакций для работы с различными БД.

## Описание

Данный проект является вольной адаптацией [go-transaction-manager](https://github.com/avito-tech/go-transaction-manager) от AvitoTech для Python.

Если кратко, то идея заключается в абстрагировании от инфраструктурных деталей (той же транзакции к БД) и хранение их в неизменяемой структуре "Контекст". Работать с контекстом может только менеджер контекста (не путать с менеджером контекста в Python Core), который используется при работе через публичное API библиотеки `pytrm`: реализация менеджера транзакций (`pytrm.TransactionManager`) и функции получения нативной транзакции (`pytrm.get_native_transaction` и `pytrm.find_native_transaction`)

Во всех реализациях менеджера транзакций (кроме null реализации, которая ничего не делает) заложена след. логика:

- Фиксация изменений при выходе из блока работы с транзакцией при отсутствии исключения
- Откат изменений при наличии исключения

Если требуется фиксация изменений для конкретных типов исключений, то их можно указать в параметре `exclude` в методе менеджера транзакций `pytrm.TransactionManager.do` и декораторе `pytrm.transactional_with`.

## Установка

Данный пакет не опубликован в PyPI, но его можно установить из Git репозитория.

### Установка через pip:

```sh
# установка последней версии (нежелательно)
pip install git+https://github.com/Aleksey1707/pytrm.git@master

# установка конкретной версии
pip install git+https://github.com/Aleksey1707/pytrm.git@0.3.0

# установка конкретной версии с extras
pip install "pytrm[sqlalchemy] @ git+https://github.com/Aleksey1707/pytrm.git@0.3.0"
```

### Установка через uv:

```sh
uv add "pytrm[sqlalchemy] @ git+https://github.com/Aleksey1707/pytrm.git@0.3.0"
```

## Реализации

Каждая реализация живёт в своём модуле и тянет драйвер из соответствующего extra.
Ядро `pytrm` зависимостей от драйверов не имеет.

| БД | Extra | Модуль | Вложенные транзакции |
|---|---|---|---|
| PostgreSQL и другие через SQLAlchemy | `sqlalchemy` | `pytrm.impls.sqlalchemy` | да, через `SAVEPOINT` |
| MongoDB (motor) | `mongo-motor` | `pytrm.impls.mongo.motor` | нет |
| MongoDB (pymongo, async) | `mongo-pymongo` | `pytrm.impls.mongo.pymongo` | нет |
| Redis | `redis` | `pytrm.impls.redis` | нет |
| — (ничего не делает) | — | `pytrm.impls.null` | — |

Реализация без поддержки вложенности бросает `NestedTransactionsNotSupportedTrmException`
на `Propagation.NESTED`.

У Redis есть особенность: команды внутри блока только накапливаются в pipeline и применяются
на выходе из него. Прочитать записанное значение внутри того же блока нельзя — для чтения
нужен отдельный клиент вне транзакции.

## Использование

Для работы с `pytrm` требуется реализация контекста `pytrm.Context`, который является неизменяемой структурой.

Перед использованием требуется настройка:

- Создание настроек
  - ID настройки
  - Ключ по которому транзакция будет храниться в контексте
  - Правило распространения транзакции по умолчанию
- Конфигурация библиотеки
  - Указание атрибута, в котором хранится менеджер транзакции
  - Указание атрибута, в котором хранится настройка, которую необходимо использовать вместо настройки по умолчанию
  - Настройки по умолчанию, созданные ранее
- Создание экземпляров реализаций менеджера транзакции (достаточно одного экземпляра для использования во всех местах)

Пример:

```python
import pytrm
from pytrm.impls import sqlalchemy as sa_trm
from pytrm.impls.mongo import motor as motor_trm

# Настройки для MongoDB
mongo_settings = pytrm.UniqSettings(
    id="mongo",
    key=pytrm.Key("mongo"),
    propagation=pytrm.Propagation.REQUIRED,
)

# Настройки для Postgres
postgres_settings = pytrm.UniqSettings(
    id="postgres",
    key=pytrm.Key("postgres"),
    propagation=pytrm.Propagation.REQUIRED,
)

# Конфигурация pytrm
pytrm.configurate(
    "_trm",
    "_trm_settings",
    mongo_settings,
    postgres_settings,
)

# =============

# Создание менеджера транзакций для MongoDB
mongo_connection_url = ...
mongo_client = AsyncIOMotorClient(mongo_connection_url)
mongo_trm = motor_trm.MongoTransactionManager.create(mongo_client, mongo_settings.id)

# Создание менеджера транзакций для Postgres
postgres_connection_url = ...
engine = create_async_engine(url=postgres_connection_url)
sessionmaker_ = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
postgres_trm = sa_trm.SqlAlchemyTransactionManager.create(sessionmaker_, postgres_settings.id)
```

## Правила распространения

Правило задаётся в настройках и переопределяется параметром `propagation` у `do()` либо
у декоратора `transactional_with`.

| Правило | Транзакция в контексте есть | Транзакции нет |
|---|---|---|
| `REQUIRED` | переиспользовать существующую | создать новую |
| `NESTED` | создать вложенную от текущей | создать новую |
| `MANDATORY` | переиспользовать существующую | `PropagationMandatoryTrmException` |
| `NEVER` | `PropagationNeverTrmException` | выполнить без транзакции |
| `NOT_SUPPORTED` | убрать транзакцию из контекста на время блока | выполнить без транзакции |
| `REQUIRES_NEW` | создать новую, подменив её в контексте | создать новую |
| `SUPPORTS` | переиспользовать существующую | выполнить без транзакции |

Фиксирует и откатывает транзакцию тот блок, который её начал. Вложенный блок с `REQUIRED`
ничего не фиксирует — решение принимает внешний. Нужна независимая фиксация — `REQUIRES_NEW`,
нужен частичный откат — `NESTED`.

Отмена задачи (`asyncio.CancelledError`) откатывает транзакцию, а не оставляет её открытой.

Пример использования менеджера транзакций (императивный стиль):

```python
trm: pytrm.TransactionManager = postgres_trm
context = Context.empty()

async with trm.do(context) as new_context:
    stmt = table.insert().values(value="test")
    session = pytrm.get_native_transaction(new_context, postgres_settings.id)
    assert isinstance(session, AsyncSession)
    await session.execute(stmt)
```

Менеджер транзакций лучше всего проявляет себя если разрабатываемое приложение структурируется по предметным областям, а работа с базой происходит через репозиторий и используются декораторы из `pytrm`.

Пример использования менеджера транзакций (декларативный стиль):

```python
@dataclasses.dataclass(slots=True)
class Person:
    id: PersonID
    last_name: PersonLastName
    first_name: PersonFirstName
    mid_name: PersonMidName
    gender: Gender
    # ...


class PersonRepository(Protocol):

    async def get(self, id_: PersonID, *, context: Context) -> Person: ...

    async def save(self, entity: Person, *, context: Context) -> None: ...

    async def delete(self, id_: PersonID, *, context: Context) -> None: ...


class PersonMongoRepository:

    def __init__(
        self,
        collection: AsyncIOMotorCollection,
        settings_id: pytrm.SettingsID,
    ) -> None:
        self._collection = collection
        self._settings_id = settings_id

    async def get(self, id_: PersonID, *, context: Context) -> Person:
        doc = await self._collection.find_one({"_id": id_.value}, session=self._find_session(context))
        if doc is None:
            raise exceptions.PersonNotFoundError

        entity = mappers.person_doc_to_entity(doc)
        return entity

    async def save(self, entity: Person, *, context: Context) -> None:
        doc = mappers.person_entity_to_doc(entity)
        await self._collection.insert_one(doc, session=self._find_session(context))

    async def delete(self, id_: PersonID, *, context: Context) -> None:
        await self._collection.delete_one({"_id": id_.value}, session=self._find_session(context))

    def _find_session(self, context: Context) -> Optional[AsyncIOMotorClientSession]:
        session = pytrm.find_native_transaction(context, self._settings_id)
        if session is None:
            return None

        return cast(AsyncIOMotorClientSession, session)


@dataclasses.dataclass(slots=True, frozen=True)
class PersonAppService:

    _trm: pytrm.TransactionManager
    _trm_settings: Optional[pytrm.UniqSettings]
    _repo: PersonRepository

    @pytrm.transactional
    async def change_last_name(self, id_: str, new_last_name: str, reason: str, *, context: Context) -> None:
        person_id = PersonID(id_)
        new_last_name_ = PersonLastName(new_last_name)
        reason_ = Reason(reason)

        person = await self._repo.get(person_id, context=context)
        person.change_last_name(new_last_name_, reason_)
        await self._repo.save(person, context=context)
```

Используя декоратор `pytrm.transactional` на методе прикладного сервиса, внутри него контекст уже будет содержать активную транзакцию (взависимости от настроек), созданную на основе менеджера транзакций (атрибут `_trm`) и настроек менеджера транзакций (атрибут `_trm_settings`). Эти атрибуты были указаны в `pytrm.configurate`.

Есть настраиваемая версия `pytrm.transactional` - `pytrm.transactional_with`. В нем можно указать имена атрибутов в которых содержатся менеджер транзакций и настройки для него, переопределить правило распространения транзакции (`propagation=`), а также указать исключения, при возникновении которых требуется фиксация изменений (commit), а не их откат (rollback). Если атрибут настроек компонента равен `None`, `propagation` применяется к настройкам по умолчанию менеджера транзакций. Для императивного стиля то же самое доступно через `trm.do(ctx, propagation=...)` и `settings.with_propagation(...)`.
