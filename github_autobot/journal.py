"""Journal diário — garante um commit por dia e registra o progresso."""

from __future__ import annotations

from datetime import date
from pathlib import Path

JOURNAL = "CHANGELOG.md"


def today_str() -> str:
    return date.today().isoformat()


def _header() -> str:
    return (
        "# Changelog (gerado pelo github-autobot)\n\n"
        "Registro automático de melhorias progressivas. Um commit por dia.\n"
    )


def append_entry(root: Path, task_name: str, improved: bool) -> None:
    path = root / JOURNAL
    if not path.exists():
        path.write_text(_header(), encoding="utf-8")
    tag = "aplicada" if improved else "sem pendências (heartbeat)"
    line = f"- {today_str()}: `{task_name}` — {tag}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
