# delete_investigation.py

from redis_client import get_redis_client

def delete_investigation(issue_id: str):
    """
    Delete an investigation's question and answer from Redis.
    """
    r = get_redis_client()
    keys = [
        f"investigation:{issue_id}:question",
        f"investigation:{issue_id}:answer"
    ]
    deleted = r.delete(*keys)

    if deleted:
        print(f"🗑️  Investigation '{issue_id}' deleted.")
    else:
        print(f"⚠️  Investigation '{issue_id}' not found.")


if __name__ == "__main__":
    print("🗑️  Delete an Investigation\n")
    issue_id = input("Enter issue ID to delete (e.g., inv001): ").strip()

    if issue_id:
        delete_investigation(issue_id)
    else:
        print("❌ Issue ID cannot be empty.")

