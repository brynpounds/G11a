import redis
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# InfluxDB connection
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "_ngsl81ZgEW-zivbImIl6kjANpltSdb6Pu-SPe116a7tBk7epMizCTHN2NgO8-xfNsrhaOTNijZRg352HS4V4w=="
INFLUX_ORG = "gotn"
INFLUX_BUCKET = "gotn-metrics"
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def check_redis_structured_cache(ticket_id, raw_input):
    """
    Check if the input exists in the structured Redis cache for a specific ticket.
    Returns the hash fields if found, else None.
    Also logs the duration of the Redis query to InfluxDB.
    """
    redis_key = f"graded:{ticket_id}:{raw_input}"
    start = time.perf_counter()
    cached = r.hgetall(redis_key)
    duration = time.perf_counter() - start

    # Write duration metric to InfluxDB
    point = Point("embedding_similarity_check") \
        .field("duration", duration) \
        .tag("operation", "redis_structured_check") \
        .tag("ticket_id", ticket_id)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    return cached if cached else None

if __name__ == "__main__":
    ticket_id = input("🎟️ Enter ticket ID: ").strip()
    user_input = input("🔍 Enter your EXACT diagnostic phrase to check (no normalization): ").strip()

    if not ticket_id or not user_input:
        print("⚠️ Ticket ID and input phrase are required.")
        exit()

    cached_entry = check_redis_structured_cache(ticket_id, user_input)

    if cached_entry:
        print("\n✅ Found in structured Redis cache:")
        print(f"Grade:    {cached_entry.get('grade')}")
        print(f"Feedback: {cached_entry.get('feedback')}")
        print(f"Source:   {cached_entry.get('source')}")
    else:
        print("\n❌ Entry not found in Redis structured cache.")

