from __future__ import annotations

import asyncio
from pathlib import Path
import logging
import json
import functools
import re
import subprocess
import tempfile
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
        if message.author == self.bot.user:
            return

        content = message.clean_content.strip().split(" ")
        if len(content) >= 2 and content[1] == "help":  # Help messages handled by HelpCommand subclass
            return

        if not self.bot.user.mentioned_in(message):
            return

        id_or_username, search_type = process_message(message)
        file_name = str(uuid.uuid4())
        _, output_path = tempfile.mkstemp(suffix=".gif", prefix=f"{file_name}")
        game_pgn, error = create_gif(id_or_username, search_type, Path(output_path))
        if error is not None or game_pgn is None:
            await self.handle_subprocess_error(message, error)
            return

        embed, gif_file = make_gif_embed(game_pgn, Path(output_path))
        await message.channel.send(embed=embed, file=gif_file)

    async def handle_subprocess_error(self, message: discord.Message, error):
        logging.error("Processing: %s, failed with %s", message, error)
        await message.channel.send("I had trouble fetching your chess game")


def process_message(message: discord.Message) -> tuple[str, str]:
    """Handle messages sent to bot"""
    logging.info("Processing message: %s", message)
    content = message.clean_content.strip().split(" ")[1:]

    for arg in content:
        splitted = arg.split(":")
        key = splitted[0]
        value = splitted[1]

        if key == "id" or key == "player":
            search_type = key
            id_or_username = value

    return id_or_username, search_type


def create_gif(
    id_or_username: str, search_type: str, output: Path = Path("chess.gif")
) -> tuple[Optional[str], Optional[str]]:
    """Create a chess GIF for the given game ID or player username using c2g"""
    game_pgn, error = get_game_pgn(id_or_username, search_type)
    if error is not None or game_pgn is None:
        return None, error

    logging.info("Saving game to: %s", output)
    proc = subprocess.run(["c2g", game_pgn, "-o", str(output)], capture_output=True)
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
    inline_headers = [
        "Date",
        "Result",
        "Termination",
    ]
    headers = ["White", "Black", "WhiteElo", "BlackElo"]
    game = get_game_dict(pgn, headers + inline_headers)
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


def get_game_dict(pgn: str, headers: list[str]) -> dict[str, str]:
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
