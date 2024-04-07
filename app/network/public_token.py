from loguru import logger

from app.config import settings
from app.database.cache import get_redis_client
from app.network.network import httpx_request


class PublicToken:
    def __init__(self):
        self.cache = get_redis_client()

    async def set_public_token(self):
        client_id = settings.CLIENT_ID
        client_secret = settings.CLIENT_SECRET

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "public",
        }

        response_json = await httpx_request("POST", "https://osu.ppy.sh/oauth/token", headers=headers, data=data)

        for key in ["access_token", "token_type", "expires_in"]:
            if key not in response_json:
                logger.error(f"KeyError: Missing {key}")
                raise KeyError(f"Missing {key}")

        access_token = response_json["access_token"]
        expires_in = response_json["expires_in"]
        try:
            self.cache.set("public_token", access_token, ex=expires_in)
        except Exception as exc:
            logger.error(f"Radis Cache error: {exc}")

    async def get_public_token(self):
        token = self.cache.get("public_token")
        if token is None:
            try:
                await self.set_public_token()
            except Exception as exc:
                logger.error(f"Failed to get public token: {exc}")
                return None
        if token is not None:
            token = token.decode('utf-8')
        return token
