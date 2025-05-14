# redis_client.py

import os
import redis
import threading
from redis.sentinel import Sentinel

# Thread-local storage for safe multi-threading in Streamlit
_thread_local = threading.local()

def get_redis_client():
    """
    Returns a thread-local Redis client instance.
    This prevents stale connection pooling across Streamlit threads.
    """
    if hasattr(_thread_local, "redis_client"):
        return _thread_local.redis_client

    use_sentinel = os.getenv("REDIS_USE_SENTINEL", "False").lower() == "true"

    if use_sentinel:
        sentinel_hosts = os.getenv("REDIS_SENTINEL_HOSTS", "")
        if not sentinel_hosts:
            raise ValueError("REDIS_SENTINEL_HOSTS must be set when REDIS_USE_SENTINEL=True")

        hosts = [tuple(host.split(":")) for host in sentinel_hosts.split(",")]
        hosts = [(host, int(port)) for host, port in hosts]

        sentinel = Sentinel(hosts, socket_timeout=0.2)
        _thread_local.redis_client = sentinel.master_for(
            os.getenv("REDIS_SENTINEL_SERVICE_NAME", "redis-master"),
            socket_timeout=0.2,
            decode_responses=True
        )
    else:
        _thread_local.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )

    return _thread_local.redis_client

