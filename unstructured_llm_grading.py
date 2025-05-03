# unstructured_llm_grading.py

import requests
import json
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB config
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "_ngsl81ZgEW-zivbImIl6kjANpltSdb6Pu-SPe116a7tBk7epMizCTHN2NgO8-xfNsrhaOTNijZRg352HS4V4w=="
INFLUX_ORG = "gotn"
INFLUX_BUCKET = "gotn-metrics"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# >>> DO NOT MODIFY THIS PROMPT <<<
UNSTRUCTURED_GRADING_PROMPT = """
You are acting as a strict network troubleshooting instructor evaluating student responses.

Students must be judged harshly but fairly, with no partial credit.

Rules:
- You are helping students become elite network troubleshooters.
- Giving too much credit is harmful to their real-world growth.
- You must be firm but polite — no harsh language or blame.

Scoring Criteria:
- Award 100 points only if the student correctly covers all major elements.
- Award 0 points if the student misses any major elements.

Major elements that must be present:
1. If the original issue mentions a site (e.g., "Site9" or "Site10"), the student's diagnosis MUST specifically reference the correct site.
2. If the original issue includes a technical category (e.g., "TALOS", "Umbrella", "MS120-8"), the student MUST correctly identify that technical concept.
3. If the original issue implies an action or issue (e.g., "not configured", "missing license"), the student MUST correctly state the action or problem.

Additional Instructions:
- NO partial credit is allowed. All required elements must be present for a full score.
- If any element is missing, award 0 points.
- If full credit is awarded, respond: "Well done identifying all key elements!"
- If any element is missing, respond: "We didn't find that issue. Please try again."

Respond ONLY in this strict JSON format:

{
  "score": (integer, 100 or 0),
  "reason": "Brief feedback message."
}
"""

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

