# sentence_transformer.py

from sentence_transformers import SentenceTransformer, util

# Load the Sentence Transformer model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_cosine_similarity(text1, text2):
    """
    Calculate and return the cosine similarity between two input strings.
    """
    # Encode both sentences
    embedding1 = model.encode(text1, normalize_embeddings=True)
    embedding2 = model.encode(text2, normalize_embeddings=True)

    # Calculate cosine similarity
    similarity = util.cos_sim(embedding1, embedding2).item()

    return similarity

# Test block
if __name__ == "__main__":
    print("🔬 Sentence Transformer Cosine Similarity Tester")
    print("Type 'exit' at any prompt to quit.\n")

    while True:
        text1 = input("Enter first sentence: ").strip()
        if text1.lower() == "exit":
            break

        text2 = input("Enter second sentence: ").strip()
        if text2.lower() == "exit":
            break

        similarity = calculate_cosine_similarity(text1, text2)
        print(f"\n✅ Cosine Similarity: {similarity:.4f}")
        print("\n" + "=" * 60 + "\n")

