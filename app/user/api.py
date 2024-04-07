from fastapi import APIRouter, HTTPException, status, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from tortoise.exceptions import DoesNotExist, IntegrityError
from loguru import logger

from app.osu_utils.user import OsuUser
from app.user.models import UserModel
from app.user.schema import BindUserSchema, UnbindUserSchema, UpdateGameModeSchema
from app.security.api_key import get_api_key

user_router = APIRouter(tags=["User"])
limiter = Limiter(key_func=get_remote_address)


@user_router.post("/users/unbind", responses={
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute")
async def read_users(request: Request, data: UnbindUserSchema):
    try:
        instance = await UserModel.get(platform_uid=data.platform_uid, platform=data.platform)
        await instance.delete()
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        logger.error(f"unbind user error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"database error: {e}")

    return {"message": "unbind user success"}


@user_router.post("/users/bind", responses={
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    409: {"description": "User already bound"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute")
async def bind_user(request: Request, data: BindUserSchema):
    try:
        osu_user = OsuUser()
        osu_uid = await osu_user.get_user_uid(data.osu_username)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"get osu user error: {e}")

    try:
        await UserModel.create(osu_uid=osu_uid, platform=data.platform, platform_uid=data.platform_uid)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    except Exception as e:
        logger.error(f"bind user error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"database error: {e}")

    return {"message": "bind user success"}


@user_router.post("/users/update_mode", responses={
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute")
async def update_user_mode(request: Request, data: UpdateGameModeSchema):
    try:
        instance = await UserModel.get(platform_uid=data.platform_uid, platform=data.platform)
        instance.game_mode = data.game_mode.value
        await instance.save()
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        logger.error(f"update user game mode error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"database error: {e}")

    return {"message": "update user game mode success"}
