import datetime

import discord
from discord.ext import commands


class ErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=discord.Embed(
                color=0xFF0000,
                description=f"You're missing a required argument: `{error.param.name}`",
                timestamp=datetime.datetime.utcnow()))

        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(
                color=0xFF0000,
                description="You don't have permission to do that.",
                timestamp=datetime.datetime.utcnow()))

        if isinstance(error, commands.CommandOnCooldown):
            total = int('{:.0f}'.format(error.retry_after))
            minutes = total / 60
            seconds = total % 60
            if total > 60:
                return await ctx.send(embed=discord.Embed(
                    color=0xFF0000,
                    description=f'You are on cooldown. Try again in {round(minutes, 2)} minutes',
                    timestamp=datetime.datetime.utcnow()))
            await ctx.send(embed=discord.Embed(
                color=0xFF0000,
                description=f'You are on cooldown. Try again in {round(seconds, 2)} seconds',
                timestamp=datetime.datetime.utcnow()))

        else:
            await ctx.send(embed=discord.Embed(color=0xff0000,
                                               description=f"{error}",
                                               timestamp=datetime.datetime.utcnow()))


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
