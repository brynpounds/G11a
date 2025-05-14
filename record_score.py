# record_score.py

from redis_client import get_redis_client

def record_player_score(username, ticket_id, new_score):
    """
    Records a player's score for a specific ticket.

    If full credit (100+) already awarded, no additional points are given.
    Only the difference between current score and new score is added to the total.
    """
    r = get_redis_client()  # ✅ CALL INSIDE FUNCTION
    ticket_key = f"user:{username}:ticket:{ticket_id}"
    total_score_key = f"user:{username}:total_score"

    existing_score = int(r.get(ticket_key) or 0)

    # ✅ Don't re-award if full credit (100+) already given
    if existing_score >= 100:
        return None  # Indicate no score change

    # ✅ Only add the difference (e.g., upgrading from 60 → 100 adds 40)
    score_delta = max(0, int(new_score) - existing_score)
    r.set(ticket_key, new_score)

    # ✅ Update total score
    current_total = int(r.get(total_score_key) or 0)
    new_total = current_total + score_delta
    r.set(total_score_key, new_total)

    return new_total

