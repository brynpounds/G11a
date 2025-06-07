# grade_response.py

from redis_client import get_redis_client
from normalize import normalize_sentence
from sentence_transformers import SentenceTransformer, util

# Load model once at top
model = SentenceTransformer("all-MiniLM-L6-v2")

def grade_response(issue_id: str, player_input: str, threshold: float = 0.8):
    """
    Grade a player response using sentence similarity against expected answer.
    """
    r = get_redis_client()
    
    # Load expected answer
    expected = r.get(f"investigation:{issue_id}:answer")
    if not expected:
        return {"error": f"Issue '{issue_id}' not found."}

    # Normalize
    expected = normalize_sentence(expected.decode() if isinstance(expected, bytes) else expected)
    player = normalize_sentence(player_input)

    # Embeddings
    expected_embedding = model.encode(expected, convert_to_tensor=True)
    player_embedding = model.encode(player, convert_to_tensor=True)

    # Similarity
    score = util.cos_sim(expected_embedding, player_embedding).item()

    return {
        "similarity": round(score, 3),
        "correct": score >= threshold,
        "normalized_expected": expected,
        "normalized_input": player
    }


if __name__ == "__main__":
    print("🧠 Grade a player response\n")
    issue_id = input("Enter investigation ID (e.g., inv001): ").strip()
    player_input = input("Enter player response: ").strip()

    result = grade_response(issue_id, player_input)
    
    print("\n📊 Grading Result:")
    if "error" in result:
        print("❌", result["error"])
    else:
        print(f"- Similarity: {result['similarity']}")
        print(f"- Correct: {'✅ Yes' if result['correct'] else '❌ No'}")
        print(f"- Normalized Input: {result['normalized_input']}")
        print(f"- Normalized Answer: {result['normalized_expected']}")

