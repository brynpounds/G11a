# auth.py

import uuid
import datetime
import hashlib
from redis_client import get_redis_client

# ---------- Redis Client ----------
r = get_redis_client()

# ---------- Utility Functions ----------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(username):
    r = get_redis_client()
    return r.exists(f"user:{username.strip().lower()}")

def validate_user(username, password):
    r = get_redis_client()
    username = username.strip().lower()
    redis_key = f"user:{username}"
    stored_hash = r.hget(redis_key, "password_hash")
    return stored_hash == hash_password(password)

def create_user(username, password):
    r = get_redis_client()
    username = username.strip().lower().replace(" ", "_")
    redis_key = f"user:{username}"

    if r.exists(redis_key):
        return False, "⚠️  User already exists."

    if not password or len(password) < 4:
        return False, "❌ Password is too short."

    user_id = str(uuid.uuid4())
    user_profile = {
        "user_id": user_id,
        "username": username,
        "created_at": str(datetime.datetime.utcnow()),
        "password_hash": hash_password(password),
        "score": "0",
        "games_played": "0"
    }

    r.hset(redis_key, mapping=user_profile)
    return True, f"✅ User '{username}' created successfully."




