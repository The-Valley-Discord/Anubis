import sqlite3

conn = sqlite3.connect("log.db")

c = conn.cursor()


def init_db():
    with open("./schema.sql", "r") as schema_file:
        schema = schema_file.read()
    c.executescript(schema)


def add_guild_settings(guild_init):
    sql = """INSERT INTO level_settings (guild_id, text_time, base, modifier, amount, channel) 
    VALUES(?,?,?,?,?,?)"""
    c.execute(sql, guild_init)
    conn.commit()


def get_guild_settings(guild_id):
    c.execute("SELECT * FROM level_settings WHERE guild_id=:guild_id", {"guild_id": guild_id})
    return c.fetchone()


def update_text_time(text_time, guild_id):
    c.execute("UPDATE level_settings SET text_time=:text_time WHERE guild_id=:guild_id",
              {"text_time": text_time, "guild_id": guild_id})
    conn.commit()


def update_base(base, guild_id):
    c.execute("UPDATE level_settings SET base=:base WHERE guild_id=:guild_id",
              {"base": base, "guild_id": guild_id})
    conn.commit()


def update_modifier(modifier, guild_id):
    c.execute("UPDATE level_settings SET modifier=:modifier WHERE guild_id=:guild_id",
              {"modifier": modifier, "guild_id": guild_id})
    conn.commit()


def update_amount(amount, guild_id):
    c.execute("UPDATE level_settings SET amount=:amount WHERE guild_id=:guild_id",
              {"amount": amount, "guild_id": guild_id})
    conn.commit()


def update_channel(channel_id, guild_id):
    c.execute("UPDATE level_settings SET channel=:channel WHERE guild_id=:guild_id",
              {"channel": channel_id, "guild_id": guild_id})
    conn.commit()


def add_user(user_init):
    sql = """INSERT INTO user_levels (guild_id, user_id, xp, timeout, ignore_xp_gain) 
        VALUES(?,?,?,?,?)"""
    c.execute(sql, user_init)
    conn.commit()


def get_user(user_id, guild_id):
    c.execute("SELECT * FROM user_levels WHERE user_id=:user_id AND guild_id=:guild_id",
              {"user_id": user_id, "guild_id": guild_id})
    return c.fetchone()


def update_user_xp(user_id, guild_id, xp, timeout):
    c.execute("UPDATE user_levels SET xp=:xp, timeout=:timeout "
              "WHERE user_id=:user_id AND guild_id=:guild_id",
              {"xp": xp, "timeout": timeout, "user_id": user_id, "guild_id": guild_id})
    conn.commit()


def ignore_user_xp(user_id, guild_id, is_user_ignored):
    updated_user = (is_user_ignored, guild_id, user_id)
    sql = "UPDATE user_levels SET ignore_xp_gain = ? WHERE guild_id = ? AND user_id = ?"
    c.execute(sql, updated_user)
    conn.commit()


def add_guild_reward(guild_id, reward_role, reward_level):
    new_reward = (guild_id, reward_role, reward_level)
    sql = """INSERT INTO rewards (guild_id, 
                                reward_role,
                                reward_level)
        VALUES(?,?,?)"""
    c.execute(sql, new_reward)
    conn.commit()


def get_guild_rewards(guild_id):
    c.execute("SELECT * FROM rewards WHERE guild_id=:guild_id",
              {"guild_id": guild_id})
    return c.fetchall()


def get_single_guild_reward(guild_id, role_id):
    c.execute("SELECT * FROM rewards WHERE guild_id=:guild_id AND reward_role=:reward_role",
              {"guild_id": guild_id, "reward_role": role_id})
    return c.fetchone()


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


def add_ignored_channel(guild_id, channel_id):
    ignored_channel = (guild_id, channel_id)
    sql = "INSERT INTO ignored_channels(guild_id, channel_id) VALUES(?,?)"
    c.execute(sql, ignored_channel)
    conn.commit()


def get_ignored_channels(guild_id):
    guild = (guild_id,)
    sql = "SELECT * FROM ignored_channels WHERE guild_id = ?"
    c.execute(sql, guild)
    ignored_channels = []
    retrieved_channels = c.fetchall()
    for channel in retrieved_channels:
        ignored_channels.append(channel[1])
    return ignored_channels


def delete_ignored_channel(channel_id):
    sql = "DELETE FROM ignored_channels WHERE channel_id = ?"
    c.execute(sql, channel_id)
