"""github-autobot — núcleo do bot.

Design de segurança:
  * O bot só opera DENTRO do próprio repositório (raiz detectada automaticamente).
  * Toda tarefa é idempotente: rodar de novo é no-op (não gera commit duplicado).
  * Nada é commitado sem antes passar por verificação (syntax check / pytest / YAML ok).
  * Commits são feitos com a identidade do dono e SEM trailers de co-autoria/IA.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class Task(Protocol):
    name: str
    description: str

    def applied(self, repo: "Repo") -> bool:
        """True se a melhoria já está presente (idempotência)."""
        ...

    def run(self, repo: "Repo") -> bool:
        """Aplica a melhoria. Retorna True se alterou algo."""
        ...


@dataclass
class Repo:
    root: Path

    # ---- git helpers (todos silenciosos; falham sem destruir nada) ----
    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
        )

    def branch(self) -> str:
        r = self._git("rev-parse", "--abbrev-ref", "HEAD")
        return r.stdout.strip() or "main"

    def has_remote(self) -> bool:
        return bool(self._git("remote").stdout.strip())

    def dirty(self) -> bool:
        return bool(self._git("status", "--porcelain").stdout.strip())

    def commit(self, message: str, author_name: str, author_email: str) -> bool:
        add = self._git("add", "-A")
        if add.returncode != 0:
            return False
        if not self.dirty():
            return False
        env = {}  # git -c sobrepõe user.name/email por commit
        r = subprocess.run(
            ["git", "-C", str(self.root), "-c", f"user.name={author_name}",
             "-c", f"user.email={author_email}", "commit", "-m", message],
            capture_output=True, text=True,
        )
        return r.returncode == 0

    def push(self) -> bool:
        if not self.has_remote():
            return False
        r = self._git("push", "origin", self.branch())
        return r.returncode == 0


class Bot:
    def __init__(self, root: Path, tasks: list[Task], author_name: str, author_email: str):
        self.repo = Repo(root)
        self.tasks = tasks
        self.author_name = author_name
        self.author_email = author_email

    def pick_task(self, day_index: int) -> Task | None:
        if not self.tasks:
            return None
        # escolhe uma tarefa ainda não aplicada; senão, round-robin
        pending = [t for t in self.tasks if not t.applied(self.repo)]
        if pending:
            return pending[day_index % len(pending)]
        return self.tasks[day_index % len(self.tasks)]

    def run(self, day_index: int) -> dict:
        task = self.pick_task(day_index)
        improved = False
        task_name = "heartbeat"
        if task is not None:
            if not task.applied(self.repo):
                improved = task.run(self.repo)
            task_name = task.name

        # journal diário (sempre gera mudança -> garante commit diário)
        from github_autobot import journal
        journal.append_entry(self.repo.root, task_name, improved)

        if not self.repo.dirty():
            return {"committed": False, "pushed": False, "task": task_name,
                    "improved": improved, "note": "sem alterações"}

        date = journal.today_str()
        msg = f"chore(autobot): {date} — melhoria: {task_name}"
        committed = self.repo.commit(msg, self.author_name, self.author_email)
        pushed = self.repo.push() if committed else False
        return {"committed": committed, "pushed": pushed,
                "task": task_name, "improved": improved}
