import redis
import json
import random
import os
from redis_client import get_redis_client

random.seed(os.urandom(128))  # ✅ Ensures better randomness

# Redis setup
r = get_redis_client()

def get_random_joke():
    data = r.get("game_data")
    if not data:
        return "❌ No 'game_data' found in Redis."

    try:
        game_data = json.loads(data)
        jokes = game_data.get("jokes", [])
        if not jokes:
            return "❌ No jokes found in game_data."

        return random.choice(jokes)
    except Exception as e:
        return f"❌ Error reading jokes from Redis: {e}"

# ✅ For CLI testing
if __name__ == "__main__":
    print("🧪 Testing get_random_joke from Redis...\n")
    joke = get_random_joke()
    print(f"🤣 Joke: {joke}")

