# load_game.py

import json
import redis
from redis.sentinel import Sentinel
from normalize import populate_cache  # ✅ Populates acronym/synonym cache
from settings import REDIS_USE_SENTINEL, REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_SERVICE_NAME, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_DECODE_RESPONSES

# Connect to Redis using settings from settings.py
if REDIS_USE_SENTINEL:
    sentinel_hosts = [tuple(host.split(":")) for host in REDIS_SENTINEL_HOSTS]
    sentinel = Sentinel(sentinel_hosts, decode_responses=REDIS_DECODE_RESPONSES)
    r = sentinel.master_for(REDIS_SENTINEL_SERVICE_NAME, db=REDIS_DB)
else:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)

# Load game_data.json
with open('game_data.json', 'r') as f:
    game_data = json.load(f)

# Store full blob in Redis
r.set('game_data', json.dumps(game_data))
print("✅ Game data successfully loaded into Redis.")

# Populate acronym/synonym cache
populate_cache()
print("✅ Acronym cache loaded into Redis.")

# ✅ Load unstructured issues individually using correct field name
network_issues = game_data.get("network_issues", [])
for issue in network_issues:
    redis_key = f"issue:{issue['id']}"
    r.set(redis_key, json.dumps(issue))

print(f"✅ Loaded {len(network_issues)} unstructured issues into Redis individually.")

def load_trouble_tickets():
    """
    Extract trouble_tickets from game_data.json and store them in Redis under the key 'trouble_tickets'.
    """
    try:
        # Load game_data.json
        with open("game_data.json", "r") as f:
            game_data = json.load(f)

        # Extract trouble_tickets
        trouble_tickets = game_data.get("trouble_tickets", [])

        # Store trouble_tickets in Redis
        r.set("trouble_tickets", json.dumps(trouble_tickets))
        print("✅ Successfully loaded trouble_tickets into Redis.")
    except Exception as e:
        print(f"❌ Failed to load trouble_tickets into Redis: {e}")

# Call the function to load trouble_tickets
if __name__ == "__main__":
    load_trouble_tickets()

