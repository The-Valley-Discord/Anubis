CREATE TABLE IF NOT EXISTS ignored_roles (
    guild_id    INTEGER     NOT NULL,
    role_id     INTEGER     NOT NULL,

    FOREIGN KEY(guild_id) REFERENCES level_settings(guild_id)
);