import logging
import sqlite3
from pathlib import Path
from typing import List

from anubis.models import *


class Database:
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger("anubis")
        self.log.setLevel(logging.INFO)

        self.conn = sqlite3.connect(
            config["database"]["path"],
            isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self.conn.row_factory = sqlite3.Row
        last_migration_number = 0
        try:
            last_migration_number = self.conn.execute(
                "SELECT * FROM applied_migrations ORDER BY number DESC LIMIT 1;"
            ).fetchone()[0]
        except sqlite3.DatabaseError:
            pass

        for path in sorted(Path(config["database"]["migrations"]).glob("*.sql")):
            number = int(path.stem)
            if number > last_migration_number:
                self.conn.executescript(
                    f"""
                    BEGIN TRANSACTION;
                    {path.read_text()}
                    INSERT INTO applied_migrations VALUES({number});
                    COMMIT;
                    """
                )
                self.log.info(f"Applied migration {number}")

        self.guilds = Guilds(self.conn)
        self.users = Users(self.conn, self)
        self.rewards = Rewards(self.conn, self)
        self.ignored_channels = IgnoredChannels(self.conn, self)
        self.ignored_roles = IgnoredRoles(self.conn, self)


class Guilds:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_settings(self, guild_id: int) -> Guild:
        guild = None
        try:
            guild = self.conn.execute(
                "SELECT * FROM level_settings WHERE guild_id=:guild_id",
                {"guild_id": guild_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Guild(
                    guild["guild_id"],
                    guild["text_time"],
                    guild["base"],
                    guild["modifier"],
                    guild["amount"],
                    guild["user_channel"],
                    guild["log_channel"],
                )
                if guild
                else None
            )

    def save(self, guild: Guild) -> Guild:
        retrieved_guild = self.get_settings(guild.id)
        if retrieved_guild:
            try:
                self.conn.execute(
                    "UPDATE level_settings "
                    "SET text_time=:text_time,"
                    "base=:base,"
                    "modifier=:modifier,"
                    "amount=:amount,"
                    "user_channel=:user_channel,"
                    "log_channel=:log_channel "
                    "WHERE guild_id=:guild_id",
                    {
                        "text_time": guild.get_text_timeout(),
                        "base": guild.base,
                        "modifier": guild.modifier,
                        "amount": guild.reward_amount,
                        "user_channel": guild.user_channel,
                        "log_channel": guild.log_channel,
                        "guild_id": guild.id,
                    },
                )
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        else:
            try:
                values = (
                    guild.id,
                    guild.get_text_timeout(),
                    guild.base,
                    guild.modifier,
                    guild.reward_amount,
                    guild.user_channel,
                    guild.log_channel,
                )
                sql = (
                    "INSERT INTO level_settings (guild_id, text_time, base, modifier, amount, user_channel, "
                    "log_channel) VALUES(?,?,?,?,?,?,?)"
                )
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        return self.get_settings(guild.id)


class Users:
    def __init__(self, conn: sqlite3.Connection, database: Database):
        self.conn = conn
        self.database = database

    def get(self, user_id: int, guild_id: int) -> User:
        user = None
        try:
            user = self.conn.execute(
                "SELECT * FROM user_levels WHERE user_id=:user_id AND guild_id=:guild_id",
                {"user_id": user_id, "guild_id": guild_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                User(
                    user["user_id"],
                    self.database.guilds.get_settings(user["guild_id"]),
                    user["xp"],
                    user["timeout"].replace(tzinfo=timezone.utc),
                    bool(user["ignore_xp_gain"]),
                )
                if user
                else None
            )

    def get_all_ignored(self, guild_id: int) -> List[User]:
        users = None
        guild = self.database.guilds.get_settings(guild_id)
        try:
            users = self.conn.execute(
                "SELECT * FROM user_levels WHERE guild_id=:guild_id AND ignore_xp_gain=:ignore_xp_gain",
                {"guild_id": guild_id, "ignore_xp_gain": True},
            ).fetchall()
        except sqlite3.DatabaseError:
            pass
        finally:
            return [
                User(
                    user["user_id"],
                    guild,
                    user["xp"],
                    user["timeout"].replace(tzinfo=timezone.utc),
                    bool(user["ignore_xp_gain"]),
                )
                for user in users
            ]

    def save(self, user: User) -> User:
        retrieved_user = self.get(user.id, user.guild.id)
        if retrieved_user:
            try:
                self.conn.execute(
                    "UPDATE user_levels "
                    "SET xp=:xp,"
                    "timeout=:timeout,"
                    "ignore_xp_gain=:ignore_xp_gain "
                    "WHERE user_id=:user_id "
                    "AND guild_id=:guild_id",
                    {
                        "xp": user.xp,
                        "timeout": user.timeout,
                        "ignore_xp_gain": user.ignore_xp_gain,
                        "user_id": user.id,
                        "guild_id": user.guild.id,
                    },
                )
            except sqlite3.DatabaseError:
                pass
        else:
            try:
                values = (
                    user.guild.id,
                    user.id,
                    user.xp,
                    user.timeout,
                    user.ignore_xp_gain,
                )
                sql = (
                    "INSERT INTO user_levels (guild_id, user_id, xp, timeout, ignore_xp_gain) "
                    "VALUES(?,?,?,?,?)"
                )
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        return self.get(user.id, user.guild.id)

    def get_ranked_users(self, guild_id: int) -> List[User]:
        users = self.conn.execute(
            "SELECT * FROM user_levels WHERE guild_id=:guild_id ORDER BY xp DESC",
            {"guild_id": guild_id},
        ).fetchall()
        guild = self.database.guilds.get_settings(guild_id)
        objectified_users: List[User] = [
            User(
                user["user_id"],
                guild,
                user["xp"],
                user["timeout"].replace(tzinfo=timezone.utc),
                bool(user["ignore_xp_gain"]),
            )
            for user in users
        ]
        return objectified_users


class Rewards:
    def __init__(self, conn: sqlite3.Connection, database: Database):
        self.conn = conn
        self.database = database

    def get(self, guild_id: int, role_id: int) -> Reward:
        reward = None
        try:
            reward = self.conn.execute(
                "SELECT * FROM rewards WHERE guild_id=:guild_id AND reward_role=:reward_role",
                {"guild_id": guild_id, "reward_role": role_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Reward(
                    self.database.guilds.get_settings(reward["guild_id"]),
                    reward["reward_role"],
                    reward["reward_level"],
                )
                if reward
                else None
            )

    def get_all(self, guild_id: int) -> List[Reward]:
        rewards = []
        try:
            rewards = self.conn.execute(
                "SELECT * FROM rewards WHERE guild_id=:guild_id", {"guild_id": guild_id}
            ).fetchall()
        except sqlite3.DatabaseError:
            pass
        finally:
            guild = self.database.guilds.get_settings(guild_id)
            return [
                Reward(guild, reward["reward_role"], reward["reward_level"])
                for reward in rewards
            ]

    def save(self, reward: Reward) -> Reward:
        retrieved_reward = self.get(reward.guild.id, reward.role)
        if retrieved_reward:
            try:
                self.conn.execute(
                    "UPDATE rewards SET "
                    "reward_level=:reward_level "
                    "WHERE guild_id=:guild_id AND reward_role=:reward_role ",
                    {
                        "reward_level": reward.level,
                        "guild_id": reward.guild.id,
                        "reward_role": reward.role,
                    },
                )
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        else:
            try:
                values = (reward.guild.id, reward.role, reward.level)
                sql = "INSERT INTO rewards (guild_id, reward_role, reward_level) VALUES(?,?,?)"
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        return self.get(reward.guild.id, reward.role)

    def delete(self, guild_id: int, role_id: int) -> None:
        try:
            self.conn.execute(
                "DELETE from rewards WHERE guild_id=:guild_id AND reward_role=:reward_role",
                {"guild_id": guild_id, "reward_role": role_id},
            )
            self.conn.commit()
        except sqlite3.DatabaseError:
            pass


class IgnoredChannels:
    def __init__(self, conn: sqlite3.Connection, database: Database):
        self.conn = conn
        self.database = database

    def get(self, channel_id: int, guild_id: int) -> IgnoredChannel:
        try:
            ignored_channel = self.conn.execute(
                "SELECT * FROM ignored_channels WHERE channel_id=:channel_id AND guild_id=:guild_id",
                {"channel_id": channel_id, "guild_id": guild_id},
            ).fetchone()
            guild = self.database.guilds.get_settings(guild_id)
            return (
                IgnoredChannel(guild, ignored_channel["channel_id"])
                if ignored_channel
                else None
            )
        except sqlite3.DatabaseError:
            pass

    def get_all(self, guild_id: int) -> List[IgnoredChannel]:
        try:
            ignored_channels = self.conn.execute(
                "SELECT * FROM ignored_channels WHERE guild_id=:guild_id",
                {"guild_id": guild_id},
            ).fetchall()
            guild = self.database.guilds.get_settings(guild_id)
            return [
                IgnoredChannel(guild, channel["channel_id"])
                for channel in ignored_channels
            ]
        except sqlite3.DatabaseError:
            pass

    def save(self, ignored_channel: IgnoredChannel) -> IgnoredChannel:
        retrieved_ignored_channel = self.get(
            ignored_channel.channel, ignored_channel.guild.id
        )
        if not retrieved_ignored_channel:
            try:
                values = (ignored_channel.guild.id, ignored_channel.channel)
                sql = "INSERT INTO ignored_channels(guild_id, channel_id) VALUES(?,?)"
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        return self.get(ignored_channel.channel, ignored_channel.guild.id)

    def delete(self, channel_id: int, guild_id: int) -> None:
        try:
            self.conn.execute(
                "DELETE FROM ignored_channels WHERE channel_id=:channel_id AND guild_id=:guild_id",
                {"channel_id": channel_id, "guild_id": guild_id},
            )
            self.conn.commit()
        except sqlite3.DatabaseError:
            pass


class IgnoredRoles:
    def __init__(self, conn: sqlite3.Connection, database: Database):
        self.conn = conn
        self.database = database

    def get(self, role_id: int, guild_id: int) -> IgnoredRole:
        try:
            ignored_role = self.conn.execute(
                "SELECT * FROM ignored_roles WHERE role_id=:role_id AND guild_id=:guild_id",
                {"roll_id": role_id, "guild_id": guild_id},
            ).fetchone()
            guild = self.database.guilds.get_settings(guild_id)
            return IgnoredRole(guild, ignored_role["role_id"]) if ignored_role else None
        except sqlite3.DatabaseError:
            pass

    def get_all(self, guild_id: int) -> List[IgnoredRole]:
        try:
            ignored_roles = self.conn.execute(
                "SELECT * FROM ignored_roles WHERE guild_id=:guild_id",
                {"guild_id": guild_id},
            ).fetchall()
            guild = self.database.guilds.get_settings(guild_id)
            return [IgnoredRole(guild, role["role_id"]) for role in ignored_roles]
        except sqlite3.DatabaseError:
            pass

    def save(self, ignored_role: IgnoredRole) -> IgnoredRole:
        retrieved_ignored_role = self.get(ignored_role.role, ignored_role.guild.id)
        if not retrieved_ignored_role:
            try:
                values = (ignored_role.guild.id, ignored_role.role)
                sql = "INSERT INTO ignored_roles(guild_id, role_id) VALUES(?,?)"
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        return self.get(ignored_role.role, ignored_role.guild.id)

    def delete(self, role_id: int, guild_id: int) -> None:
        try:
            self.conn.execute(
                "DELETE FROM ignored_roles WHERE role_id=:role_id AND guild_id=:guild_id",
                {"role_id": role_id, "guild_id": guild_id},
            )
            self.conn.commit()
        except sqlite3.DatabaseError:
            pass
