import requests
import redis
import json
from settings import OLLAMA_URL, OLLAMA_MODEL, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_DECODE_RESPONSES

# Ollama configuration is now imported from settings.py

# Initialize Redis connection
r = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=REDIS_DECODE_RESPONSES
)

def test_ollama_connection():
    """
    Test if the Ollama API is running and the mistral model is accessible.
    """
    test_prompt = "Hello, can you confirm that the Ollama API is working?"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": test_prompt,
        "options": {"temperature": 0.2},
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            print("✅ Ollama API is running.")
            print("Response:", response.json())
        else:
            print("❌ Failed to connect to Ollama API.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("❌ Error connecting to Ollama API.")
        print(f"Exception: {e}")

def test_trouble_tickets_from_redis():
    """
    Test if trouble_tickets can be retrieved from the game_data key in Redis.
    """
    try:
        # Fetch game_data from Redis
        game_data_json = r.get("game_data")
        if game_data_json:
            game_data = json.loads(game_data_json)
            trouble_tickets = game_data.get("trouble_tickets", [])
            if trouble_tickets:
                print("✅ Successfully retrieved trouble_tickets from Redis:")
                for ticket in trouble_tickets:
                    print(f"ID: {ticket['id']}, Description: {ticket['description']}")
            else:
                print("❌ No trouble_tickets found in game_data.")
        else:
            print("❌ No game_data found in Redis. Please ensure the data is loaded.")
    except Exception as e:
        print("❌ Error retrieving trouble_tickets from Redis.")
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_ollama_connection()
    test_trouble_tickets_from_redis()