from pathlib import Path
import subprocess

from discord.ext import commands
import pytest

from chess_bot.bot import process_message, create_gif

def command_not_available(command: str) -> bool:
    try:
        subprocess.check_call([command, "--help"])
    except OSError: # Raised when executable not found
        True
    return False

missingcgf = pytest.mark.skipif(
    command_not_available("cgf"), reason="cgf not available"
)
missingc2g = pytest.mark.skipif(
    command_not_available("c2g"), reason="c2g not available"
)

@pytest.mark.execs
@missingcgf
@missingc2g
def test_create_gif_with_player_name(tmp_path):
    d = tmp_path / "gif"
    d.mkdir()
    p = d / "test.gif"
    assert not p.is_file()

    _, error = create_gif("pepegasacrifice", "player", output=p)
    assert error is None
    assert p.is_file()


@pytest.mark.execs
@missingcgf
@missingc2g
def test_create_gif_with_game_id(tmp_path):
    d = tmp_path / "gif"
    d.mkdir()
    p = d / "test.gif"
    assert not p.is_file()

    _, error = create_gif("11219006649", "id", output=p)
    assert error is None
    assert p.is_file()


class FakeMessage:
    def __init__(self, content):
        self.clean_content = content

def test_process_message_with_id():
    message = FakeMessage("@Chess2GIF id:11219006649")
    _id, search_type = process_message(message)
    assert _id == "11219006649"
    assert search_type == "id"


def test_process_message_with_player_name():
    message = FakeMessage("@Chess2GIF player:hikaru")
    player, search_type = process_message(message)
    assert player == "hikaru"
    assert search_type == "player"
