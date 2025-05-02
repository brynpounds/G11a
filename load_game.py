# load_game.py

import json
import redis
from normalize import populate_cache  # ✅ Populates acronym/synonym cache

# Connect to Redis (adjust if needed)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

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

