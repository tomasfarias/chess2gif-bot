from __future__ import annotations

import asyncio
from contextlib import contextmanager
import functools
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Optional
import uuid

import discord
from discord.ext import commands

PGN_HEADER_PATTERN = r"((?<=\[{header}\s\")|(?<=\[{header}\s))([a-zA-Z\s0-9\-\/\.]+)"


class Chess2GIF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Return the GIF of a chess game"""
        check, error = is_valid_message(message, self.bot.user)
        if check is False:
            if error is not None:
                # Communicate to the user if there is an error because, apparently,
                # the message was not supposed to be ignored.
                await self.handle_message_not_valid_error(message, error)
            return

        args = process_message(message)
        file_name = str(uuid.uuid4())

        with tmp_file_path(f"{file_name}.gif") as output_path:
            game_pgn, error = create_gif(args, output_path)

            if error is not None or game_pgn is None:
                await self.handle_subprocess_error(message, error)
                return

            embed, gif_file = make_gif_embed(game_pgn, Path(output_path))
            await message.channel.send(embed=embed, file=gif_file)

    async def handle_message_not_valid_error(self, message: discord.Message, error: str):
        """Handle errors related to potential wrongful invocations of the bot"""
        logging.error("Not valid message: %s, failed with %s", message, error)
        await message.channel.send(error)

    async def handle_subprocess_error(self, message: discord.Message, error: Optional[str]):
        """Handle errors related to c2g or cgf failing"""
        logging.error("Processing: %s, failed with %s", message, error)
        await message.channel.send("I could not find your chess game")


@contextmanager
def tmp_file_path(name):
    """Return a file path that will be deleted after it's used (if it's used)"""
    path = Path(name)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def is_valid_message(
    message: discord.Message, bot_user: discord.ClientUser
) -> tuple[Optional[bool], Optional[str]]:
    """Check if the message is valid to be processed by the bot"""
    if message.author == bot_user:
        # Ignore messages by a bot
        return False, None

    if not bot_user.mentioned_in(message):
        # Ignore messages that do not mention the bot
        return False, None

    if message.mention_everyone is True:
        # Ignore messages that mention everyone
        return False, None

    content = message.clean_content.strip().split(" ")
    if len(content) == 2 and content[1] == "help":
        # Help messages handled by help command
        return False, None

    if not any(part.startswith("id:") or part.startswith("player:") for part in content):
        # All calls to the bot should contain "id:" or "player:"
        # so this is probably a user error
        return (
            False,
            'Messages must contain "id" or "player", request help for more information: @Chess2GIF help',
        )

    return True, None


def process_message(message: discord.Message) -> dict[str, str]:
    """Handle messages sent to bot"""
    logging.info("Processing message: %s", message)
    content = message.clean_content.strip().split(" ")[1:]
    args = {}

    for arg in content:
        splitted = arg.split(":")
        key = splitted[0]
        value = splitted[1]

        if key == "id" or key == "player":
            args["search_type"] = key
            args["id_or_username"] = value

        if key == "time":
            args["time"] = value

    return args


def create_gif(args: dict[str, str], output: Path = Path("chess.gif")) -> tuple[Optional[str], Optional[str]]:
    """Create a chess GIF for the given game ID or player username using c2g"""
    id_or_username, search_type = args["id_or_username"], args["search_type"]
    game_pgn, error = get_game_pgn(id_or_username, search_type)
    if error is not None or game_pgn is None:
        return None, error

    game = extract_game_headers(game_pgn, ["Black"])

    delay = None
    if "time" in args.keys():
        time = args["time"]
        if time != "real":
            delay = "--delay=" + str(time)
        else:
            delay = "--delay=real"

    logging.info("Saving game to: %s", output)
    c2g_args = ["c2g", game_pgn, "-o", str(output)]
    if delay is not None:
        c2g_args.append(delay)

    if game.get("Black", "") == id_or_username:
        # Flip the board if the username is playing as black
        c2g_args.append("--flip")

    proc = subprocess.run(c2g_args, capture_output=True)
    error = proc.stderr.decode("utf-8")
    if error != "":
        return None, error
    return game_pgn, None


def get_game_pgn(id_or_username: str, search_type: str) -> tuple[Optional[str], Optional[str]]:
    """Runs cgf to get a PGN for a chess game"""
    if search_type == "id":
        proc = subprocess.run(["cgf", id_or_username, "--pgn"], capture_output=True)
    elif search_type == "player":
        proc = subprocess.run(["cgf", id_or_username, "--player", "--pgn"], capture_output=True)
    else:
        raise ValueError('search_type must be either "id" or "player"')

    error = proc.stderr.decode("utf-8")
    if error != "":
        return None, error

    return proc.stdout.decode("utf-8"), None


def make_gif_embed(pgn: str, gif_file_path: Path) -> tuple[discord.Embed, discord.File]:
    """Create a discord.Embed with a Chess GIF File"""
    inline_headers = [
        "Date",
        "Result",
        "Termination",
    ]
    headers = ["White", "Black", "WhiteElo", "BlackElo"]
    game = extract_game_headers(pgn, headers + inline_headers)
    gif_file = discord.File(gif_file_path)

    title = "{white} ({white_rating}) ♔ vs {black} ({black_rating}) ♚".format(
        white=game.get("White", "Anonymous"),
        white_rating=game.get("WhiteElo", "N/A"),
        black=game.get("Black", "Anonymous"),
        black_rating=game.get("BlackElo", "N/A"),
    )
    logging.info("Creating embed: %s", title)
    embed = discord.Embed(title=title, color=discord.Color.green())
    for header in inline_headers:
        value = game.get(header)
        logging.debug("Adding header: %s, %s", header, value)
        if value is not None:
            embed.add_field(name=header, value=game[header], inline=True)

    embed.set_image(url=f"attachment://{gif_file_path.name}")

    return embed, gif_file


def extract_game_headers(pgn: str, headers: list[str]) -> dict[str, str]:
    """Extract headers from a PGN string"""
    logging.debug("Processing PGN: %s", pgn)
    result = {}

    for header in headers:
        logging.debug("Finding header: %s", PGN_HEADER_PATTERN.format(header=header))
        match = re.search(PGN_HEADER_PATTERN.format(header=header), pgn, flags=re.IGNORECASE)
        if match is not None:
            logging.debug("Header found: %s", match)
            result[header] = match.group()

    return result


bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    description="Turn your chess games into GIFs!",
    help=commands.DefaultHelpCommand(),
)


@bot.event
async def on_ready():
    logging.info("Connected as %s", bot.user)
    await bot.change_presence(
        activity=discord.Activity(name="@Chess2GIF help", type=discord.ActivityType.listening)
    )


bot.add_cog(Chess2GIF(bot))
