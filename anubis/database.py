import logging
import sqlite3
from pathlib import Path

from typing import List

from models import *


class Database:
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger("fuzzy")
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


class Guilds:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_settings(self, guild_id: int) -> Guild:
        guild = None
        try:
            guild = self.conn.execute(
                "SELECT * FROM level_settings WHERE guild_id=:guild_id", {"guild_id": guild_id}
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
                        "text_time": guild.text_timeout,
                        "base": guild.base,
                        "modifier": guild.modifier,
                        "amount": guild.reward_amount,
                        "user_channel": guild.user_channel,
                        "log_channel": guild.log_channel,
                        "guild_id": guild.id
                    },
                )
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
        else:
            try:
                values = (
                    guild.id,
                    guild.text_timeout,
                    guild.base,
                    guild.modifier,
                    guild.reward_amount,
                    guild.user_channel,
                    guild.log_channel
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

    def get(self, user_id, guild_id):
        user = None
        try:
            user = self.conn.execute("SELECT * FROM user_levels WHERE user_id=:user_id AND guild_id=:guild_id",
                                     {"user_id": user_id, "guild_id": guild_id}).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                User(
                    user["user_id"],
                    self.database.guilds.get_settings(user["guild_id"]),
                    user["xp"],
                    user["timeout"],
                    bool(user["ignore_xp_gain"])
                )
                if user
                else None
            )

    def save(self, user: User):
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
                        "guild_id": user.guild.id
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
                    user.ignore_xp_gain
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

    def get_ranked_users(self, guild_id):
        users = self.conn.execute("SELECT * FROM user_levels WHERE guild_id=:guild_id ORDER BY xp DESC",
                  {"guild_id": guild_id}).fetchall()
        guild = self.database.guilds.get_settings(guild_id)
        objectified_users: List[User] = [
            User(
                    user["user_id"],
                    guild,
                    user["xp"],
                    user["timeout"],
                    bool(user["ignore_xp_gain"])
                )for user in users]
        return objectified_users


class Rewards:
    def __init__(self, conn: sqlite3.Connection, database: Database):
        self.conn = conn
        self.database = database

    def get(self, guild_id: int, role_id: int):
        reward = None
        try:
            reward = self.conn.execute(
                "SELECT * FROM rewards WHERE guild_id=:guild_id AND reward_role=:reward_role",
                  {"guild_id": guild_id, "reward_role": role_id}).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Reward(
                    self.database.guilds.get_settings(reward["guild_id"]),
                    reward["reward_role"],
                    reward["reward_level"]
                )
                if reward
                else None
            )

    def get_all(self, guild_id: int):
        rewards = []
        try:
            rewards = self.conn.execute(
                "SELECT * FROM rewards WHERE guild_id=:guild_id",
                  {"guild_id": guild_id}).fetchall()
        except sqlite3.DatabaseError:
            pass
        finally:
            guild = self.database.guilds.get_settings(guild_id)
            return [
                Reward(
                    guild,
                    reward["reward_role"],
                    reward["reward_level"]
                )
                for reward in rewards
            ]

    def save(self, reward: Reward):
        retrieved_reward = self.get(reward.guild.id, reward.role)
        if retrieved_reward:
            try:
                self.conn.execute(
                    """UPDATE rewards SET
                    reward_level=:reward_level
                    WHERE guild_id=:guild_id AND reward_role=:reward_role """,
                    {
                        "reward_level": guild_rewards[2],
                        "guild_id": guild_rewards[0],
                        "reward_role": guild_rewards[1]
                    }
                )
        new_reward = (guild_id, reward_role, reward_level)
        sql = """INSERT INTO rewards (guild_id, 
                                        reward_role,
                                        reward_level)
                VALUES(?,?,?)"""
        c.execute(sql, new_reward)
        conn.commit()

    def update_guild_reward(guild_rewards):
        c.execute("""UPDATE rewards SET
                        reward_level=:reward_level
                        WHERE guild_id=:guild_id AND reward_role=:reward_role """,
                  {
                      "reward_level": guild_rewards[2],
                      "guild_id": guild_rewards[0],
                      "reward_role": guild_rewards[1]
                  })
        conn.commit()


    def delete_guild_reward(guild_id, reward_role):
        deleted_reward = (guild_id, reward_role)
        sql = "DELETE from rewards WHERE guild_id = ? AND reward_role = ? "
        c.execute(sql, deleted_reward)
        conn.commit()