# grading_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from settings import (
    INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET,
    OLLAMA_URL, OLLAMA_MODEL,
    STRUCTURED_GRADING_PROMPT, STRUCTURED_GRADING_FEW_SHOT,
    UNSTRUCTURED_GRADING_PROMPT
)

app = FastAPI()

# InfluxDB setup
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

### ==== MODELS ====

class StructuredGradeRequest(BaseModel):
    player_response: str
    ticket: dict

class UnstructuredGradeRequest(BaseModel):
    player_input: str
    root_cause: str

### ==== ENDPOINTS ====

@app.post("/grade")
def grade_response(request: StructuredGradeRequest):
    prompt = f"""
{STRUCTURED_GRADING_PROMPT}

{STRUCTURED_GRADING_FEW_SHOT}

Ticket:
Minimal: {request.ticket['minimal_credit']}
Partial: {request.ticket['partial_credit']}
Full: {request.ticket['full_credit']}

Player: "{request.player_response}"

Give your Grade and Feedback in this JSON format:
{{"grade": number, "feedback": "string"}}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {"temperature": 0.2},
        "stream": False
    }

    start = time.perf_counter()
    response = requests.post(OLLAMA_URL, json=payload)
    duration = time.perf_counter() - start

    # Log to InfluxDB
    point = Point("llm_structured_response").field("duration", duration)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    try:
        result = response.json()["response"].strip()
        parsed = json.loads(result)
        return {"grade": parsed['grade'], "feedback": parsed['feedback']}
    except Exception as e:
        print("[ERROR] Structured LLM response parsing failed.")
        print(response.text)
        raise HTTPException(status_code=500, detail="Failed to parse LLM structured response.")

@app.post("/unstructured_grade")
def unstructured_grade(request: UnstructuredGradeRequest):
    full_prompt = UNSTRUCTURED_GRADING_PROMPT + f"""

Original Network Issue Summary:
{request.root_cause}

Student Diagnosis Summary:
{request.player_input}
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

    # Log to InfluxDB
    point = Point("llm_unstructured_response").field("duration", duration)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    try:
        result = response.json()["response"].strip()
        parsed = json.loads(result)
        return {"score": parsed["score"], "reason": parsed["reason"]}
    except Exception as e:
        print("[ERROR] Unstructured LLM response parsing failed.")
        print(response.text)
        raise HTTPException(status_code=500, detail="Failed to parse LLM unstructured response.")

