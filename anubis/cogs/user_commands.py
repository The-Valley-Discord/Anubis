from anubis import Anubis, commands, discord, Guild, Reward, typing, datetime


class UserCommands(Anubis.Cog):
    @commands.command()
    @Anubis.has_guild_manage_message_or_in_user_bot_channel()
    async def level(self, ctx: Anubis.Context, user: discord.User = "me"):
        guild: Guild = ctx.database.guilds.get_settings(ctx.guild.id)
        if user == "me":
            user = ctx.author
        retrieved_user = ctx.database.users.get(user.id, ctx.guild.id)
        user_level = retrieved_user.level
        rewards = ctx.database.rewards.get_all(ctx.guild.id)
        next_reward = Reward(guild, 0, 0)
        for reward1 in rewards:
            if reward1.level <= user_level:
                pass
            elif reward1.level < next_reward.level or next_reward.level == 0:
                next_reward = reward1

        role_reward = ctx.guild.get_role(next_reward.role)
        level_progress = retrieved_user.xp - retrieved_user.xp_needed()
        xp_between = retrieved_user.xp_needed(1) - retrieved_user.xp_needed()
        embed = discord.Embed(
            title=f"Level and EXP for {user.display_name}", color=user.color
        )
        embed.add_field(name="XP", value=f"{retrieved_user.xp}", inline=True)
        embed.add_field(name="Level", value=f"{user_level}", inline=True)
        embed.add_field(
            name="Progress", value=f"{level_progress}/{xp_between}", inline=True
        )
        if next_reward.role == 0:
            embed.add_field(name="Next Reward", value=f"None", inline=True)
        else:
            embed.add_field(
                name="Next Reward",
                value=f"{role_reward.mention}\n at level {next_reward.level}",
                inline=True,
            )
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f"{ctx.guild.name}", icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    @Anubis.has_guild_manage_message_or_in_user_bot_channel()
    async def leaderboard(
        self, ctx: Anubis.Context, user: typing.Union[discord.User, str] = "all"
    ):
        ranked_users = ctx.database.users.get_ranked_users(ctx.guild.id)
        if not isinstance(user, discord.User) and user.lower() == "me":
            user = ctx.author
        if user.lower() == "all":
            leader_board_text = ""
            i = 0
            while i < 10 and i < len(ranked_users):
                retrieved_user = await self.bot.fetch_user(ranked_users[i].id)
                if retrieved_user:
                    leader_board_text += f"**{i + 1}** {retrieved_user.mention} **XP:** {ranked_users[i].xp}\n"
                i += 1
            await ctx.reply(
                title="LeaderBoard",
                msg=leader_board_text,
                color=ctx.Color.AUTOMATIC_BLUE,
                subtitle=f"Total Users {len(ranked_users)}",
                timestamp=datetime.utcnow(),
            )
            return
        if isinstance(user, discord.User):
            requesting_user = ctx.database.users.get(user.id, ctx.guild.id)
            leader_board_text = ""
            i = 0
            user_index = ranked_users.index(requesting_user)
            if user_index - 5 < 0:
                start_index = 0
            else:
                start_index = user_index - 5

            while i < 10 and i < len(ranked_users) and start_index < len(ranked_users):
                retrieved_user = await self.bot.fetch_user(ranked_users[start_index].id)
                if retrieved_user:
                    leader_board_text += (
                        f"**{start_index + 1}** {retrieved_user.mention} "
                        f"**XP:** {ranked_users[start_index].xp}\n"
                    )
                i += 1
                start_index += 1
            await ctx.reply(
                title="LeaderBoard",
                msg=leader_board_text,
                color=ctx.Color.AUTOMATIC_BLUE,
                subtitle=f"Total Users {len(ranked_users)}",
                timestamp=datetime.utcnow(),
            )
            return
