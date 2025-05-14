# redis_client.py

import os
import threading
import redis
from redis.sentinel import Sentinel, MasterNotFoundError

# Thread-local storage for safety in multi-threaded apps
_thread_local = threading.local()

def get_redis_client():
    if hasattr(_thread_local, "redis_client"):
        return _thread_local.redis_client

    use_sentinel = os.getenv("REDIS_USE_SENTINEL", "False").lower() == "true"

    if use_sentinel:
        sentinel_hosts = os.getenv("REDIS_SENTINEL_HOSTS", "")
        if not sentinel_hosts:
            raise ValueError("REDIS_SENTINEL_HOSTS must be set when REDIS_USE_SENTINEL=True")
        hosts = [tuple(host.split(":")) for host in sentinel_hosts.split(",")]
        hosts = [(host, int(port)) for host, port in hosts]

        service_name = os.getenv("REDIS_SENTINEL_SERVICE_NAME", "redis-master")

        # Attempt to connect to Sentinels, skip any unreachable ones
        for host, port in hosts:
            try:
                sentinel = Sentinel([(host, port)], socket_timeout=0.5)
                master = sentinel.discover_master(service_name)
                if master:
                    _thread_local.redis_client = sentinel.master_for(
                        service_name,
                        socket_timeout=0.5,
                        decode_responses=True
                    )
                    print(f"✅ Connected to Redis master via Sentinel at {host}:{port}")
                    break
            except (ConnectionError, TimeoutError, MasterNotFoundError):
                print(f"⚠️ Sentinel at {host}:{port} unreachable, trying next...")

        # If no connection succeeded
        if not hasattr(_thread_local, "redis_client"):
            raise ConnectionError("❌ Could not connect to any Sentinel instance to discover master.")

    else:
        _thread_local.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )
        print(f"✅ Connected to standalone Redis at {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")

    return _thread_local.redis_client

