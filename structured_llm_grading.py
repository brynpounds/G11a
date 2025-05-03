# structured_llm_grading.py

import requests
import json
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from settings import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from settings import STRUCTURED_GRADING_PROMPT, STRUCTURED_GRADING_FEW_SHOT

# InfluxDB configuration
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Ollama endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"

def llm_grade(player_response, ticket):
    print("🚨 [LLM INPUT DEBUG] Player response being graded:")
    print(player_response)

    prompt = f"""
{STRUCTURED_GRADING_PROMPT}

{STRUCTURED_GRADING_FEW_SHOT}

Ticket:
Minimal: {ticket['minimal_credit']}
Partial: {ticket['partial_credit']}
Full: {ticket['full_credit']}

Player: "{player_response}"

Give your Grade and Feedback in this JSON format:
{{"grade": number, "feedback": "string"}}
"""

    payload = {
        "model": "mistral",
        "prompt": prompt,
        "options": {"temperature": 0.2},
        "stream": False
    }

    start = time.perf_counter()
    response = requests.post(OLLAMA_URL, json=payload)
    duration = time.perf_counter() - start

    # Record to InfluxDB
    point = Point("llm_structured_response").field("duration", duration)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    try:
        result = response.json()["response"].strip()
        parsed = json.loads(result)
        return parsed['grade'], parsed['feedback']
    except Exception as e:
        print("[ERROR] LLM response parsing failed.")
        print(response.text)
        print(f"Exception: {e}")
        return 0, "Failed to parse LLM response."

# === Manual test ===
if __name__ == "__main__":
    test_ticket = {
        "description": "Cisco Umbrella is not working at Site 9",
        "root_cause": "Cisco Umbrella is not configured at Site9",
        "minimal_credit": "Cisco Umbrella",
        "partial_credit": "Cisco Umbrella not configured",
        "full_credit": "Cisco Umbrella is not configured at Site9"
    }

    player_input = input("Enter your troubleshooting response for Cisco Umbrella is not configured at Site9: ")
    grade, feedback = llm_grade(player_input, test_ticket)

    print(f"\n📊 Grade: {grade}")
    print(f"📝 Feedback: {feedback}")

