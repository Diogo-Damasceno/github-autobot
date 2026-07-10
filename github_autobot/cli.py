"""CLI do github-autobot.

Uso:
  python -m github_autobot            roda 1 rodada (commit diário)
  python -m github_autobot --dry      simula, não commita
  python -m github_autobot --install  instala systemd user timer (diário)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from github_autobot import core
from github_autobot.tasks import ALL_TASKS

AUTHOR_NAME = "Diogo Damasceno"
AUTHOR_EMAIL = "mitszukyo@gmail.com"


def _find_repo_root() -> Path:
    # o bot só opera dentro do próprio repositório
    here = Path(__file__).resolve().parent
    # sobe até achar .git
    cur = here
    for _ in range(5):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return here.parent.parent  # fallback: raiz do projeto


def run(dry: bool = False) -> int:
    root = _find_repo_root()
    from github_autobot import journal
    date_str = journal.today_str()
    bot = core.Bot(root, ALL_TASKS, AUTHOR_NAME, AUTHOR_EMAIL)
    if dry:
        task = bot.pick_task(date_str)
        print(f"[dry] repo={root}")
        print(f"[dry] data={date_str}")
        print(f"[dry] próxima tarefa: {task.name if task else 'heartbeat'}")
        print(f"[dry] já aplicada: {task.applied(bot.repo) if task else 'n/a'}")
        return 0
    result = bot.run(date_str)
    print("result:", result)
    return 0 if result.get("committed") or result.get("note") else 0


def install_systemd() -> int:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    svc = unit_dir / "github-autobot.service"
    timer = unit_dir / "github-autobot.timer"
    # caminho absoluto ao python do sistema (leve, sem venv)
    py = sys.executable
    script = f'"{py}" -m github_autobot'
    # working dir = raiz do repo
    repo_root = _find_repo_root()
    svc.write_text(
        "[Unit]\n"
        "Description=github-autobot daily self-improvement\n"
        "[Service]\n"
        f"WorkingDirectory={repo_root}\n"
        f"ExecStart={script}\n"
        "Type=oneshot\n",
        encoding="utf-8",
    )
    timer.write_text(
        "[Unit]\n"
        "Description=Roda github-autobot diariamente\n"
        "[Timer]\n"
        "OnCalendar=*-*-* 18:30:00\n"
        "Persistent=true\n"
        "[Install]\n"
        "WantedBy=timers.target\n",
        encoding="utf-8",
    )
    print(f"Service: {svc}")
    print(f"Timer:   {timer}")
    print("Ative com: systemctl --user enable --now github-autobot.timer")
    return 0


def main_cli() -> int:
    ap = argparse.ArgumentParser(description="github-autobot")
    ap.add_argument("--dry", action="store_true", help="simula sem commitar")
    ap.add_argument("--install", action="store_true", help="instala systemd user timer")
    args = ap.parse_args()
    if args.install:
        return install_systemd()
    return run(dry=args.dry)


if __name__ == "__main__":
    raise SystemExit(main_cli())
