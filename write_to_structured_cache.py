import redis
from normalize import normalize_sentence  # Make sure this is available

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

REQUIRED_FIELDS = {"ticket_id", "input", "grade", "feedback"}

def validate_entry(entry: dict):
    """Ensure the entry has required fields."""
    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        raise ValueError(f"Structured cache entry missing required fields: {', '.join(missing)}")

def write_structured_entry_to_cache(entry: dict):
    """
    Adds a new entry to the Redis structured grading cache.

    Expected entry format:
    {
        "ticket_id": int,
        "input": str,
        "grade": int or str,
        "feedback": str
    }

    The 'source' field will always be set to 'game_play'.
    The input will be normalized before forming the Redis key.
    """
    validate_entry(entry)
    normalized_input = normalize_sentence(entry["input"])
    redis_key = f"graded:{entry['ticket_id']}:{normalized_input}"

    r.hset(redis_key, mapping={
        "grade": str(entry["grade"]),
        "feedback": entry["feedback"],
        "source": "game_play",
        "raw_input": entry["input"]  # optional for debugging
    })
    print(f"✅ Cached to Redis: {redis_key}")

# For standalone testing
if __name__ == "__main__":
    print("🧪 Manual Test Mode: Add a structured cache entry to Redis.\n")

    ticket_id = input("Ticket ID: ").strip()
    input_text = input("Input phrase: ").strip()
    grade = input("Grade (0–100): ").strip()
    feedback = input("Feedback: ").strip()

    try:
        entry = {
            "ticket_id": int(ticket_id),
            "input": input_text,
            "grade": int(grade),
            "feedback": feedback
        }
        write_structured_entry_to_cache(entry)
    except Exception as e:
        print(f"❌ Error: {e}")

