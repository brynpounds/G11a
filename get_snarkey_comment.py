import json
import random
import os
from redis_client import get_redis_client

# Ensure better randomness across short-lived runs
random.seed(os.urandom(128))

# Redis connection
r = get_redis_client()

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

