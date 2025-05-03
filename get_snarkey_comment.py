import redis
import json
import random
import os
from redis.sentinel import Sentinel
from settings import REDIS_USE_SENTINEL, REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_SERVICE_NAME, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_DECODE_RESPONSES

# Ensure better randomness across short-lived runs
random.seed(os.urandom(128))

# Redis setup
if REDIS_USE_SENTINEL:
    sentinel_hosts = [tuple(host.split(":")) for host in REDIS_SENTINEL_HOSTS]
    sentinel = Sentinel(sentinel_hosts, decode_responses=REDIS_DECODE_RESPONSES)
    r = sentinel.master_for(REDIS_SENTINEL_SERVICE_NAME, db=REDIS_DB)
else:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)

def get_random_snark():
    data = r.get("game_data")
    if not data:
        return "❌ No 'game_data' found in Redis."

    try:
        game_data = json.loads(data)
        snark = game_data.get("snarky_comments", [])
        if not snark:
            return "❌ No snarky comments found."

        return random.choice(snark)
    except Exception as e:
        return f"❌ Error retrieving snark: {e}"

if __name__ == "__main__":
    print(get_random_snark())

