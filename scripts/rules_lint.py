"""Проверка свода docs/rules против стандарта из 00-index.md.

Запуск: ``make rules-check`` либо ``uv run python scripts/rules_lint.py``.
"""

import re
import sys
from pathlib import Path
from typing import Iterator, List, NamedTuple, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "docs" / "rules"
SKILLS_DIR = ROOT / ".claude" / "skills"
AGENTS_FILE = ROOT / "AGENTS.md"

MAX_PROSE_LEN = 100

# Своды без шапки из трёх пунктов: реестр долга ведётся в свободной форме.
WITHOUT_HEADER = frozenset({"DEBT.md"})

# Своды без скилла: 00-index — карта, 20-agreements всегда в контексте, DEBT — реестр.
WITHOUT_SKILL = frozenset({"00-index.md", "20-agreements.md", "DEBT.md"})

HEADER_KEYS: Tuple[str, ...] = ("- **Область.**", "- **Читать перед.**", "- **Словарь.**")
LAST_SECTION = "## Связанные правила"
FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.*)$")
NAME_RE = re.compile(r"^name:\s*(?P<name>\S+)\s*$", re.MULTILINE)
DESCRIPTION_RE = re.compile(r"^description:\s*(?P<description>.+)$", re.MULTILINE)


class Problem(NamedTuple):
    """Найденное нарушение стандарта"""

    path: Path
    line: Optional[int]
    message: str

    def render(self) -> str:
        """
        Отрисовать нарушение одной строкой

        :return: строка вида ``путь:строка: сообщение``
        """
        where = "{}:{}".format(_relative(self.path), self.line) if self.line else _relative(self.path)
        return "{}: {}".format(where, self.message)


def main() -> int:
    """
    Проверить свод и напечатать найденные нарушения

    :return: код возврата процесса
    """
    rule_files = _rule_files()
    if not rule_files:
        print("rules-check: в docs/rules не найдено ни одного свода", file=sys.stderr)
        return 1

    problems: List[Problem] = []
    for path in rule_files:
        problems.extend(_check_file(path))

    problems.extend(_check_skills(rule_files))
    problems.extend(_check_maps(rule_files))

    for problem in problems:
        print(problem.render(), file=sys.stderr)

    if problems:
        print("rules-check: нарушений — {}".format(len(problems)), file=sys.stderr)
        return 1

    print("rules-check: свод в порядке ({} файлов)".format(len(rule_files)))
    return 0


def _rule_files() -> List[Path]:
    return sorted(p for p in RULES_DIR.glob("*.md"))


def _check_file(path: Path) -> List[Problem]:
    lines = path.read_text(encoding="utf-8").splitlines()

    problems: List[Problem] = []
    problems.extend(_check_headings(path, lines))
    problems.extend(_check_header(path, lines))
    problems.extend(_check_fences(path, lines))
    problems.extend(_check_last_section(path, lines))
    problems.extend(_check_line_length(path, lines))
    return problems


def _check_headings(path: Path, lines: Sequence[str]) -> Iterator[Problem]:
    h1_lines = []
    for number, line, in_fence in _walk(lines):
        if in_fence:
            continue

        match = HEADING_RE.match(line)
        if match is None:
            continue

        level = len(match.group("hashes"))
        if level == 1:
            h1_lines.append(number)
        elif level >= 4:
            yield Problem(path, number, "заголовок H{} — в своде допустимы только H1, H2 и H3".format(level))

    if not h1_lines:
        yield Problem(path, None, "нет заголовка H1")
    elif len(h1_lines) > 1:
        yield Problem(path, h1_lines[1], "второй заголовок H1 — в файле свода он MUST быть один")


def _check_header(path: Path, lines: Sequence[str]) -> Iterator[Problem]:
    if path.name in WITHOUT_HEADER:
        return

    header = _header_block(lines)
    for key in HEADER_KEYS:
        if not any(line.startswith(key) for line in header):
            yield Problem(path, None, "в шапке нет пункта `{}`".format(key))


def _header_block(lines: Sequence[str]) -> List[str]:
    block: List[str] = []
    seen_h1 = False
    for line in lines:
        if not seen_h1:
            seen_h1 = line.startswith("# ")
            continue

        if line.startswith("## "):
            break

        if line.strip():
            block.append(line)

    return block


def _check_fences(path: Path, lines: Sequence[str]) -> Iterator[Problem]:
    stack: List[str] = []
    for number, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if match is None:
            continue

        fence = match.group("fence")
        info = match.group("info").strip()

        if stack and _closes(stack[-1], fence) and not info:
            stack.pop()
            continue

        if stack:
            continue

        if not info:
            yield Problem(path, number, "у fenced-блока не указан язык")

        stack.append(fence)

    if stack:
        yield Problem(path, None, "незакрытый fenced-блок")


def _closes(opening: str, candidate: str) -> bool:
    return candidate[0] == opening[0] and len(candidate) >= len(opening)


def _check_last_section(path: Path, lines: Sequence[str]) -> Iterator[Problem]:
    sections = [line for _, line, in_fence in _walk(lines) if not in_fence and line.startswith("## ")]
    if not sections:
        yield Problem(path, None, "в файле нет ни одного H2")
        return

    if sections[-1].rstrip() != LAST_SECTION:
        yield Problem(path, None, "последний H2 — `{}`, ожидается `{}`".format(sections[-1].rstrip(), LAST_SECTION))


def _check_line_length(path: Path, lines: Sequence[str]) -> Iterator[Problem]:
    for number, line, in_fence in _walk(lines):
        if in_fence or len(line) <= MAX_PROSE_LEN:
            continue

        if line.lstrip().startswith("|"):
            continue

        if len(line.split()) < 2:
            continue

        yield Problem(path, number, "строка прозы длиннее {} символов ({})".format(MAX_PROSE_LEN, len(line)))


def _walk(lines: Sequence[str]) -> Iterator[Tuple[int, str, bool]]:
    """
    Пройти по строкам, помечая те, что лежат внутри fenced-блока

    :param lines: строки файла
    :return: тройки «номер строки, строка, внутри ли блока»
    """
    stack: List[str] = []
    for number, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if match is None:
            yield number, line, bool(stack)
            continue

        fence = match.group("fence")
        if stack and _closes(stack[-1], fence) and not match.group("info").strip():
            stack.pop()
        elif not stack:
            stack.append(fence)

        yield number, line, True


def _check_skills(rule_files: Sequence[Path]) -> Iterator[Problem]:
    for path in rule_files:
        if path.name in WITHOUT_SKILL:
            continue

        expected = _skill_name(path.name)
        skill_file = SKILLS_DIR / expected / "SKILL.md"
        if not skill_file.is_file():
            yield Problem(path, None, "нет скилла `.claude/skills/{}/SKILL.md`".format(expected))
            continue

        text = skill_file.read_text(encoding="utf-8")

        name_match = NAME_RE.search(text)
        if name_match is None or name_match.group("name").strip('"') != expected:
            yield Problem(skill_file, None, "во frontmatter нет `name: {}`".format(expected))

        description_match = DESCRIPTION_RE.search(text)
        if description_match is None or not description_match.group("description").strip('" '):
            yield Problem(skill_file, None, "во frontmatter нет непустого `description`")

        if path.name not in text:
            yield Problem(skill_file, None, "в теле нет ссылки на `docs/rules/{}`".format(path.name))


def _skill_name(file_name: str) -> str:
    return re.sub(r"^\d+-", "", file_name[: -len(".md")])


def _check_maps(rule_files: Sequence[Path]) -> Iterator[Problem]:
    index_file = RULES_DIR / "00-index.md"
    if not index_file.is_file():
        yield Problem(RULES_DIR, None, "нет карты свода `00-index.md`")
        return

    index_text = index_file.read_text(encoding="utf-8")
    agents_text = AGENTS_FILE.read_text(encoding="utf-8") if AGENTS_FILE.is_file() else ""

    for path in rule_files:
        if path.name not in index_text:
            yield Problem(index_file, None, "свод `{}` не указан в карте".format(path.name))

        if path.name in WITHOUT_SKILL - {"20-agreements.md"}:
            continue

        if path.name not in agents_text:
            yield Problem(AGENTS_FILE, None, "свод `{}` не указан в карте AGENTS.md".format(path.name))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
