# Трекер задач: GitHub

Задачи и спецификации этого репозитория живут как GitHub issues. Для всех операций используй `gh` CLI.

## Соглашения

- **Создать задачу**: `gh issue create --title "..." --body "..."`. Для многострочного тела используй heredoc.
- **Прочитать задачу**: `gh issue view <number> --comments`, фильтруя комментарии через `jq` и попутно забирая метки.
- **Список задач**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` с нужными фильтрами `--label` и `--state`.
- **Комментарий к задаче**: `gh issue comment <number> --body "..."`
- **Добавить / снять метки**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Закрыть**: `gh issue close <number> --comment "..."`

Репозиторий определяется из `git remote -v`; `gh` делает это автоматически при запуске внутри клона.

## Pull request'ы как поверхность триажа

**PR как источник запросов: нет.** _(Поставь `да`, если в этом репозитории внешние PR считаются заявками на фичи; `/triage` читает этот флаг.)_

При значении `да` PR проходят через те же метки и состояния, что и задачи, с использованием эквивалентов `gh pr`:

- **Прочитать PR**: `gh pr view <number> --comments`, а `gh pr diff <number>` — для диффа.
- **Список внешних PR для триажа**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`, затем оставить только `authorAssociation` из `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR` или `NONE` (отбросить `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Комментарий / метки / закрытие**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

У GitHub общее пространство номеров для issues и PR, поэтому голый `#42` может быть и тем, и другим: разрешай через `gh pr view 42` с откатом на `gh issue view 42`.

## Когда скилл говорит «опубликовать в трекер задач»

Создай GitHub issue.

## Когда скилл говорит «получить нужный тикет»

Выполни `gh issue view <number> --comments`.

## Операции wayfinding

Используются скиллом `/wayfinder`. **Карта** — это одна задача, а **дочерние** задачи — это тикеты.

- **Карта**: одна задача с меткой `wayfinder:map`, содержащая тело Notes / Decisions-so-far / Fog. `gh issue create --label wayfinder:map`.
- **Дочерний тикет**: задача, связанная с картой как GitHub sub-issue (`gh api` по эндпоинту sub-issues). Если sub-issues недоступны, добавь дочернюю задачу в task list в теле карты и поставь `Part of #<map>` в начало тела дочерней. Метки: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). После взятия в работу тикет назначается на ведущего разработчика.
- **Блокировки**: нативные **issue dependencies** GitHub — каноничное, видимое в UI представление. Ребро добавляется через `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, где `<blocker-db-id>` — числовой **database id** блокирующей задачи (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, а _не_ `#number` и не `node_id`). GitHub отдаёт `issue_dependencies_summary.blocked_by` (только открытые блокеры — это и есть живой гейт). Если dependencies недоступны, откатись на строку `Blocked by: #<n>, #<n>` в начале тела дочерней задачи. Тикет разблокирован, когда закрыты все блокеры.
- **Запрос фронтира**: перечисли открытые дочерние задачи карты (`gh issue list --state open`, ограниченный sub-issues / task list карты), отбрось те, у которых есть открытый блокер (`issue_dependencies_summary.blocked_by > 0` либо открытая задача в строке `Blocked by`) или назначенный исполнитель; побеждает первая в порядке карты.
- **Взять в работу**: `gh issue edit <n> --add-assignee @me` — первая запись в сессии.
- **Закрыть вопрос**: `gh issue comment <n> --body "<answer>"`, затем `gh issue close <n>`, затем добавь указатель на контекст (gist + ссылка) в Decisions-so-far карты.
