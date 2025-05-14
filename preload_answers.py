import os
import redis
import yaml
from normalize import normalize_sentence  # ensure this exists and is correct
from redis_client import get_redis_client

# Redis setup
r = get_redis_client()

PRELOAD_DIR = './preload_answers'
REQUIRED_FIELDS = {"ticket_id", "input", "grade", "feedback", "source"}

def load_yaml_files():
    for filename in os.listdir(PRELOAD_DIR):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            file_path = os.path.join(PRELOAD_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    entries = yaml.safe_load(f)

                if not isinstance(entries, list):
                    entries = [entries]

                for entry in entries:
                    if not all(field in entry for field in REQUIRED_FIELDS):
                        print(f"❌ Missing fields in {filename}: {entry}")
                        continue

                    normalized_input = normalize_sentence(entry["input"])
                    redis_key = f"graded:{entry['ticket_id']}:{normalized_input}"

                    if r.exists(redis_key):
                        print(f"⚠️  Skipped (already exists): {redis_key}")
                        continue

                    r.hset(redis_key, mapping={
                        "grade": str(entry["grade"]),
                        "feedback": entry["feedback"],
                        "source": entry["source"],
                        "raw_input": entry["input"]  # Optional for audit/debug
                    })

                    print(f"✅ Cached: {redis_key}")

            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")

if __name__ == "__main__":
    load_yaml_files()

