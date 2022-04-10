from datetime import datetime, timezone

import discord
from discord.ext import commands

from anubis import Anubis, User


class Leveling(Anubis.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ignored_channels = [channel.channel for channel in self.bot.database.ignored_channels.get_all(message.guild.id)]
        ignored_roles = [role.role for role in self.bot.database.ignored_roles.get_all(message.guild.id)]
        if (
            message.author.bot
            or message.is_system()
            or message.channel.id in ignored_channels
            or any(item.id in ignored_roles for item in message.author.roles)
        ):
            return
        user = self.bot.database.users.get(message.author.id, message.guild.id)
        if not user:
            self.bot.database.users.save(
                User(
                    message.author.id,
                    self.bot.database.guilds.get_settings(message.guild.id),
                    0,
                    datetime.now(timezone.utc),
                    False,
                )
            )
            return
        if user.ignore_xp_gain:
            return
        elif user.timeout < datetime.now(timezone.utc):
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
                    user.guild, embed=embed, timestamp=discord.utils.utcnow()
                )
            if rewards:
                roles: List[discord.Role] = []
                for reward in rewards:
                    role = message.guild.get_role(reward.role)
                    if role in message.author.roles:
                        pass
                    elif reward.level <= user.level:
                        roles.append(role)
                if not roles:
                    return
                try:
                    await message.author.add_roles(*roles, reason="Earned by leveling.")
                    embed = discord.Embed(
                        description=f"{message.author.mention} has earned {' '.join([role.mention for role in roles])}",
                        color=self.bot.Context.Color.AUTOMATIC_BLUE,
                    ).set_author(
                        name=f"{message.author.name}#{message.author.discriminator}"
                    ).set_footer(text=f"{message.author.id}")
                    await self.bot.post_log(
                        user.guild,
                        embed=embed,
                        timestamp=discord.utils.utcnow(),
                    )
                except discord.Forbidden:
                    await self.bot.post_log(
                        user.guild,
                        msg=f"Anubis does not have permission to add this role: {role.mention}",
                        color=self.bot.Context.Color.BAD,
                        timestamp=discord.utils.utcnow(),
                    )


async def setup(bot):
    await bot.add_cog(Leveling(bot))
