import re
import io
import os
import json
import random
import asyncio
import datetime

import discord
from discord.ext import commands

from backend import get_permitted


class ServerSaver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.periodic_copy())
        if not os.path.isdir("saved_servers"):
            os.mkdir("saved_servers")

    def display_time(self, seconds, granularity=2):
        result = []
        intervals = (
            ('weeks', 604800),
            ('days', 86400),
            ('hours', 3600),
            ('minutes', 60),
            ('seconds', 1),
        )
        for name, count in intervals:
            value = seconds // count
            if not value:
                continue
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    @asyncio.coroutine
    async def periodic_copy(self):
        await self.bot.wait_until_ready()
        while True:
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f'{len(self.bot.guilds)} guilds!'))
            for guild in self.bot.guilds:
                try:
                    await self.copy(guild)
                except Exception as E:
                    await (guild.system_channel or random.choice(guild.text_channels)).send(f"Failed to back up guild:\n{E}")
            await asyncio.sleep(1800)

    @asyncio.coroutine
    async def copy(self, guild):
        data = {"bans": [],
                "roles": {},
                'members': [],
                'messages': {},
                "channels": {},
                "categories": {},
                'member_roles': {},
                "voice_channels": {}}

        for role in guild.roles:
            data["roles"][role.name] = {}
            role_data = data["roles"][role.name]
            role_data["permissions"] = role.permissions.value
            role_data["color"] = role.color.value
            role_data["position"] = role.position
            role_data["mentionable"] = role.mentionable
            role_data["hoisted"] = role.hoist

        bans = await guild.bans()

        for ban in bans:
            if ban[1] is None:
                continue
            data["bans"].append(ban[1].id)

        for member in guild.members:
            data['members'].append(member.id)

        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                data['messages'][channel.name] = []
                async for message in channel.history(limit=None):
                    if message.content in [None, '', 'None']:
                        for embed in message.embeds:
                            data['messages'][channel.name].append({
                                'embed': True,
                                'message': embed.to_dict()
                            })
                    else:
                        data['messages'][channel.name].append({
                            'embed': False,
                            'message': message.content,
                            'author': str(message.author),
                            'avatarUrl': str(message.author.avatar_url),
                            'timestamp': message.created_at.timestamp()
                        })
                data["channels"][channel.name] = {}
                channel_data = data["channels"][channel.name]
                channel_data["is_nsfw"] = channel.is_nsfw()
                channel_data["category"] = channel.category.name if channel.category else False
                channel_data["topic"] = channel.topic if channel.topic else ''

            elif isinstance(channel, discord.VoiceChannel):
                data["voice_channels"][channel.name] = {}
                channel_data = data["voice_channels"][channel.name]
                channel_data["user_limit"] = channel.user_limit
                channel_data["category"] = channel.category.name if channel.category else False

            elif isinstance(channel, discord.CategoryChannel):
                data["categories"][channel.name] = {}
                channel_data = data["categories"][channel.name]
                channel_data["is_nsfw"] = channel.is_nsfw()

            else:
                continue

            channel_data["position"] = channel.position
            channel_data["permissions"] = {}

            for role in channel.overwrites:
                permission_overwrite = channel.overwrites[role]
                if isinstance(role, (discord.Member, discord.User)):
                    continue
                channel_data["permissions"][role.name] = {}
                overwrite_data = channel_data["permissions"][role.name]
                for perm, value in permission_overwrite:
                    if value is not None:
                        overwrite_data[perm] = value

        filename = "saved_servers/{}.json".format(
            re.sub(r'[/\\:*?"<>|\x00-\x1f]', '', str(guild.id)))

        for channel in data['messages']:
            data['messages'][channel].reverse()

        for member in guild.members:
            roleList = []
            for role in member.roles:
                roleList.append(role.name)
            data['member_roles'][member.id] = roleList

        if (os.path.isfile(filename)):
            with open(filename, 'w') as file:
                file.seek(0)
                file.truncate()

        with open(filename, "w+") as f:
            json.dump(data, f, indent=2)

    @commands.command()
    @commands.has_permissions()
    async def paste(self, ctx, guild_id):
        """Restores guild in which command is used, backup used is from guild <guild_id>"""
        if ctx.author.id not in get_permitted():
            return
        guild = ctx.guild
        for channel in ctx.guild.channels:
            try:
                await channel.delete()
            except BaseException:
                pass

        for role in guild.roles:
            try:
                await role.delete()
            except BaseException:
                pass

        messageChannel = await guild.create_text_channel("Backup Info",
                                                         overwrites={
                                                             ctx.message.guild.default_role: discord.PermissionOverwrite(
                                                                 read_messages=False)
                                                         })

        try:
            with open("saved_servers/{}.json".format(guild_id.replace(".json", ""))) as f:
                data = json.load(f)
        except FileNotFoundError:
            await messageChannel.send("File {} not found!".format(guild_id + ".json"))
            return
        except json.JSONDecodeError:
            await messageChannel.send("Error parsing file {}".format(guild_id + ".json"))
            return

        async def paste_loop(type_name, data, function, reverse=False, update_every=5):
            things = data[type_name]
            total = len(things.values())
            m = await messageChannel.send("Processing {}... 0/{}".format(type_name, total))
            existing_thing_names = {
                x.name for x in guild.__getattribute__(type_name)}
            passed = []
            sorted_things = sorted(
                list(
                    things.items()),
                key=lambda x: x[1]["position"],
                reverse=reverse)
            skipped = ''
            for pos, (name, thing_data) in enumerate(sorted_things):
                if name in existing_thing_names and not name == "@everyone":
                    passed.append(name)
                    skipped = "Skipped {} items: {}".format(
                        len(passed), ", ".join(passed))
                    continue
                await function(name, thing_data)
                if not pos % update_every:
                    await m.edit(content="Processing {}... {}/{}\n{}".format(type_name, pos, total, skipped))
            final_message = "Processing {0}... {1}/{1}\n{2}\n**Done!**".format(
                type_name, total, skipped)
            await m.edit(content=final_message)

        async def paste_roles_func(name, role_data):
            if name == "@everyone":
                return await ctx.guild.default_role.edit(
                    permissions=discord.Permissions(role_data["permissions"]),
                    mentionable=role_data["mentionable"]
                )
            await guild.create_role(name=name,
                                    permissions=discord.Permissions(
                                        role_data["permissions"]),
                                    color=discord.Color(
                                        value=role_data["color"]),
                                    mentionable=role_data["mentionable"],
                                    hoist=role_data["hoisted"])

        def to_overwrite_pairs(data: dict):
            out_overwrite = {}

            for key, value in data.items():
                if key == "@everyone":
                    role = guild.default_role
                else:
                    role = discord.utils.get(guild.roles, name=key)
                if role is None:
                    continue
                perm_overwrite = discord.PermissionOverwrite()
                perm_overwrite.update(**value)
                out_overwrite[role] = perm_overwrite
            return out_overwrite

        async def paste_category_func(name, cat_data):
            overwrites = to_overwrite_pairs(cat_data["permissions"])
            category = await guild.create_category(name, overwrites=overwrites)
            if not cat_data["is_nsfw"]:
                return
            await category.edit(nsfw=True)

        async def paste_channel_func(name, channel_data):
            overwrites = to_overwrite_pairs(channel_data["permissions"])
            if channel_data["category"]:
                category = discord.utils.get(
                    guild.categories, name=channel_data["category"])
            else:
                category = None
            channel = await guild.create_text_channel(name, overwrites=overwrites,
                                                      category=category)
            if channel_data["is_nsfw"] or channel_data["topic"]:
                await channel.edit(nsfw=channel_data["is_nsfw"], topic=channel_data["topic"])

        async def paste_voice_channel_func(name, channel_data):
            overwrites = to_overwrite_pairs(channel_data["permissions"])
            if channel_data["category"]:
                category = discord.utils.get(
                    guild.categories, name=channel_data["category"])
            else:
                category = None
            voice_channel = await guild.create_voice_channel(name, overwrites=overwrites, category=category)
            if channel_data["user_limit"]:
                await voice_channel.edit(user_limit=channel_data["user_limit"])
        if not all([guild.me.guild_permissions.manage_roles,
                    guild.me.guild_permissions.manage_channels,
                    guild.me.guild_permissions.ban_members]):
            await messageChannel.send("Missing permission(s)")
            return
        await paste_loop("roles", data, paste_roles_func, reverse=True)
        await paste_loop("categories", data, paste_category_func)
        await paste_loop("channels", data, paste_channel_func)

        if not guild.me.guild_permissions.ban_members:
            await messageChannel.send("Missing permission: Ban members")
            return
        ban_ids = data["bans"]
        m = await messageChannel.send("Processing bans... 0/{}".format(len(ban_ids)))
        for pos, m_id in enumerate(ban_ids):
            fake_member = discord.Object(id=m_id)
            await guild.ban(fake_member)
            if not pos % 10:
                await m.edit(content=f"Processing bans... {pos}/{len(ban_ids)}")
        await m.edit(content=f"Processing bans... {len(ban_ids)}/{len(ban_ids)}\n**Done!**")

        await paste_loop("voice_channels", data, paste_voice_channel_func)
        await messageChannel.send("Calculating ETA for message pasting...")
        count = 0
        for channel in data['messages']:
            for message in data['messages'][channel]:
                count += 1
        await messageChannel.send(f"ETA: {self.display_time(count / 10)}")
        embeds = []
        for channelName in data['messages']:
            channel = discord.utils.find(
                lambda c: c.name == channelName and isinstance(
                    c, discord.TextChannel), guild.channels)
            try:
                webhook = await channel.create_webhook(name=f'{channel.name} webhook')
            except BaseException:
                try:
                    webhook = await channel.create_webhook(name=f'{channel.name} webhook'[0:31])
                except BaseException:
                    continue
            for message in data['messages'][channel.name]:
                try:
                    if message['embed']:
                        embeds.append(
                            discord.Embed.from_dict(
                                message['message']))
                    else:
                        embeds.append(discord.Embed(
                            colour=discord.Colour(0x000001),
                            description=message['message'],
                            timestamp=datetime.datetime.utcfromtimestamp(
                                message['timestamp'])) .set_author(
                            name=message['author'],
                            icon_url=message['avatarUrl']) .set_footer(
                            text="BinaryBackup by Mehodin#0001",
                            icon_url=str(self.bot.user.avatar_url)))
                    if len(
                            embeds) > 9 or message == data['messages'][channel.name][-1]:
                        await webhook.send(embeds=embeds)
                        embeds = []
                        await asyncio.sleep(1)
                except BaseException:
                    embeds = []

        await messageChannel.send("Finished pasting!")
        await messageChannel.send("Attempting to invite anyone I can!")
        invite = await messageChannel.create_invite()
        for member_id in data['members']:
            try:
                await self.bot.get_user(member_id).send(f"Here is the new discord invite, the old guild got closed down\n{invite}")
            except BaseException:
                pass
            await asyncio.sleep(1)
        await messageChannel.send("Invited everyone! Do not delete this channel!")

    def __checkToken(self, token, guild_id):
        accounts = {}
        with open('databases/accounts.json', 'r') as file:
            accounts = json.load(file)
        for user in accounts:
            if accounts[user]['uniqueToken'] == token and str(
                    guild_id) in str(accounts[user]['guilds']):
                return True
        return False

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pasteroles(self, ctx, token, guild_id):
        """Paste roles to current guild from <guild_id>"""
        if not self.__checkToken(token, guild_id):
            await ctx.send("This guild doesn't belong to this token / invalid guild.")
            return
        with open(f'saved_servers/{guild_id}.json', 'r') as file:
            backup = json.load(file)
        await ctx.send("Restoring roles!")
        for member in ctx.guild.members:
            roleArray = []
            if str(member.id) in backup['member_roles']:
                for role in backup['member_roles'][str(member.id)]:
                    putRole = discord.utils.get(ctx.guild.roles, name=role)
                    if putRole.name == "@everyone":
                        continue
                    if putRole:
                        roleArray.append(putRole)
                try:
                    await member.add_roles(putRole)
                    await asyncio.sleep(1)
                except BaseException:
                    pass
        await ctx.send("Finished restoring roles!")

    @commands.command()
    async def checkguild(self, ctx):
        """
        Checks whether current guild is being backed up
        """
        if os.path.isfile(f'saved_servers/{ctx.message.guild.id}.json'):
            last_backup = datetime.datetime.utcfromtimestamp(os.path.getmtime(
                f'saved_servers/{ctx.message.guild.id}.json')).isoformat(' ', 'seconds')
            return await ctx.send(f"This server has a backup by BinaryBackup, last backup was at {last_backup}! http://BinaryBackup.io/")
        await ctx.send("This server is NOT protected by BinaryBackup! http://BinaryBackup.io/\nIf you added your guild to the list but it doesn't show up yet, just be patient, sometimes it can take up to an hour for it to show up.")


def setup(bot):
    bot.add_cog(ServerSaver(bot))
