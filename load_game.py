# load_game.py

import json
from normalize import populate_cache  # ✅ Populates acronym/synonym cache
from redis_client import get_redis_client

# Connect to Redis
r = get_redis_client()

# Load game_data.json
with open('game_data.json', 'r') as f:
    game_data = json.load(f)

# Store full blob in Redis
r.set('game_data', json.dumps(game_data))
print("✅ Game data successfully loaded into Redis.")

# Populate acronym/synonym cache
populate_cache()
print("✅ Acronym cache loaded into Redis.")

# ✅ Load unstructured issues individually and as array
network_issues = game_data.get("network_issues", [])

# Store full array (for app.py compatibility)
r.set("network_issues", json.dumps(network_issues))
print("✅ Full network_issues array stored in Redis.")

# Store individual issues
for issue in network_issues:
    redis_key = f"issue:{issue['id']}"
    r.set(redis_key, json.dumps(issue))

print(f"✅ Loaded {len(network_issues)} unstructured issues into Redis individually.")

def load_trouble_tickets():
    """
    Extract trouble_tickets from game_data.json and store them in Redis under the key 'trouble_tickets'.
    """
    try:
        with open("game_data.json", "r") as f:
            game_data = json.load(f)

        trouble_tickets = game_data.get("trouble_tickets", [])
        r.set("trouble_tickets", json.dumps(trouble_tickets))
        print("✅ Successfully loaded trouble_tickets into Redis.")
    except Exception as e:
        print(f"❌ Failed to load trouble_tickets into Redis: {e}")

# Call the function to load trouble_tickets
if __name__ == "__main__":
    load_trouble_tickets()

