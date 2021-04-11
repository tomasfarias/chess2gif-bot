from pathlib import Path
import subprocess

import discord
from discord.ext import commands
import pytest

from chess_bot.bot import (
    process_message,
    create_gif,
    make_gif_embed,
    extract_game_headers,
    get_game_pgn,
    is_valid_message,
    tmp_file_path,
)


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


SAMPLE_PGN_1 = """
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

SAMPLE_PGN_2 = """
[Event "Live Chess"]
[Site "Chess.com"]
[Date "2021.03.11"]
[Round "-"]
[White "SXSH-2021"]
[Black "pepegasacrifice"]
[Result "0-1"]
[CurrentPosition "6k1/5pb1/4p1p1/6Pr/p7/6KP/8/8 w - -"]
[Timezone "UTC"]
[ECO "D20"]
[ECOUrl "https://www.chess.com/openings/Queens-Gambit-Accepted-3.Nc3-Nf6"]
[UTCDate "2021.03.11"]
[UTCTime "08:30:14"]
[WhiteElo "1286"]
[BlackElo "1402"]
[TimeControl "60"]
[Termination "pepegasacrifice won on time"]
[StartTime "08:30:14"]
[EndDate "2021.03.11"]
[EndTime "08:32:22"]
[Link "https://www.chess.com/game/live/9190563687"]

1. d4 {[%clk 0:00:59.9]} 1... d5 {[%clk 0:00:59.9]} 2. c4 {[%clk 0:00:58.1]} 2... Nf6 {[%clk 0:00:59.5]} 3. Nc3 {[%clk 0:00:57.9]} 3... dxc4 {[%clk 0:00:58.5]} 4. f3 {[%clk 0:00:57.7]} 4... g6 {[%clk 0:00:58.1]} 5. e4 {[%clk 0:00:56.8]} 5... Bg7 {[%clk 0:00:57.8]} 6. Bxc4 {[%clk 0:00:55.7]} 6... O-O {[%clk 0:00:56.9]} 7. e5 {[%clk 0:00:54.9]} 7... Nfd7 {[%clk 0:00:53]} 8. Nge2 {[%clk 0:00:53.4]} 8... a6 {[%clk 0:00:52.1]} 9. O-O {[%clk 0:00:52.6]} 9... b5 {[%clk 0:00:51.4]} 10. Bb3 {[%clk 0:00:52.5]} 10... a5 {[%clk 0:00:50.1]} 11. Nxb5 {[%clk 0:00:50.8]} 11... a4 {[%clk 0:00:49.1]} 12. Bc4 {[%clk 0:00:49]} 12... c6 {[%clk 0:00:47.4]} 13. Nbc3 {[%clk 0:00:48.2]} 13... Ba6 {[%clk 0:00:44.3]} 14. Bxa6 {[%clk 0:00:46.8]} 14... Nxa6 {[%clk 0:00:44.1]} 15. Ng3 {[%clk 0:00:46.4]} 15... Nb4 {[%clk 0:00:43.4]} 16. d5 {[%clk 0:00:46.3]} 16... Nxd5 {[%clk 0:00:42.4]} 17. Nxd5 {[%clk 0:00:46]} 17... cxd5 {[%clk 0:00:41.8]} 18. Qxd5 {[%clk 0:00:45.6]} 18... Nxe5 {[%clk 0:00:40.9]} 19. Qxd8 {[%clk 0:00:40.9]} 19... Rfxd8 {[%clk 0:00:39.6]} 20. f4 {[%clk 0:00:40.6]} 20... Ng4 {[%clk 0:00:38.3]} 21. f5 {[%clk 0:00:39.1]} 21... Bd4+ {[%clk 0:00:36.4]} 22. Kh1 {[%clk 0:00:35.7]} 22... Ne3 {[%clk 0:00:36.3]} 23. Bxe3 {[%clk 0:00:32.9]} 23... Bxe3 {[%clk 0:00:36.1]} 24. fxg6 {[%clk 0:00:32.5]} 24... hxg6 {[%clk 0:00:35.5]} 25. Ne4 {[%clk 0:00:29.3]} 25... Bh6 {[%clk 0:00:34.8]} 26. Nc5 {[%clk 0:00:27.7]} 26... Bg7 {[%clk 0:00:34]} 27. Nb7 {[%clk 0:00:25.7]} 27... Rdb8 {[%clk 0:00:33]} 28. Nc5 {[%clk 0:00:23.3]} 28... Rxb2 {[%clk 0:00:32.3]} 29. Rad1 {[%clk 0:00:22.9]} 29... Rab8 {[%clk 0:00:31.3]} 30. Nd7 {[%clk 0:00:21]} 30... Rd8 {[%clk 0:00:30.1]} 31. Rf3 {[%clk 0:00:19.2]} 31... Rbb8 {[%clk 0:00:27.4]} 32. Rh3 {[%clk 0:00:18]} 32... Rbc8 {[%clk 0:00:25.9]} 33. a3 {[%clk 0:00:16.5]} 33... e6 {[%clk 0:00:24]} 34. Rdd3 {[%clk 0:00:14.9]} 34... Bb2 {[%clk 0:00:22.9]} 35. g3 {[%clk 0:00:11.8]} 35... Rc3 {[%clk 0:00:21.8]} 36. Rxc3 {[%clk 0:00:09.9]} 36... Bxc3 {[%clk 0:00:21.2]} 37. Kg2 {[%clk 0:00:09]} 37... Rxd7 {[%clk 0:00:20.5]} 38. g4 {[%clk 0:00:08.1]} 38... Rd2+ {[%clk 0:00:19.8]} 39. Kf3 {[%clk 0:00:07.7]} 39... Bg7 {[%clk 0:00:19.5]} 40. Rh4 {[%clk 0:00:05.9]} 40... Rb2 {[%clk 0:00:19.2]} 41. Ke4 {[%clk 0:00:04.2]} 41... Rb3 {[%clk 0:00:18.2]} 42. h3 {[%clk 0:00:03.9]} 42... Rxa3 {[%clk 0:00:17.7]} 43. Kf4 {[%clk 0:00:02.3]} 43... Rc3 {[%clk 0:00:17.2]} 44. g5 {[%clk 0:00:02.1]} 44... Rc4+ {[%clk 0:00:16.4]} 45. Kf3 {[%clk 0:00:01.9]} 45... Rxh4 {[%clk 0:00:16]} 46. Kg3 {[%clk 0:00:00.2]} 46... Rh5 {[%clk 0:00:15.5]} 0-1
"""  # noqa


@pytest.mark.execs
@missingcgf
def test_get_game_pgn_with_id():
    pgn, error = get_game_pgn("11219006649", search_type="id")
    # Don't really care about extra whitespace or quotes
    assert error is None
    assert clean_str(pgn) == clean_str(SAMPLE_PGN_1)


def clean_str(s: str) -> str:
    return s.replace("\n", "").replace(" ", "").replace("'", "")


def test_extract_game_headers_with_pgn_1():
    headers = ["Termination", "Result", "Date", "White", "Black", "WhiteElo", "BlackElo"]
    game_dict = extract_game_headers(SAMPLE_PGN_1, headers)

    assert [k for k in game_dict.keys()] == headers
    assert game_dict["Result"] == "1/2-1/2"
    assert game_dict["Black"] == "Hikaru"
    assert game_dict["Date"] == "2021.04.03"
    assert game_dict["Termination"] == "Game drawn by timeout vs insufficient material"


def test_extract_game_headers_with_pgn_2():
    headers = ["Termination", "Result", "Date", "White", "Black", "WhiteElo", "BlackElo"]
    game_dict = extract_game_headers(SAMPLE_PGN_2, headers)

    assert [k for k in game_dict.keys()] == headers
    assert game_dict["Result"] == "0-1"
    assert game_dict["Black"] == "pepegasacrifice"
    assert game_dict["Date"] == "2021.03.11"
    assert game_dict["Termination"] == "pepegasacrifice won on time"


def test_make_gif_embed(tmp_path):
    d = tmp_path / "gif"
    d.mkdir()
    p = d / "test.gif"
    p.write_text("some text")
    embed, gif_file = make_gif_embed(SAMPLE_PGN_1, p)

    assert embed.title == "liczner (2836) ♔ vs Hikaru (3205) ♚"
    assert any(f.name == "Date" for f in embed.fields)
    assert any(f.name == "Result" for f in embed.fields)
    assert any(f.name == "Termination" for f in embed.fields)
    assert embed.image.url == "attachment://test.gif"


class FakeMessage:
    def __init__(self, content):
        self.clean_content = content
        self.author = None
        self.mention_everyone = False
        self.mentions = []


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


USER_DATA = {
    "username": "a-user",
    "id": "0",
    "discriminator": "#123",
    "avatar": "N/A",
}

BOT_USER_DATA = {
    "username": "@Chess2GIF",
    "id": "1",
    "discriminator": "#123",
    "avatar": "N/A",
    "bot": True,
    "system": False,
}


def test_is_valid_message():
    message = FakeMessage("@Chess2GIF player:hikaru")
    user = discord.ClientUser(state={}, data=USER_DATA)
    bot = discord.ClientUser(state={}, data=BOT_USER_DATA)
    message.mentions = [bot]
    message.author = user

    check, error = is_valid_message(message, bot_user=bot)
    assert check is True
    error is None


def test_is_not_valid_message_by_bot():
    """If the bot wrote the message, we should ignore it"""
    bot = discord.ClientUser(state={}, data=BOT_USER_DATA)
    message = FakeMessage("@Chess2GIF player:hikaru")
    message.mentions = [bot]
    message.author = bot

    check, error = is_valid_message(message, bot_user=bot)
    assert check is False
    error is None


def test_is_not_valid_message_has_help():
    message = FakeMessage("@Chess2GIF help")
    user = discord.ClientUser(state={}, data=USER_DATA)
    bot = discord.ClientUser(state={}, data=BOT_USER_DATA)
    message.mentions = [bot]
    message.author = user

    check, error = is_valid_message(message, bot_user=bot)
    assert check is False
    error is not None


def test_is_not_valid_message_malformed_message():
    message = FakeMessage("@Chess2GIF malformed message")
    user = discord.ClientUser(state={}, data=USER_DATA)
    bot = discord.ClientUser(state={}, data=BOT_USER_DATA)
    message.mentions = [bot]
    message.author = user

    check, error = is_valid_message(message, bot_user=bot)
    assert check is False
    error is not None


def test_tmp_file_path():
    a_file = "file.gif"
    assert not Path(a_file).exists()
    with tmp_file_path(a_file) as p:
        assert Path(a_file) == p
        assert not p.exists()
        p.write_text("some text")
        assert p.exists()
    assert not Path(a_file).exists()
