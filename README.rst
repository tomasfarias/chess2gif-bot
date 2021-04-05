************
chess2gif-bot
************
A Discord bot to turn your chess games into GIFs! For now, it works with chess.com and lichess.org.

Usage
#####
Simply call the bot with your Discord token:
::
   chess-bot TOKEN

Alternatively, the token can be read from the environment using ``DISCORD_BOT_TOKEN``:
::
   DISCORD_BOT_TOKEN=TOKEN chess-bot

Commands
########

The bot doesn't have any commands but insteads listens to mentions. So, for example, to send a message containing Hikaru's last game from chess.com, simply do:
::
   @Chess2GIF player:hikaru

Alternatively, you can mention the bot with any game ID:
::
   @Chess2GIF id:1111111111

You can get any game ID from the game's URL:

- `chess.com <https://www.chess.com>`_: ``https://www.chess.com/game/live/{ID}``
- `lichess.org <https://www.lichess.org>`_: ``https://www.lichess.org/{ID}``
