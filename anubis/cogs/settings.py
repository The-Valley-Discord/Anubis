import typing

import discord

from anubis import Anubis, commands


class Settings(Anubis.Cog):
    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def levelset(
        self,
        ctx: Anubis.Context,
        setting: str = "view",
        value: typing.Union[discord.TextChannel, int] = "view",
    ):
        """Adjusts the settings for the server. If no options are provided then it will post the settings.
        `Setting` is the option to adjust.
        `Value` is the new value."""
        guild = ctx.database.guilds.get_settings(ctx.guild.id)
        if value == "view":
            user_channel = ctx.guild.get_channel(guild.user_channel)
            if user_channel is None:
                user_channel = "None"
            else:
                user_channel = user_channel.mention
            log_channel = ctx.guild.get_channel(guild.log_channel)
            if log_channel is None:
                log_channel = "None"
            else:
                log_channel = log_channel.mention
            await ctx.reply(
                title="Current Level System settings",
                msg=(
                    f"**Texttime:** {guild.text_timeout}\n"
                    f"**Base:** {guild.base}\n"
                    f"**Modifier:** {guild.modifier}\n"
                    f"**Reward Amount:** {guild.reward_amount}\n"
                    f"**User-Channel:** {user_channel}\n"
                    f"**Log-Channel:** {log_channel}\n"
                ),
            )
            return
        elif setting.lower() == "texttime":
            guild.set_text_timeout(value)
            await ctx.reply(f"text timeout now set to {value} minutes.")
        elif setting.lower() == "base":
            guild.base = value
            await ctx.reply(f"Base XP now set to {value}.")
        elif setting.lower() == "modifier":
            guild.modifier = value
            await ctx.reply(f"Modifier now set to {value}.")
        elif setting.lower() == "amount":
            guild.reward_amount = value
            await ctx.reply(f"XP Amount now set to {value} per valid message.")
        elif setting.lower() == "user-channel":
            if value == 0:
                guild.user_channel = value
                await ctx.reply(f"User channel disabled.")
            elif not isinstance(value, discord.TextChannel):
                await ctx.reply("Please enter a valid channel.")
            else:
                guild.user_channel = value.id
                await ctx.reply(f"User channel now set to {value.mention}.")
        elif setting.lower() == "log-channel":
            if value == 0:
                guild.log_channel = value
                await ctx.reply(f"Log Channel disabled.")
            elif not isinstance(value, discord.TextChannel):
                await ctx.reply("Please enter a valid channel.")
            else:
                guild.log_channel = value.id
                await ctx.reply(f"Log Channel now set to {value.mention}.")
        else:
            raise commands.UserInputError(f"{setting} is not a valid setting option.")
        ctx.database.guilds.save(guild)


async def setup(bot):
    await bot.add_cog(Settings(bot))
