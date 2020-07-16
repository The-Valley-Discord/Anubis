create table if not exists level_settings (
guild_id integer primary key,
text_time integer,
base integer,
modifier integer,
amount integer,
user_channel integer,
log_channel integer
);

create table if not exists user_levels (
guild_id integer,
user_id integer,
xp integer,
timeout timestamp,
ignore_xp_gain integer
);

create table if not exists rewards (
guild_id integer,
reward_role integer,
reward_level integer
);

create table if not exists ignored_channels (
guild_id integer,
channel_id integer
);