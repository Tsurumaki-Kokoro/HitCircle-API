import redis


def get_redis_client():
    return redis.Redis(host="localhost", port=6379, db=1)
