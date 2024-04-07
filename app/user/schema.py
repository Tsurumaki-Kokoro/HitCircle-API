from pydantic import BaseModel
from enum import Enum


class Platform(str, Enum):
    discord = "discord"
    qq = "qq"
    telegram = "telegram"


class GameModeInt(int, Enum):
    osu = 0
    taiko = 1
    ctb = 2
    mania = 3


class BindUserSchema(BaseModel):
    osu_username: str
    platform: str
    platform_uid: str


class UnbindUserSchema(BaseModel):
    platform: str
    platform_uid: str


class UpdateGameModeSchema(BaseModel):
    platform: str
    platform_uid: str
    game_mode: GameModeInt
