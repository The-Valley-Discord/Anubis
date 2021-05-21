import discord

from anubis import Anubis, commands, Reward


class Rewards(Anubis.Cog):
    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def reward(self, ctx: Anubis.Context, role: discord.Role, role_level: int):
        """Adds or updates a leveling reward.
        `role` is the role that is to be rewarded. This can be a mention, id or name.
        `role_level` is the level that the role should be awarded at."""
        retrieved_reward = ctx.database.rewards.get(ctx.guild.id, role.id)
        if not retrieved_reward:
            ctx.database.rewards.save(
                Reward(
                    ctx.database.guilds.get_settings(ctx.guild.id), role.id, role_level
                )
            )
            await ctx.reply(
                f"Added {role.mention} reward at level {role_level}",
                color=ctx.Color.GOOD,
            )
        else:
            retrieved_reward.level = role_level
            ctx.database.rewards.save(retrieved_reward)
            await ctx.reply(
                f"Updated {role.mention} reward to level {role_level}",
                color=ctx.Color.GOOD,
            )

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def remove(self, ctx: Anubis.Context, role: discord.Role):
        """Removes a reward from the database.
        `role` is the role that is to be removed. This can be a mention, id or name."""
        ctx.database.rewards.delete(ctx.guild.id, role.id)
        await ctx.reply(f"Removed {role.mention} reward", color=ctx.Color.I_GUESS)
