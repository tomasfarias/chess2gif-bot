from pathlib import Path
import subprocess

from discord.ext import commands
import pytest

from chess_bot.bot import process_message, create_gif, make_gif_embed, get_game_dict, get_game_pgn


def command_not_available(command: str) -> bool:
    try:
        subprocess.check_call([command, "--help"])
    except OSError:  # Raised when executable not found
        True
    return False


missingcgf = pytest.mark.skipif(command_not_available("cgf"), reason="cgf not available")
missingc2g = pytest.mark.skipif(command_not_available("c2g"), reason="c2g not available")


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


SAMPLE_PGN = """
[Event Live Chess]
[Site Chess.com]
[Date 2021.04.03]
[White liczner]
[Black Hikaru]
[Result 1/2-1/2]
[CurrentPosition rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1]
[ECO B06]
[WhiteElo 2836]
[BlackElo 3205]
[TimeControl 180]
[EndTime 13:03:49 PDT]
[Termination Game drawn by timeout vs insufficient material]

1.e4 g6 2.d4 Bg7 3.Nf3 c6 4.Nc3 d5 5.h3 dxe4 6.Nxe4 Nf6 7.Nxf6+ exf6 8.Bc4 O-O 9.O-O Nd7 10.c3 b5 11.Bb3 Nb6 12.Re1 a5 13.a3 a4 14.Ba2 Re8 15.Bf4 Be6 16.Bxe6 Rxe6 17.Rxe6 fxe6 18.Qe2 Qd5 19.Re1 Re8 20.Nd2 Qd7 21.Ne4 Nd5 22.Bg3 Bf8 23.Qf3 Kg7 24.h4 h6 25.Re2 Qf7 26.Bd6 Be7 27.Bxe7 Rxe7 28.g3 g5 29.hxg5 hxg5 30.Nc5 f5 31.Re5 g4 32.Qe2 Kf6 33.Kg2 Qg8 34.Qd2 Qh8 35.Qe2 Qh3+ 36.Kg1 Rh7 37.Rxe6+ Kf7 38.Re7+ Kg6 39.Qe6+ Nf6 40.Rxh7 Qxh7 41.Nd3 Qg8 42.Ne5+ Kg5 43.Qxg8+ Nxg8 44.Nxc6 Nf6 45.Na7 Ne4 46.Nxb5 Nd2 47.d5 Kf6 48.d6 Nc4 49.d7 Ke7 50.Nd4 Nxb2 51.Nxf5+ Kxd7 52.Ne3 Ke6 53.Nxg4 Nc4 54.Ne3 Nxa3 55.f4 Nb1 56.Nc2 Kd5 57.Kf2 Ke4 58.Nb4 Nxc3 59.Ke1 Ke3 60.f5 Ne4 61.f6 Nc3 62.f7 Kd4 63.f8=Q Nb5 64.Qf4+ Kc3 65.Nc6 Nd4 66.Qxd4+ Kb3 67.Qxa4+ Kb2 68.Nd4 Kc3 69.Qb3+ Kxd4 70.Qc2 Kd5 1/2-1/2
"""  # noqa


@pytest.mark.execs
@missingcgf
def test_get_game_pgn_with_id():
    pgn, error = get_game_pgn("11219006649", search_type="id")
    # Don't really care about extra whitespace or quotes
    assert error is None
    assert clean_str(pgn) == clean_str(SAMPLE_PGN)


def clean_str(s: str) -> str:
    return s.replace("\n", "").replace(" ", "").replace("'", "")


def test_get_game_dict():
    headers = ["Termination", "Result", "Date", "White", "Black", "WhiteElo", "BlackElo"]
    game_dict = get_game_dict(SAMPLE_PGN, headers)

    assert [k for k in game_dict.keys()] == headers
    assert game_dict["Result"] == "1/2-1/2"
    assert game_dict["Black"] == "Hikaru"
    assert game_dict["Date"] == "2021.04.03"
    assert game_dict["Termination"] == "Game drawn by timeout vs insufficient material"


def test_make_gif_embed(tmp_path):
    d = tmp_path / "gif"
    d.mkdir()
    p = d / "test.gif"
    p.write_text("some text")
    embed, gif_file = make_gif_embed(SAMPLE_PGN, p)

    assert embed.title == "liczner (2836) ♔ vs Hikaru (3205) ♚"
    assert any(f.name == "Date" for f in embed.fields)
    assert any(f.name == "Result" for f in embed.fields)
    assert any(f.name == "Termination" for f in embed.fields)
    assert embed.image.url == "attachment://test.gif"


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
