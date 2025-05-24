# repair_issues.py

import json
from redis_client import get_redis_client

r = get_redis_client()
raw = r.get("network_issues")
if not raw:
    print("❌ No network_issues array found.")
    exit(1)

issues = json.loads(raw)
for issue in issues:
    key = f"issue:{issue['id']}"
    r.set(key, json.dumps(issue))
    print(f"✅ Rebuilt key: {key}")

