import redis
import yaml
import os
from redis_client import get_redis_client

# Redis connection
r = get_redis_client()

def get_gameplay_entries():
    keys = r.keys("graded:*")
    gameplay_entries = []

    for key in keys:
        entry = r.hgetall(key)
        if entry.get("source") == "game_play":
            parts = key.split(":")
            if len(parts) >= 3:
                ticket_id = parts[1]
                normalized_input = parts[2]
                gameplay_entries.append({
                    "ticket_id": int(ticket_id) if ticket_id.isdigit() else ticket_id,
                    "input": entry.get("raw_input", normalized_input),
                    "grade": int(entry.get("grade", 0)),
                    "feedback": entry.get("feedback", ""),
                    "source": "game_play"
                })
    return gameplay_entries

def write_gameplay_entries_to_yaml(entries, file_path="extracted_gameplay_data.yml"):
    with open(file_path, "w") as f:
        for i, entry in enumerate(entries):
            if i > 0:
                f.write("\n")  # blank line between top-level entries

            f.write("- ticket_id: {}\n".format(entry["ticket_id"]))
            f.write("  input: {}\n".format(entry["input"]))
            f.write("  grade: {}\n".format(entry["grade"]))
            f.write("  feedback: {}\n".format(entry["feedback"]))
            f.write("  source: {}\n".format(entry["source"]))

    print(f"✅ Wrote {len(entries)} entries to {file_path}")

if __name__ == "__main__":
    entries = get_gameplay_entries()
    write_gameplay_entries_to_yaml(entries)
