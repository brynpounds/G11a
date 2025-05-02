import redis
import json

# Redis setup
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

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

