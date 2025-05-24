# record_score.py

from redis_client import get_redis_client

def record_player_score(username, ticket_id, new_score):
    """
    Records or adjusts a player's score for a specific ticket.

    Scoring Logic:
    - If new_score is negative (penalty):
        • Subtract from total_score only.
        • Do NOT update ticket score.
        • Total score will not go below 0.

    - If new_score is positive:
        • Do NOT update if existing score is already 100 or higher.
        • Only apply the difference if new_score is higher than existing.
        • Only update ticket score if it's an improvement.

    Returns:
        - Updated total_score (int), or
        - None if no change was applied.
    """
    r = get_redis_client()

    ticket_key = f"user:{username}:ticket:{ticket_id}"
    total_score_key = f"user:{username}:total_score"

    existing_score = int(r.get(ticket_key) or 0)
    current_total = int(r.get(total_score_key) or 0)

    if int(new_score) < 0:
        # Negative = penalty (deduct from total only)
        penalty = int(new_score)
        new_total = max(0, current_total + penalty)
        r.set(total_score_key, new_total)
        return new_total

    # If ticket already has full credit, ignore
    if existing_score >= 100:
        return None

    # Only reward improvements
    if int(new_score) > existing_score:
        score_delta = int(new_score) - existing_score
        r.set(ticket_key, int(new_score))
        new_total = current_total + score_delta
        r.set(total_score_key, new_total)
        return new_total

    # No improvement → no change
    return None

