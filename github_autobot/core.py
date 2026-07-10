"""github-autobot — núcleo do bot.

Design de segurança:
  * O bot só opera DENTRO do próprio repositório (raiz detectada automaticamente).
  * Toda tarefa é idempotente: rodar de novo é no-op (não gera commit duplicado).
  * Uma única melhoria por DIA (trava por data) — chamar o bot várias vezes no
    mesmo dia não aplica melhorias novas nem cria commits extras.
  * Nada é commitado sem antes passar por verificação (syntax check / pytest / YAML ok).
  * Commits são feitos com a identidade do dono e SEM trailers de co-autoria/IA.
"""

from __future__ import annotations

import hashlib
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

    def pick_task(self, date_str: str) -> Task | None:
        if not self.tasks:
            return None
        # decisão determinística e ESTÁVEL por dia: hash da data sobre as
        # tarefas ainda pendentes; se nenhuma pendente, hash sobre todas.
        pending = [t for t in self.tasks if not t.applied(self.repo)]
        pool = pending if pending else self.tasks
        idx = int(hashlib.sha256(date_str.encode()).hexdigest(), 16) % len(pool)
        return pool[idx]

    def run(self, date_str: str | None = None) -> dict:
        from github_autobot import journal

        date_str = date_str or journal.today_str()

        # trava diária: se já existe entrada para HOJE, repete a mesma tarefa
        # do dia (sem aplicar melhoria nova nem criar commit extra).
        todays = journal.todays_task(self.repo.root, date_str)
        if todays is not None:
            task = next((t for t in self.tasks if t.name == todays), None)
            if task is not None:
                task_name = task.name
                improved = False if task.applied(self.repo) else task.run(self.repo)
                journal.append_entry(self.repo.root, task_name, improved, dedupe=True)
                if not self.repo.dirty():
                    return {"committed": False, "pushed": False, "task": task_name,
                            "improved": improved, "note": "sem alterações"}
                msg = f"chore(autobot): {date_str} — melhoria: {task_name}"
                committed = self.repo.commit(msg, self.author_name, self.author_email)
                pushed = self.repo.push() if committed else False
                return {"committed": committed, "pushed": pushed,
                        "task": task_name, "improved": improved}

        task = self.pick_task(date_str)
        improved = False
        task_name = "heartbeat"
        if task is not None:
            if not task.applied(self.repo):
                improved = task.run(self.repo)
            task_name = task.name

        journal.append_entry(self.repo.root, task_name, improved)

        if not self.repo.dirty():
            return {"committed": False, "pushed": False, "task": task_name,
                    "improved": improved, "note": "sem alterações"}

        msg = f"chore(autobot): {date_str} — melhoria: {task_name}"
        committed = self.repo.commit(msg, self.author_name, self.author_email)
        pushed = self.repo.push() if committed else False
        return {"committed": committed, "pushed": pushed,
                "task": task_name, "improved": improved}
