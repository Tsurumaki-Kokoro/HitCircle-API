from pydantic import BaseModel


class UserInfoUpdateSchema(BaseModel):
    platform: str
    platform_uid: str
