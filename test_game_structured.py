# test_game_structured.py

import redis
import json
import random
from normalize import normalize_sentence
from sentence_transformer import calculate_cosine_similarity
from structured_llm_grading import llm_grade
from write_to_structured_cache import write_structured_entry_to_cache, r as redis_conn

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_random_ticket():
    data = r.get("game_data")
    if not data:
        print("❌ Could not find 'game_data' in Redis.")
        return None

    game_data = json.loads(data)
    tickets = game_data.get("trouble_tickets", [])

    if not tickets:
        print("❌ No trouble tickets found.")
        return None

    return random.choice(tickets)

def display_ticket(ticket):
    print("\n🎫 Trouble Ticket")
    print(f"ID:             {ticket['id']}")
    print(f"Description:    {ticket['description']}")
    print(f"Root Cause:     {ticket['root_cause']}")
    print(f"Minimal Credit: {ticket['minimal_credit']}")
    print(f"Partial Credit: {ticket['partial_credit']}")
    print(f"Full Credit:    {ticket['full_credit']}")

def precheck_similarity(normalized_input, ticket, threshold=0.55):
    """Return True if input is close enough to warrant LLM grading."""
    credit_fields = {
        "minimal_credit": ticket.get("minimal_credit", ""),
        "partial_credit": ticket.get("partial_credit", ""),
        "full_credit": ticket.get("full_credit", "")
    }

    for label, reference in credit_fields.items():
        if reference.strip():
            similarity = calculate_cosine_similarity(normalized_input, reference)
            print(f"📊 Similarity to {label}: {similarity:.4f}")
            if similarity >= threshold:
                return True
    return False

def main():
    ticket = get_random_ticket()
    if not ticket:
        return

    display_ticket(ticket)

    user_input = input("\n🧠 Enter your troubleshooting response: ").strip()
    if not user_input:
        print("⚠️ No response entered.")
        return

    normalized = normalize_sentence(user_input)
    print("\n✅ Normalized Response:")
    print(normalized)

    redis_key = f"graded:{ticket['id']}:{normalized}"
    if redis_conn.exists(redis_key):
        print("✅ 🎯 Cache HIT — skipping LLM.")
        cached = redis_conn.hgetall(redis_key)
        print(f"\n🏁 Score: {cached['grade']}")
        print(f"📝 Feedback: {cached['feedback']}")
        return

    if not precheck_similarity(normalized, ticket):
        print("\n❌ Input not similar enough to known answers. No score awarded.")
        return

    print("\n🧠 Submitting to LLM for structured grading...")
    print(f"\n🛠 DEBUG ticket type: {type(ticket)}")
    print(f"🛠 DEBUG ticket: {ticket}")
    score, feedback = llm_grade(normalized, ticket)

    print(f"\n🏁 Score: {score}")
    print(f"📝 Feedback: {feedback}")

    try:
        entry = {
            "ticket_id": ticket["id"],
            "input": user_input,
            "grade": int(score),
            "feedback": feedback
        }
        write_structured_entry_to_cache(entry)
    except Exception as e:
        print(f"❌ Failed to write to cache: {e}")

if __name__ == "__main__":
    main()

