"""Journal diário — garante um commit por dia e registra o progresso."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

JOURNAL = "CHANGELOG.md"
_ENTRY = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}): `(?P<task>[^`]+)`")


def today_str() -> str:
    return date.today().isoformat()


def _header() -> str:
    return (
        "# Changelog (gerado pelo github-autobot)\n\n"
        "Registro automático de melhorias progressivas. Um commit por dia.\n"
    )


def todays_task(root: Path, date_str: str) -> str | None:
    """Devolve o nome da tarefa já registrada para a data (ou None)."""
    path = root / JOURNAL
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _ENTRY.match(line)
        if m and m.group("date") == date_str:
            return m.group("task")
    return None


def append_entry(root: Path, task_name: str, improved: bool, dedupe: bool = False) -> None:
    path = root / JOURNAL
    if not path.exists():
        path.write_text(_header(), encoding="utf-8")
    elif dedupe:
        # não duplica entrada do dia; apenas garante que existe
        if todays_task(root, today_str()) is not None:
            return
    tag = "aplicada" if improved else "sem pendências (heartbeat)"
    line = f"- {today_str()}: `{task_name}` — {tag}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
