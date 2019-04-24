import datetime

import discord
from discord.ext import commands


from backend import (
    get_permitted,
    get_token
)


class ServerManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sortchannels(self, ctx):
        """Sorts channels alphabetically"""
        if ctx.guild is None:
            return
        channel_dict = {}
        channels = []
        await ctx.send("Sorting channels alphabetically!")
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.channel.CategoryChannel):
                continue
            channel_dict[channel.id] = channel.category
            channels.append(channel.name)

        channels.sort()

        append_text = ""
        for index, channel in enumerate(channels):
            try:
                channel = discord.utils.get(ctx.message.channel.guild.channels,
                                            name=channel)
                await channel.edit(position=index)
            except Exception:
                append_text += f"Could not move {channel.name}\n"
        await ctx.send(f"Finished sorting channels!\n{append_text}")

    @commands.command()
    async def invite(self, ctx):
        """Gives invite to the support guild and gives link to invite the bot"""
        await ctx.send(embed=discord.Embed(colour=discord.Colour(0xffffff), timestamp=datetime.datetime.utcnow())
                       .set_author(name=f"BinaryBackup", url="http://binarybackup.io/", icon_url=f"{self.bot.user.avatar_url}")
                       .set_footer(text="BinaryBackup by Mehodin#0001", icon_url=f"{self.bot.user.avatar_url}")
                       .add_field(name="Guild Invite:", value="http://binarybackup.io/")
                       .add_field(name="Bot Invite", value=f"{discord.utils.oauth_url(self.bot.user.id)}&permissions=8"))

    @commands.command(hidden=True)
    async def logout(self, ctx):
        if ctx.message.author.id not in get_permitted():
            return
        try:
            await ctx.send('Logging out bot!')
            await self.bot.close()
        except BaseException:
            pass

    def __chunkIt(self, seq, num):
        avg = len(seq) / float(num)
        last = 0
        while last < len(seq):
            yield seq[int(last):int(last + avg)]
            last += avg


def setup(bot):
    bot.add_cog(ServerManager(bot))
