"""Redis client."""

import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

client = redis.Redis(host=REDIS_HOST, port=6379, db=0)

