from dataclasses import dataclass
from datetime import datetime


@dataclass
class Guild:
    id: int
    text_timeout: int
    base: int
    modifier: int
    reward_amount: int
    user_channel: int
    log_channel: int


@dataclass
class User:
    id: int
    guild: Guild
    xp: int
    timeout: datetime
    ignore_xp_gain: bool

    @property
    def level(self):
        i = 0
        while True:
            xp_needed = self.guild.base + (
                round(self.guild.base * (self.guild.modifier / 100) * i) * i
            )
            if self.xp < xp_needed:
                return i + 1
            i += 1

    def xp_needed(self, level_modifier: int = 0) -> int:
        level = self.level - 2 + level_modifier
        if level == 0:
            return self.guild.base
        elif level < 0:
            return 0
        else:
            return self.guild.base + (
                round(self.guild.base * (self.guild.modifier / 100) * level) * level
            )

    def grant_xp(self, xp_amount: int = None) -> None:
        if not xp_amount:
            xp_amount = self.guild.reward_amount
        self.xp += xp_amount


@dataclass
class Reward:
    guild: Guild
    role: int
    level: int

    @property
    def xp_needed(self):
        level = self.level - 2
        if level == 0:
            return self.guild.base
        elif level < 0:
            return 0
        else:
            return self.guild.base + (
                round(self.guild.base * (self.guild.modifier / 100) * level) * level
            )


@dataclass
class IgnoredChannel:
    guild: Guild
    channel: int


@dataclass
class IgnoredRole:
    guild: Guild
    role: int
