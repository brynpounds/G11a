import requests
from settings import OLLAMA_URL, OLLAMA_MODEL

# Ollama configuration is now imported from settings.py

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

if __name__ == "__main__":
    test_ollama_connection()