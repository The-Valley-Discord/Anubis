import enum
import logging
import random
import typing
from copy import copy
from datetime import datetime, timezone

import discord
from discord import Activity, ActivityType
from discord.ext import commands

from anubis.database import Database


class Anubis(commands.Bot):
    """
    This Class is mostly just a standard discord.py bot class but sets up additional configuration needed for this bot.
    """

    class Context(commands.Context):
        """
        A context with extra features.
        """

        class Color(enum.IntEnum):
            """Colors used by Anubis."""

            GOOD = 0x7DB358
            I_GUESS = 0xF9AE36
            BAD = 0xD52D48
            AUTOMATIC_BLUE = 0x1C669B

        @property
        def log(self) -> logging.Logger:
            """Return a logger that's associated with the current cog and command."""
            name = self.command.name.replace(self.bot.config["discord"]["prefix"], "")
            if not self.cog:
                return self.bot.log.getChild(name)

            return self.cog.log.getChild(name)

        @property
        def database(self) -> Database:
            """Return the bot's database connection"""
            return self.bot.database

        async def invoke_command(self, text: str) -> None:
            """Pretend the user is invoking a command."""
            words = text.split(" ")
            if not words:
                return

            if not words[0].startswith(self.bot.command_prefix):
                words[0] = self.bot.command_prefix + words[0]
                text = " ".join(words)

            message = copy(self.message)

            message.content = text
            message.id = discord.utils.time_snowflake(
                datetime.now(tz=timezone.utc).replace(tzinfo=None)
            )
            await self.bot.process_commands(message)

        async def reply(
            self,
            msg: str = None,
            title: str = discord.Embed.Empty,
            subtitle: str = None,
            color: Color = Color.GOOD,
            embed: discord.Embed = None,
            delete_after: float = None,
            timestamp: datetime = datetime.utcnow(),
        ):
            """Helper for sending embedded replies"""
            if not embed:
                if not subtitle:
                    subtitle = discord.Embed.Empty

                lines = str(msg).split("\n")
                buf = ""
                for line in lines:
                    if len(buf + "\n" + line) > 2048:
                        try:
                            await self.send(
                                "",
                                embed=discord.Embed(
                                    color=color,
                                    description=buf,
                                    title=title,
                                    timestamp=timestamp,
                                ).set_footer(text=subtitle),
                                delete_after=delete_after,
                            )
                            buf = ""
                        except discord.Forbidden:
                            return await self.send(
                                "The bot does not have permissions to send embeds in this channel."
                            )
                    else:
                        buf += line + "\n"

                if len(buf) > 0:
                    try:
                        return await self.send(
                            "",
                            embed=discord.Embed(
                                color=color,
                                description=buf,
                                title=title,
                                timestamp=timestamp,
                            ).set_footer(text=subtitle),
                            delete_after=delete_after,
                        )
                    except discord.Forbidden:
                        return await self.send(
                            "The bot does not have permissions to send embeds in this channel."
                        )
            try:
                return await self.send("", embed=embed, delete_after=delete_after)
            except discord.Forbidden:
                return await self.send(
                    "The bot does not have permissions to send embeds in this channel."
                )

    class Cog(commands.Cog):
        """
        A cog with a logger attached to it.
        """

        def __init__(self, bot):
            self.bot: Anubis = bot
            self.log = bot.log.getChild(self.__class__.__name__)

    def __init__(self, config, database: Database, **kwargs):
        self.config = config

        self.log = logging.getLogger("Anubis")
        self.log.setLevel(logging.INFO)
        self.database: Database = database
        super().__init__(command_prefix=config["discord"]["prefix"], **kwargs)

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    @staticmethod
    def random_status() -> Activity:
        """Return a silly status to show to the world"""
        return random.choice(
            [
                Activity(
                    type=ActivityType.watching,
                    name="and judging the content of your soul.",
                ),
                Activity(
                    type=ActivityType.listening,
                    name="to the souls of the damned.",
                ),
            ]
        )

    @staticmethod
    async def direct_message(
        to: typing.Union[discord.Member, discord.User],
        msg: str = None,
        title: str = discord.Embed.Empty,
        subtitle: str = None,
        color: Context.Color = Context.Color.GOOD,
        embed: discord.Embed = None,
        delete_after: float = None,
    ):
        """Helper for direct messaging a user."""
        if to.bot:
            return None
        if not embed:
            if not subtitle:
                subtitle = discord.Embed.Empty

            lines = str(msg).split("\n")
            buf = ""
            for line in lines:
                if len(buf + "\n" + line) > 2048:
                    await to.send(
                        "",
                        embed=discord.Embed(
                            color=color, description=buf, title=title
                        ).set_footer(text=subtitle),
                        delete_after=delete_after,
                    )
                    buf = ""
                else:
                    buf += line + "\n"

            if len(buf) > 0:
                return await to.send(
                    "",
                    embed=discord.Embed(
                        color=color, description=buf, title=title
                    ).set_footer(text=subtitle),
                    delete_after=delete_after,
                )

        return await to.send("", embed=embed, delete_after=delete_after)

    async def post_log(self, guild: discord.Guild, *args, **kwargs):
        """Post a log entry to a guild, usage same as ctx.reply"""
        configuration = self.database.guilds.get_settings(guild.id)
        if not configuration:
            return
        channel = self.get_channel(configuration.log_channel)
        if channel:
            await self.Context.reply(channel, *args, **kwargs)

    @staticmethod
    def has_guild_manage_message_or_in_user_bot_channel():
        def predicate(ctx: Anubis.Context):
            guild = ctx.database.guilds.get_settings(ctx.guild.id)
            return (
                ctx.author.guild_permissions.manage_messages
                or guild.user_channel == ctx.channel.id
                or guild.user_channel == 0
            )

        return commands.check(predicate)

    @staticmethod
    def create_embed_fields_from_list(
        message_list: typing.List[str],
    ) -> typing.List[str]:
        length = 0
        msg = ""
        fields = []
        for message in message_list:
            if len(message) > 2048:
                raise ValueError("Individual line is too long.")
            if length + len(message) > 2048:
                fields.append(msg)
                msg = ""
            msg += message
            length = len(msg)
        if len(msg) > 0:
            fields.append(msg)
        return fields
