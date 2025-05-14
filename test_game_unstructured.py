import redis
import json
import random
from normalize import normalize_sentence
from sentence_transformer import calculate_cosine_similarity
from unstructured_llm_grading import evaluate_unstructured_from_root_cause
from write_to_structured_cache import write_structured_entry_to_cache, r as redis_conn
from redis_client import get_redis_client

# Redis setup
r = get_redis_client()

def get_random_unstructured_issue():
    keys = r.keys("issue:*")
    if not keys:
        print("❌ No unstructured issues found in Redis.")
        return None
    key = random.choice(keys)
    return json.loads(r.get(key))

def main():
    issue = get_random_unstructured_issue()
    if not issue:
        return

    print("\n🌐 Unstructured Network Issue")
    print(f"ID:          {issue['id']}")
    print(f"Issue:       {issue['issue']}")
    print(f"Root Cause:  {issue['root_cause']}")

    player_input = input("\n🧠 Enter your troubleshooting diagnosis: ").strip()
    if not player_input:
        print("⚠️ No input provided.")
        return

    normalized = normalize_sentence(player_input)
    print(f"\n✅ Normalized Input:\n{normalized}")

    redis_key = f"graded:{issue['id']}:{normalized}"
    if redis_conn.exists(redis_key):
        cached = redis_conn.hgetall(redis_key)
        print("\n✅ 🎯 Cache HIT")
        print(f"🏁 Score: {cached['grade']}")
        print(f"📝 Feedback: {cached['feedback']}")
        return

    similarity = calculate_cosine_similarity(normalized, normalize_sentence(issue["root_cause"]))
    print(f"\n📏 Similarity to root cause: {similarity:.4f}")

    if similarity < 0.5:
        print("❌ Not similar enough to consider a valid match.")
        return

    print("\n🧠 Submitting to LLM for evaluation...")
    score, feedback = evaluate_unstructured_from_root_cause(issue["root_cause"], normalized)

    print(f"\n🏁 Score: {score}")
    print(f"📝 Feedback: {feedback}")

    entry = {
        "ticket_id": issue["id"],
        "input": player_input,
        "grade": score,
        "feedback": feedback,
        "source": "game_play"
    }

    write_structured_entry_to_cache(entry)

if __name__ == "__main__":
    main()

