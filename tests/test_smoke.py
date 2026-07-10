from github_autobot import __version__
from github_autobot.core import Bot
from pathlib import Path


def test_version():
    assert __version__


def test_bot_instantiates(tmp_path: Path):
    bot = Bot(tmp_path, [], "Test User", "test@example.com")
    assert bot.repo.root == tmp_path
