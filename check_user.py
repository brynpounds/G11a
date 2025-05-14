import redis
import json
from redis_client import get_redis_client

# Redis setup
r = get_redis_client()

def check_user(username):
    username = username.strip().lower().replace(" ", "_")
    redis_key = f"user:{username}"

    if not r.exists(redis_key):
        print(f"❌ User '{username}' does not exist.")
        return

    user_data = r.hgetall(redis_key)
    print(f"\n👤 User: {username}")
    print("📦 Stored Data:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    username = input("🔍 Enter username to check: ").strip()
    if username:
        check_user(username)
    else:
        print("❌ Username cannot be blank.")

