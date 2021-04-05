import asyncio
from pathlib import Path
import logging
import json
import functools
import re
import subprocess
import tempfile
import typing
import uuid

import discord
from discord.ext import commands

PGN_HEADER_PATTERN = r'(?<={header}\s\")([a-zA-Z\s0-9\-\/\.]*)'

class ChessGIF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Return the GIF of a chess game"""
        if message.author == self.bot.user:
            return

        if not self.bot.user.mentioned_in(message):
            return

        id_or_username, search_type = process_message(message)
        file_name = str(uuid.uuid4())
        _, output_path = tempfile.mkstemp(suffix=".gif", prefix=f"{file_name}")
        game_pgn, error = create_gif(id_or_username, search_type, output_path)
        if error is not None:
            await self.handle_subprocess_error(message, error)
            return

        embed, gif_file = make_gif_embed(game_pgn, Path(output_path))
        await message.channel.send(embed=embed, file=gif_file)


    async def handle_subprocess_error(self, message: discord.Message, error):
        logging.error("Processing: %s, failed with %s", message, error)
        await message.channel.send(f"I had trouble fetching your chess game")


def process_message(message) -> (str, str):
    """Handle messages sent to bot"""
    logging.info("Processing message: %s", message)
    content = message.clean_content.strip()

    if content.startswith("@Chess2GIF id:"):
        id_or_username = content.split(":")[1]
        search_type = "id"
    elif content.startswith("@Chess2GIF player:"):
        id_or_username = content.split(":")[1]
        search_type = "player"

    return id_or_username, search_type


def create_gif(id_or_username: str, search_type: str, output: Path=Path("chess.gif")) -> typing.Union[typing.Optional[str], typing.Optional[str]]:
    """Run cgf and c2g to create a chess GIF for the given game ID or player username"""
    game_pgn, error = get_game_pgn(id_or_username, search_type)
    if error is not None:
        return None, error

    logging.info("Saving game to: %s", output)
    proc = subprocess.run(["c2g", game_pgn, "-o", str(output)], capture_output=True)
    error = proc.stderr.decode("utf-8")
    if error != '':
        return None, error
    return game_pgn, None


def get_game_pgn(id_or_username: str, search_type: str) -> typing.Union[typing.Optional[dict], typing.Optional[str]]:
    if search_type == "id":
        proc = subprocess.run(["cgf", id_or_username, "--pgn"], capture_output=True)
    elif search_type == "player":
        proc = subprocess.run(["cgf", id_or_username, "--player", "--pgn"], capture_output=True)
    else:
        raise ValueError("search_type must be either \"id\" or \"player\"")

    error = proc.stderr.decode("utf-8")
    if error != '':
        return None, error

    return proc.stdout.decode("utf-8"), None


def make_gif_embed(pgn: str, gif_file_path: Path) -> (discord.Embed, discord.File):
    inline_headers = [
        "Date", "Result", "Termination",
    ]
    headers = [
        "White", "Black", "WhiteElo", "BlackElo"
    ]
    game = get_game_dict(pgn, headers + inline_headers)
    gif_file = discord.File(gif_file_path)

    title = "{white} ({white_rating}) ♔ vs {black} ({black_rating}) ♚".format(
        white=game.get("White", "Anonymous"),
        white_rating=game.get("WhiteElo", "N/A"),
        black=game.get("Black", "Anonymous"),
        black_rating=game.get("BlackElo", "N/A"),
    )
    embed = discord.Embed(title=title, color=discord.Color.green())

    for header in inline_headers:
        embed.add_field(name=header, value=game[header], inline=True)

    embed.set_image(url=f"attachment://{gif_file_path.name}")

    return embed, gif_file


def get_game_dict(pgn: str, headers: list[str]):
    result = {}
    for header in headers:
        match = re.search(
            PGN_HEADER_PATTERN.format(header=header),
            pgn,
            flags=re.IGNORECASE
        )
        if match is not None:
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
    await bot.change_presence(activity=discord.Activity(name="@Chess2GIF help", type=discord.ActivityType.listening))


bot.add_cog(ChessGIF(bot))
