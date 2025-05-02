import redis
import json
import random
import os

# Seed the random generator with system entropy
random.seed(os.urandom(128))

# Redis setup
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_random_trivia():
    data = r.get("game_data")
    if not data:
        return "❌ No 'game_data' found in Redis."

    try:
        game_data = json.loads(data)
        trivia = game_data.get("trivia", [])
        if not trivia:
            return "❌ No trivia found in game_data."

        return random.choice(trivia)
    except Exception as e:
        return f"❌ Error reading trivia from Redis: {e}"

# ✅ For CLI testing
if __name__ == "__main__":
    print("🧪 Testing get_random_trivia from Redis...\n")
    trivia = get_random_trivia()
    print(f"🎉 Trivia: {trivia}")

