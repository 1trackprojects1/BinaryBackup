import datetime

import discord
from discord.ext import commands

from cogs import (
    errorhandler,
    helpcommand,
    management,
    serversaver,
)

from backend import get_token

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or('.'), case_insensitive=True)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.utils.oauth_url(bot.user.id))


errorhandler.setup(bot)
helpcommand.setup(bot)
management.setup(bot)
serversaver.setup(bot)
bot.run(get_token())
