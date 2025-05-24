# grading_api.py

from write_to_structured_cache import write_structured_entry_to_cache
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
from redis_client import get_redis_client

class TroubleTicket(BaseModel):
    id: int
    description: str
    root_cause: str
    minimal_credit: str
    partial_credit: str
    full_credit: str

class TicketID(BaseModel):
    id: int

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

class UnstructuredTicket(BaseModel):
    id: int
    issue: str
    root_cause: str
    scoring: str

class StructuredCacheEntry(BaseModel):
    ticket_id: int
    input: str
    grade: int
    feedback: str

### ==== ENDPOINTS ====

@app.post("/add_structured_cache")
def add_structured_cache(entry: StructuredCacheEntry):
    try:
        write_structured_entry_to_cache(entry.dict())
        return {"message": f"✅ Structured cache entry for ticket {entry.ticket_id} added."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@app.post("/add_trouble_ticket")
def add_trouble_ticket(ticket: TroubleTicket):
    r = get_redis_client()
    current_data = r.get("trouble_tickets")
    tickets = json.loads(current_data) if current_data else []

    if any(t["id"] == ticket.id for t in tickets):
        raise HTTPException(status_code=400, detail=f"Ticket with ID {ticket.id} already exists.")

    tickets.append(ticket.dict())
    r.set("trouble_tickets", json.dumps(tickets))
    return {"message": f"✅ Ticket ID {ticket.id} added successfully."}

@app.post("/remove_trouble_ticket")
def remove_trouble_ticket(ticket_id: TicketID):
    r = get_redis_client()
    current_data = r.get("trouble_tickets")
    if not current_data:
        raise HTTPException(status_code=404, detail="No trouble tickets found.")

    tickets = json.loads(current_data)
    updated = [t for t in tickets if t["id"] != ticket_id.id]

    if len(updated) == len(tickets):
        raise HTTPException(status_code=404, detail=f"No ticket found with ID {ticket_id.id}.")

    r.set("trouble_tickets", json.dumps(updated))
    return {"message": f"✅ Ticket ID {ticket_id.id} removed successfully."}

@app.get("/list_all_tickets")
def list_all_tickets():
    r = get_redis_client()

    structured_raw = r.get("trouble_tickets")
    unstructured_raw = r.get("network_issues")

    structured = json.loads(structured_raw) if structured_raw else []
    unstructured = json.loads(unstructured_raw) if unstructured_raw else []

    return {
        "structured_tickets": structured,
        "unstructured_tickets": unstructured
    }

@app.post("/add_unstructured_ticket")
def add_unstructured_ticket(ticket: UnstructuredTicket):
    r = get_redis_client()

    # Save to array
    raw = r.get("network_issues")
    issues = json.loads(raw) if raw else []

    if any(i["id"] == ticket.id for i in issues):
        raise HTTPException(status_code=400, detail=f"Issue with ID {ticket.id} already exists.")

    issues.append(ticket.dict())
    r.set("network_issues", json.dumps(issues))

    # Save individual key
    r.set(f"issue:{ticket.id}", json.dumps(ticket.dict()))

    return {"message": f"✅ Unstructured ticket ID {ticket.id} added."}

@app.post("/remove_unstructured_ticket")
def remove_unstructured_ticket(ticket_id: TicketID):
    r = get_redis_client()

    # Delete individual key
    r.delete(f"issue:{ticket_id.id}")

    # Remove from array
    raw = r.get("network_issues")
    if not raw:
        raise HTTPException(status_code=404, detail="No unstructured tickets found.")

    issues = json.loads(raw)
    filtered = [i for i in issues if i["id"] != ticket_id.id]

    if len(filtered) == len(issues):
        raise HTTPException(status_code=404, detail=f"No issue with ID {ticket_id.id} found.")

    r.set("network_issues", json.dumps(filtered))
    return {"message": f"✅ Unstructured ticket ID {ticket_id.id} removed."}


