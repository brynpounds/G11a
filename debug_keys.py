import redis
from redis_client import get_redis_client

USER_EMAIL = "bpounds@cisco.com"
r = get_redis_client()

for key in r.keys(f"user:{USER_EMAIL}:ticket:*"):
    print(f"{key} → {r.get(key)}")

