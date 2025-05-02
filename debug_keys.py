import redis

USER_EMAIL = "bpounds@cisco.com"
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

for key in r.keys(f"user:{USER_EMAIL}:ticket:*"):
    print(f"{key} → {r.get(key)}")

