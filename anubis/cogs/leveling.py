from datetime import datetime

import discord
from discord.ext import commands

from anubis import Anubis, User


class Leveling(Anubis.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ignored_channels = self.bot.database.ignored_channels.get_all(message.guild.id)
        ignored_roles = self.bot.database.ignored_roles.get_all(message.guild.id)
        if ignored_roles:
            ignored_role_ids = [role.role for role in ignored_roles]
            if any(item.id in ignored_role_ids for item in message.author.roles):
                return
        if (
            message.author.bot
            or message.is_system()
            or message.channel.id in ignored_channels
        ):
            return
        user = self.bot.database.users.get(message.author.id, message.guild.id)
        if not user:
            self.bot.database.users.save(
                User(
                    message.author.id,
                    self.bot.database.guilds.get_settings(message.guild.id),
                    0,
                    datetime.utcnow(),
                    False,
                )
            )
            return
        if user.ignore_xp_gain:
            return
        elif user.timeout < datetime.utcnow():
            previous_level = user.level
            user.grant_xp()
            self.bot.database.users.save(user)
            rewards = self.bot.database.rewards.get_all(message.guild.id)
            if user.level > previous_level:
                embed = discord.Embed(
                    description=f"{message.author.mention} has leveled to level {user.level}.",
                    color=self.bot.Context.Color.AUTOMATIC_BLUE,
                )
                embed.set_author(
                    name=f"{message.author.name}#{message.author.discriminator}"
                )
                embed.set_footer(text=f"{message.author.id}")
                await self.bot.post_log(
                    user.guild, embed=embed, timestamp=datetime.utcnow()
                )
            if rewards:
                for reward in rewards:
                    role = message.guild.get_role(reward.role)
                    if role in message.author.roles:
                        pass
                    elif reward.level <= user.level:
                        try:
                            await message.author.add_roles(role)
                            embed = discord.Embed(
                                description=f"{message.author.mention} has earned {role.mention}",
                                color=self.bot.Context.Color.AUTOMATIC_BLUE,
                            )
                            embed.set_author(
                                name=f"{message.author.name}#{message.author.discriminator}"
                            )
                            embed.set_footer(text=f"{message.author.id}")
                            await self.bot.post_log(
                                user.guild, embed=embed, timestamp=datetime.utcnow()
                            )
                        except discord.Forbidden:
                            await self.bot.post_log(
                                user.guild,
                                msg=f"Anubis does not have permission to add this role: {role.mention}",
                                color=self.bot.Context.Color.BAD,
                                timestamp=datetime.utcnow(),
                            )
