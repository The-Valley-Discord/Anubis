from typing import List

from discord.ext.commands import Greedy

from anubis import Anubis, IgnoredChannel, IgnoredRole, commands, discord, typing


class AdminCommands(Anubis.Cog):
    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def award(self, ctx: Anubis.Context, user: discord.User, amount: int):
        """Awards a user with the provided xp.
        `User` is the user to grant the xp to. This can be an Id, Mention, or Name
        `amount` is the amount to reward."""
        if amount < 0:
            await ctx.reply("Please enter a positive amount.", color=ctx.Color.BAD)
            return
        retrieved_user = ctx.database.users.get(user.id, ctx.guild.id)
        if not retrieved_user:
            await ctx.reply(
                f"{user.mention} was not found in database. Have they been on the server before?",
                color=ctx.Color.BAD,
            )
            return
        retrieved_user.grant_xp(amount)
        ctx.database.users.save(retrieved_user)
        await ctx.reply(
            f"{user.mention} has been awarded {amount} xp", color=ctx.Color.GOOD
        )
        return

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def reclaim(
        self, ctx: Anubis.Context, user: discord.User, amount: typing.Union[int, str]
    ):
        """Removes the provided xp from the user.
        `user` is the user to remove xp from. This can be an Id, Mention, or Name.
        `amount` is the amount to remove. `all` will remove all xp."""
        retrieved_user = ctx.database.users.get(user.id, ctx.guild.id)
        if not retrieved_user:
            await ctx.reply(
                f"{user.mention} was not found in database. Have they been on the server before?",
                color=ctx.Color.BAD,
            )
            return
        if isinstance(amount, int) and amount < 0:
            await ctx.reply("Please enter a positive number.", color=ctx.Color.BAD)
            return
        if isinstance(amount, str) and amount.lower() == "all":
            amount = retrieved_user.xp
            retrieved_user.xp = 0
        elif isinstance(amount, str):
            await ctx.reply("Please enter a valid number.", color=ctx.Color.BAD)
            return
        else:
            retrieved_user.xp -= amount
        if retrieved_user.xp < 0:
            amount += retrieved_user.xp
            retrieved_user.xp = 0
        ctx.database.users.save(retrieved_user)
        await ctx.reply(
            f"{user.mention} has had {amount} xp reclaimed", color=ctx.Color.BAD
        )
        await self.bot.post_log(
            retrieved_user.guild,
            f"{user.mention} has had {amount} xp reclaimed by {ctx.author.mention}",
            color=ctx.Color.BAD,
        )

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def ignore(
        self,
        ctx: Anubis.Context,
        args: Greedy[
            typing.Union[discord.User, discord.TextChannel, discord.Role, str]
        ],
    ):
        """Makes the bot ignore a user, Text Channel, or role for xp gain.
        `args` this is a space separated list of users, channels, or roles to ignore.
        This can be a Mention or Id. While names would work, its a bit too inaccurate
        and might cause issues"""
        mention_list = ""
        failed_list = ""
        guild = ctx.database.guilds.get_settings(ctx.guild.id)
        for arg in args:
            if isinstance(arg, discord.User):
                user = ctx.database.users.get(arg.id, ctx.guild.id)
                user.ignore_xp_gain = True
                ctx.database.users.save(user)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.TextChannel):
                ctx.database.ignored_channels.save(IgnoredChannel(guild, arg.id))
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.Role):
                ctx.database.ignored_roles.save(IgnoredRole(guild, arg.id))
                mention_list += f"{arg.mention} "
            if isinstance(arg, str):
                failed_list += " " + arg
        if len(mention_list) > 0:
            await ctx.reply(
                f"{mention_list} are now ignored.", color=ctx.Color.AUTOMATIC_BLUE
            )
            await self.bot.post_log(
                ctx.guild,
                f"**Mod:**{ctx.author.mention}\n" f"{mention_list} are now ignored.",
                color=ctx.Color.AUTOMATIC_BLUE,
            )
        if len(failed_list) > 0:
            await ctx.reply(f"Could not process {failed_list}", color=ctx.Color.BAD)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def recog(
        self,
        ctx: Anubis.Context,
        args: Greedy[
            typing.Union[discord.User, discord.TextChannel, discord.Role, str]
        ],
    ):
        """Makes the bot ignore a user, Text Channel, or role for xp gain.
        `args` this is a space separated list of users, channels, or roles to ignore.
        This can be a Mention or Id. While names would work, its a bit too inaccurate
        and might cause issues"""
        mention_list = ""
        failed_list = ""
        for arg in args:
            if isinstance(arg, discord.User):
                user = ctx.database.users.get(arg.id, ctx.guild.id)
                user.ignore_xp_gain = False
                ctx.database.users.save(user)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.TextChannel):
                ctx.database.ignored_channels.delete(arg.id, ctx.guild.id)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.Role):
                ctx.database.ignored_roles.delete(arg.id, ctx.guild.id)
                mention_list += f"{arg.mention} "
            if isinstance(arg, str):
                failed_list += " " + arg
        if len(mention_list) > 0:
            await ctx.reply(
                f"{mention_list} are no longer ignored.", color=ctx.Color.AUTOMATIC_BLUE
            )
            await self.bot.post_log(
                ctx.guild,
                f"**Mod:**{ctx.author.mention}\n"
                f"{mention_list} are no longer ignored",
                color=ctx.Color.AUTOMATIC_BLUE,
            )
        if len(failed_list) > 0:
            await ctx.reply(f"Could not process {failed_list}", color=ctx.Color.BAD)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def showignored(self, ctx: Anubis.Context):
        """Displays all the rewards for this server."""
        channels = ctx.database.ignored_channels.get_all(ctx.guild.id)
        roles = ctx.database.ignored_roles.get_all(ctx.guild.id)
        users = ctx.database.users.get_all_ignored(ctx.guild.id)
        if not channels and not roles and not users:
            await ctx.reply(
                "This guild does not have any ignored roles, users, or channels."
            )
            return
        channel_msg = []
        for channel in channels:
            retrieved_channel = ctx.guild.get_channel(channel.channel)
            if retrieved_channel:
                channel_msg.append(f"{retrieved_channel.mention}\n")
            else:
                ctx.database.ignored_channels.delete(channel.channel, ctx.guild)

        role_msg = []
        for role in roles:
            retrieved_role = ctx.guild.get_role(role.role)
            if retrieved_role:
                role_msg.append(f"{retrieved_role.mention}\n")
            else:
                ctx.database.ignored_roles.delete(role.role, ctx.guild.id)
        user_msg = []
        for user in users:
            retrieved_user = await self.bot.fetch_user(user.id)
            if retrieved_user:
                user_msg.append(f"{retrieved_user.mention}\n")
        embeds: List[discord.Embed] = []
        channel_fields = self.bot.create_embed_fields_from_list(channel_msg)
        role_fields = self.bot.create_embed_fields_from_list(role_msg)
        user_fields = self.bot.create_embed_fields_from_list(user_msg)
        embed = discord.Embed(title="Ignored Roles Users and Channels")
        embeds.append(embed)
        embeds = self.construct_ignored_embed(embeds, "Channels", channel_fields)
        embeds = self.construct_ignored_embed(embeds, "Roles", role_fields)
        embeds = self.construct_ignored_embed(embeds, "Users", user_fields)
        for embed in embeds:
            await ctx.reply(embed=embed)

    @staticmethod
    def construct_ignored_embed(
        embeds: List[discord.Embed], name: str, values: List[str]
    ) -> List[discord.Embed]:
        embed = embeds[0]
        for value in values:
            if len(embed.fields) == 25:
                embeds.append(embed)
                embed = discord.Embed(title=f"{embeds[0].title} Continued")
            embed.add_field(name=name, value=value)
        return embeds


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
