create table if not exists level_settings (
guild_id integer primary key,
text_time integer,
base integer,
modifier integer,
amount integer,
channel integer
);

create table if not exists user_levels (
guild_id integer,
user_id integer,
xp integer,
timeout timestamp,
ingnore_xp_gain integer
);

create table if not exists rewards (
guild_id integer,
reward_role integer,
reward_level integer
);