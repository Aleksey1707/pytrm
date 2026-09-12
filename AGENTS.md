# Инструкции агентам

Файл общий для агентов; `CLAUDE.md` — симлинк на него.

## Язык и тон

- Отвечай строго на русском.
- Сразу дай решение (код/diff), объяснение — только если без него нельзя понять правку.
- Исключи вводные фразы («вот решение», «пожалуйста», «конечно»), извинения, воду, мораль.
- Тон — технический, лаконичный.

## Стиль кода и формат вывода

- Минимальный diff: не переписывать код целиком без запроса.
- Формат правки: либо `diff -u` (без лишних строк), либо инлайн: «строка X: было → стало».
- Не добавляй комментарии, примеры использования, не трогай неиспользуемый код вне зоны задачи.

## Допущения и риски

- Если чего-то не хватает в задаче — явно укажи: «допущение: <кратко, 1 строка>, риск: <низкий/средний/высокий>».
- Если риск средний/высокий — не применяй допущение без подтверждения пользователя.

## Что это

`pytrm` — менеджер транзакций как абстракция доступа к БД: вольная адаптация идеи
go-transaction-manager для Python. Инфраструктурная деталь (сессия, нативная транзакция,
pipeline) прячется в неизменяемый **контекст**, а менять контекст вправе только **менеджер
контекста**. Прикладной код видит реализацию `TransactionManager`, функции
`get_native_transaction` / `find_native_transaction` и декораторы `transactional` /
`transactional_with`.

Ядро (`share.py`, `bases.py`) не знает ни про один драйвер; всё, что знает, живёт в
`pytrm/impls/` за опциональными extras: SQLAlchemy, Redis, Mongo (motor и pymongo) и null.
Отсюда главный принцип: **прикладной код не знает про драйвер БД**, а новая БД добавляется
одним модулем реализации, не трогая ядро.

Поддерживаются Python 3.9–3.14; вся работа с транзакцией асинхронная.

## Правила проекта

Свод правил лежит в `docs/rules/*.md` и обязателен к соблюдению. Всегда в контексте —
только соглашения по коду (импорт ниже; если импорт не поддержан — прочитай файл первым):

@docs/rules/20-agreements.md

Остальные своды подключаются по задаче: у каждого есть одноимённый skill, который грузит
файл целиком. Skill выбирает модель — если правишь слой, а свод не подтянулся, читай файл сам.

| Файл | Skill | Тема |
|---|---|---|
| `docs/rules/10-architecture.md` | `architecture` | слои и граф импортов, публичный API, неизменяемость контекста, `Registry`, DI, декораторы |
| `docs/rules/11-propagation.md` | `propagation` | семь правил `Propagation`, владение транзакцией, `exclude`, вложенность |
| `docs/rules/12-errors.md` | `errors` | иерархия `BaseTrmException`, `default_message`, контракт `:raises` |
| `docs/rules/13-impls.md` | `impls` | обёртка `Transaction`, менеджер и `create`, extras и подключение новой БД |
| `docs/rules/19-testing.md` | `testing` | обвязка `tests/`, общие наборы, маркер `integration`, покрытие |
| `docs/rules/20-agreements.md` | — (всегда) | CQS, `get` / `find`, иерархия классов, аннотации, правило понижения, пайплайн |
| `docs/rules/00-index.md` | — | карта свода, словари плейсхолдеров и модальности, стандарт оформления |
| `docs/rules/DEBT.md` | — | осознанные отступления от сводов: что не чинится сейчас и почему |

Файл — источник истины, skill — только доставка. Правки вносятся в `docs/rules/*.md`;
`SKILL.md` трогать нужно, только если поменялось имя файла или область применения.
Форма самих файлов проверяется `make rules-check` (`scripts/rules_lint.py`).

## Команды

```bash
make                     # format → lint → test-fast
make rules-check         # свод docs/rules против стандарта 00-index.md
make lint                # rules-check + mypy + ruff format --check + ruff check
make format              # ruff format . + ruff check --fix .
make test-fast           # pytest -m "not integration" — без Docker
make test-integration    # только помеченные integration (нужен Docker/Podman)
make test                # tox -p auto по всем версиям Python
make cover               # покрытие: term-missing + htmlcov
make build               # uv build
uv run pytest tests/redis/test_redis_trm.py          # один файл
uv run pytest tests/redis/test_redis_trm.py::test_x  # один тест
uv run mypy                                          # проверка типов по pytrm и tests
uv run pre-commit run --all-files                    # хуки стадии commit
```

Интеграционные тесты поднимают контейнеры через `testcontainers`. `DOCKER_HOST` берётся
из окружения; `Makefile` и `tox.ini` подставляют запасной вариант поверх `XDG_RUNTIME_DIR`,
Ryuk по умолчанию отключён (переопределяется `TESTCONTAINERS_RYUK_DISABLED`).

## Agent skills

### Issue tracker

Задачи ведутся в GitHub Issues репозитория `Aleksey1707/pytrm` через `gh` CLI. См. `docs/agents/issue-tracker.md`.

### Triage labels

Пять канонических меток триажа без переименований. См. `docs/agents/triage-labels.md`.

### Domain docs

Одноконтекстный репозиторий: `CONTEXT.md` и `docs/adr/` в корне. См. `docs/agents/domain.md`.
