import redis
import json
import random
import os
from redis_client import get_redis_client

# Seed only once on module load
random.seed(os.urandom(128))

# Redis setup
r = get_redis_client()

def get_random_joke(session_state=None):
    data = r.get("game_data")
    if not data:
        return "❌ No 'game_data' found in Redis."

    try:
        game_data = json.loads(data)
        jokes = game_data.get("jokes", [])
        if not jokes:
            return "❌ No jokes found in game_data."

        # Optional: Streamlit session tracking
        if session_state is not None:
            if "used_jokes" not in session_state:
                session_state.used_jokes = set()

            unused = [j for j in jokes if j not in session_state.used_jokes]

            if not unused:
                session_state.used_jokes = set()
                unused = jokes.copy()

            joke = random.choice(unused)
            session_state.used_jokes.add(joke)
            return joke

        # Fallback: just random choice
        return random.choice(jokes)

    except Exception as e:
        return f"❌ Error reading jokes from Redis: {e}"

# ✅ For CLI testing
if __name__ == "__main__":
    print("🧪 Testing get_random_joke from Redis...\n")
    joke = get_random_joke()
    print(f"🤣 Joke: {joke}")

