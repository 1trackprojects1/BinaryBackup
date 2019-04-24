import discord
from discord.ext import commands

import datetime


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def _help(self, ctx):
        await ctx.send(
            embed=discord.Embed(colour=discord.Colour(0xeb6123),
                                description="Click [here](http://binarybackup.io/help.html) for help!",
                                timestamp=datetime.datetime.utcnow())
            .set_author(name=f"{ctx.author.name}",
                        url="http://binarybackup.io/help.html",
                        icon_url=f"{ctx.author.avatar_url}")
            .set_footer(text=f"BinaryBackup by Mehodin#0001",
                        icon_url=f"{self.bot.user.avatar_url}")
        )


def setup(bot):
    bot.remove_command("help")
    bot.add_cog(Help(bot))
