"""Tarefas de melhoria progressiva (todas idempotentes e verificadas)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from github_autobot.core import Repo, Task


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


class AddCITask:
    name = "ci-github-actions"
    description = "Adiciona workflow de CI (lint + pytest) no GitHub Actions."

    def applied(self, repo: "Repo") -> bool:
        return (repo.root / ".github" / "workflows" / "ci.yml").exists()

    def run(self, repo: "Repo") -> bool:
        wf = (
            "name: CI\n"
            "on:\n"
            "  push:\n"
            "  pull_request:\n"
            "  schedule:\n"
            "    - cron: '0 6 * * *'\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: '3.11'\n"
            "      - name: Install\n"
            "        run: pip install -e . pytest ruff\n"
            "      - name: Lint\n"
            "        run: ruff check github_autobot || true\n"
            "      - name: Test\n"
            "        run: pytest -q\n"
        )
        return _write_if_absent(repo.root / ".github" / "workflows" / "ci.yml", wf)


class AddRuffConfigTask:
    name = "lint-ruff"
    description = "Garante configuração de lint (ruff) no pyproject."

    def applied(self, repo: "Repo") -> bool:
        p = repo.root / "pyproject.toml"
        return p.exists() and "[tool.ruff]" in p.read_text(encoding="utf-8")

    def run(self, repo: "Repo") -> bool:
        p = repo.root / "pyproject.toml"
        if not p.exists() or "[tool.ruff]" in p.read_text(encoding="utf-8"):
            return False
        p.write_text(
            p.read_text(encoding="utf-8") + "\n\n[tool.ruff]\nline-length = 100\n",
            encoding="utf-8",
        )
        return True


class AddBadgesTask:
    name = "readme-badges"
    description = "Insere badges de CI/license/versão no topo do README."

    def applied(self, repo: "Repo") -> bool:
        r = repo.root / "README.md"
        return r.exists() and "img.shields.io" in r.read_text(encoding="utf-8")

    def run(self, repo: "Repo") -> bool:
        r = repo.root / "README.md"
        if not r.exists():
            return False
        text = r.read_text(encoding="utf-8")
        if "img.shields.io" in text:
            return False
        badges = (
            "[![CI](https://github.com/Diogo-Damasceno/github-autobot/actions/workflows/ci.yml/badge.svg)]"
            "(https://github.com/Diogo-Damasceno/github-autobot/actions)\n"
            "[![License](https://img.shields.io/badge/license-MIT-green.svg)]"
            "(https://opensource.org/licenses/MIT)\n\n"
        )
        r.write_text(badges + text, encoding="utf-8")
        return True


class AddSmokeTestTask:
    name = "smoke-tests"
    description = "Adiciona teste de fumaça que importa o pacote e exercita o Bot."

    def applied(self, repo: "Repo") -> bool:
        return (repo.root / "tests" / "test_smoke.py").exists()

    def run(self, repo: "Repo") -> bool:
        t = (
            "from github_autobot import __version__\n"
            "from github_autobot.core import Bot\n"
            "from pathlib import Path\n"
            "\n"
            "\n"
            "def test_version():\n"
            "    assert __version__\n"
            "\n"
            "\n"
            "def test_bot_instantiates(tmp_path: Path):\n"
            "    bot = Bot(tmp_path, [], 'Test User', 'test@example.com')\n"
            "    assert bot.repo.root == tmp_path\n"
        )
        return _write_if_absent(repo.root / "tests" / "test_smoke.py", t)


class ReadmeUsageTask:
    name = "readme-usage"
    description = "Adiciona seção de uso/agendamento ao README."

    def applied(self, repo: "Repo") -> bool:
        r = repo.root / "README.md"
        return r.exists() and "## Uso" in r.read_text(encoding="utf-8")

    def run(self, repo: "Repo") -> bool:
        r = repo.root / "README.md"
        if not r.exists() or "## Uso" in r.read_text(encoding="utf-8"):
            return False
        section = (
            "\n## Uso\n\n"
            "```bash\n"
            "python -m github_autobot          # roda uma rodada (1 commit diário)\n"
            "python -m github_autobot --dry    # simula, não commita\n"
            "python -m github_autobot --install # instala systemd user timer (diário)\n"
            "```\n\n"
            "O bot é **idempotente**: tarefas já aplicadas viram no-op. "
            "Todo dia ele escolhe a próxima melhoria pendente e gera um commit + push (se houver remote).\n"
        )
        r.write_text(r.read_text(encoding="utf-8") + section, encoding="utf-8")
        return True


ALL_TASKS = [
    AddCITask(),
    AddRuffConfigTask(),
    AddBadgesTask(),
    AddSmokeTestTask(),
    ReadmeUsageTask(),
]
