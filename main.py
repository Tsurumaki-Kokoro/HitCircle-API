from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import PlainTextResponse
from tortoise.contrib.fastapi import register_tortoise
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from loguru import logger

from app.user.api import user_router, limiter
from app.config.settings import *
from app.api.api_v1.endpoints.docs import docs_router
from app.api.api_v1.endpoints.beatmap import beatmap_router
from app.api.api_v1.endpoints.score import score_router
from app.api.api_v1.endpoints.user_info import info_router
from app.api.api_v1.endpoints.task import task_router
from app.api.api_v1.endpoints.multiplayer import multiplayer_router

app = FastAPI(title="HitCircle API", version="1.2.4")
logger.add("logs/{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days", level="DEBUG")
app.add_middleware(SlowAPIMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "database": "hitcircleapi"
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.user.models"],
            "default_connection": "default",
        }
    },
}

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

app.include_router(docs_router)
app.include_router(user_router)
app.include_router(beatmap_router)
app.include_router(score_router)
app.include_router(info_router)
app.include_router(multiplayer_router)
app.include_router(task_router)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return PlainTextResponse("Too many requests", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
