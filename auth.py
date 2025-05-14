# auth.py

import redis
import uuid
import datetime
import hashlib
import os

# ---------- Redis Setup ----------
REDIS_USE_SENTINEL = os.getenv("REDIS_USE_SENTINEL", "False").lower() == "true"

if REDIS_USE_SENTINEL:
    from redis.sentinel import Sentinel

    sentinel_hosts = os.getenv("REDIS_SENTINEL_HOSTS").split(",")
    sentinel_hosts = [tuple(host.split(":")) for host in sentinel_hosts]
    sentinel_hosts = [(host, int(port)) for host, port in sentinel_hosts]

    sentinel = Sentinel(sentinel_hosts, socket_timeout=0.1)
    r = sentinel.master_for(
        os.getenv("REDIS_SENTINEL_SERVICE_NAME", "redis-master"),
        socket_timeout=0.1,
        decode_responses=True
    )
else:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0,
        decode_responses=True
    )

# ---------- Utility Functions ----------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(username):
    return r.exists(f"user:{username.strip().lower()}")

def validate_user(username, password):
    username = username.strip().lower()
    redis_key = f"user:{username}"
    stored_hash = r.hget(redis_key, "password_hash")
    return stored_hash == hash_password(password)

def create_user(username, password):
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
