from tortoise import fields
from tortoise.models import Model


class UserModel(Model):
    id = fields.IntField(pk=True)
    osu_uid = fields.CharField(max_length=255)
    game_mode = fields.IntField(default=0)
    platform = fields.CharField(max_length=255)
    platform_uid = fields.CharField(max_length=255)

    class Meta:
        table = "user"
        unique_together = [("platform", "platform_uid")]


class UserOsuInfoHistory(Model):
    id = fields.IntField(pk=True)
    osu_uid = fields.CharField(max_length=255)
    game_mode = fields.IntField()
    country_rank = fields.IntField(null=True)
    global_rank = fields.IntField(null=True)
    pp = fields.FloatField(null=True)
    accuracy = fields.FloatField(null=True)
    play_count = fields.IntField(null=True)
    play_time = fields.IntField(null=True)
    total_hits = fields.IntField(null=True)
    date = fields.DateField(auto_now_add=True)

    class Meta:
        table = "user_osu_info_history"
        indexes = ("id", "osu_uid", "date")
