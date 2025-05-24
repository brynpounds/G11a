# delete_player.py

from redis_client import get_redis_client

def delete_player(username):
    r = get_redis_client()
    username = username.strip().lower().replace(" ", "_")

    user_key = f"user:{username}"
    total_score_key = f"user:{username}:total_score"
    ticket_pattern = f"user:{username}:ticket:*"

    if not r.exists(user_key):
        print(f"❌ Player '{username}' not found.")
        return

    # Delete main account hash and score
    r.delete(user_key)
    r.delete(total_score_key)

    # Delete all per-ticket scores
    for key in r.keys(ticket_pattern):
        r.delete(key)

    print(f"✅ Player '{username}' and all related scores removed from Redis.")

# For CLI testing
if __name__ == "__main__":
    print("🧹 Delete Player From Redis\n")
    username = input("Enter player email: ").strip()
    if username:
        delete_player(username)
    else:
        print("❌ Username cannot be blank.")

