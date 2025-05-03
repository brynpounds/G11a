# unstructured_llm_grading.py

import requests
import json
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from settings import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from settings import OLLAMA_URL, OLLAMA_MODEL
from settings import UNSTRUCTURED_GRADING_PROMPT

# InfluxDB config
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Ollama config (now imported from settings)
# OLLAMA_URL and OLLAMA_MODEL are already defined in settings.py

def evaluate_unstructured_from_root_cause(player_input: str, root_cause: str):
    """
    Use the strict grading prompt with root_cause and player_input.
    """
    full_prompt = UNSTRUCTURED_GRADING_PROMPT + f"""

Original Network Issue Summary:
{root_cause}

Student Diagnosis Summary:
{player_input}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "options": {"temperature": 0.2},
        "stream": False
    }

    start = time.perf_counter()
    response = requests.post(OLLAMA_URL, json=payload)
    duration = time.perf_counter() - start

    # Log duration to InfluxDB
    point = Point("llm_unstructured_response").field("duration", duration)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    try:
        result = response.json()["response"].strip()
        parsed = json.loads(result)
        return parsed["score"], parsed["reason"]
    except Exception as e:
        print("[ERROR] LLM unstructured grading failed.")
        print(response.text)
        print(f"Exception: {e}")
        return 0, "Failed to parse LLM response."

# === Manual test ===
if __name__ == "__main__":
    root_cause = input("Enter canonical root cause: ").strip()
    player_input = input("Enter player diagnosis: ").strip()

    score, reason = evaluate_unstructured_from_root_cause(player_input, root_cause)

    print(f"\n📊 Score: {score}")
    print(f"📝 Reason: {reason}")

