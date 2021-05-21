from discord.ext.commands import Greedy

from anubis import Anubis, commands, discord, typing, IgnoredChannel, IgnoredRole


class AdminCommands(Anubis.Cog):
    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def award(self, ctx: Anubis.Context, user: discord.User, amount: int):
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
        retrieved_user += amount
        ctx.database.users.save(retrieved_user)
        await ctx.reply(
            f"{user.mention} has been awarded {amount} xp", color=ctx.Color.GOOD
        )
        return

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def reclaim(
        self, ctx: Anubis.Context, user: discord.Member, amount: typing.Union[int, str]
    ):
        if amount < 0:
            await ctx.reply("Please enter a positive number.", color=ctx.Color.BAD)
            return
        retrieved_user = ctx.database.users.get(user.id, ctx.guild.id)
        if not retrieved_user:
            await ctx.reply(
                f"{user.mention} was not found in database. Have they been on the server before?",
                color=ctx.Color.BAD,
            )
            return
        if isinstance(amount, str) and amount.lower() == "all":
            retrieved_user.xp = 0
        else:
            retrieved_user.xp -= amount
        if retrieved_user.xp < 0:
            retrieved_user.xp = 0
        ctx.database.users.save(retrieved_user)
        await ctx.reply(
            f"{user.mention} has had {amount} xp reclaimed", color=ctx.Color.BAD
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
        mention_list = ""
        failed_list = ""
        for arg in args:
            if isinstance(arg, discord.User):
                user = ctx.database.users.get(arg.id, ctx.guild.id)
                user.ignore_xp_gain = True
                ctx.database.users.save(user)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.TextChannel):
                ctx.database.ignored_channels.save(IgnoredChannel(ctx.guild.id, arg.id))
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.Role):
                ctx.database.ignored_roles.save(IgnoredRole(ctx.guild.id, arg.id))
                mention_list += f"{arg.mention} "
            if isinstance(arg, str):
                failed_list += " " + arg
        if len(mention_list) > 0:
            await ctx.reply(
                f"{mention_list} are now ignored.", color=ctx.Color.AUTOMATIC_BLUE
            )
        if len(failed_list) > 0:
            await ctx.reply(f"Could not process {failed_list}", color=ctx.Color.BAD)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def recog(
        self,
        ctx: Anubis.Context,
        args: Greedy[
            typing.Union[discord.Member, discord.TextChannel, discord.Role, str]
        ],
    ):
        mention_list = ""
        failed_list = ""
        for arg in args:
            if isinstance(arg, discord.Member):
                user = ctx.database.users.get(arg.id, ctx.guild.id)
                user.ignore_xp_gain = False
                ctx.database.users.save(user)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.TextChannel):
                ctx.database.ignored_channels.Delete(arg.id, ctx.guild.id)
                mention_list += f"{arg.mention} "
            if isinstance(arg, discord.Role):
                ctx.database.ignored_roles.Delete(arg.id, ctx.guild.id)
                mention_list += f"{arg.mention} "
            if isinstance(arg, str):
                failed_list += " " + arg
        if len(mention_list) > 0:
            await ctx.reply(
                f"{mention_list} are no longer ignored.", color=ctx.Color.AUTOMATIC_BLUE
            )
        if len(failed_list) > 0:
            await ctx.reply(f"Could not process {failed_list}", color=ctx.Color.BAD)
