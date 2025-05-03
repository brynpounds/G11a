from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_DECODE_RESPONSES = os.getenv("REDIS_DECODE_RESPONSES", "True").lower() in ("true", "1", "yes")

# Redis Sentinel settings
REDIS_USE_SENTINEL = os.getenv("REDIS_USE_SENTINEL", "False").lower() in ("true", "1", "yes")
REDIS_SENTINEL_HOSTS = os.getenv("REDIS_SENTINEL_HOSTS", "").split(",")  # Comma-separated list of host:port
REDIS_SENTINEL_SERVICE_NAME = os.getenv("REDIS_SENTINEL_SERVICE_NAME", "mymaster")

# InfluxDB settings
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "_ngsl81ZgEW-zivbImIl6kjANpltSdb6Pu-SPe116a7tBk7epMizCTHN2NgO8-xfNsrhaOTNijZRg352HS4V4w==")
INFLUX_ORG = os.getenv("INFLUX_ORG", "gotn")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "gotn-metrics")

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Prompts
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

# Structured Grading Prompt
STRUCTURED_GRADING_PROMPT = """
You are a network troubleshooting grader. Be strict.

Rules:
- If player identifies all Minimal Credit concepts: 25 points.
- If player identifies all Partial Credit concepts: 60 points.
- If player identifies all Full Credit concepts including numbers: 100 points.
- Don't get caught up with specific description terms. wrong = incorrect = bad = "error with"
- Be forgiving if different non-technical words mean the same thing.
- Be careful with numbers in full credit (e.g. VLAN 101). They are meaningful.
- Otherwise: 0 points.
"""

# Few-shot examples for structured grading
STRUCTURED_GRADING_FEW_SHOT = """
Example 1:
"root_cause": "Border Gateway Protocol AS set to 65001",
"minimal_credit": "Border Gateway Protocol",
"partial_credit": "Border Gateway Protocol AS",
"full_credit": "Border Gateway Protocol AS set to 65001"
Player: "the Border Gateway Protocol AS set to 65001"
Grade: 100
Feedback: Player identified the Border Gateway Protocol AS set to 65001, and specifically included the AS number.

Example 2:
"root_cause": "Open Shortest Path First area 0 is not extended to RouterA",
"minimal_credit": "Open Shortest Path First",
"partial_credit": "Open Shortest Path First area 0",
"full_credit": "Open Shortest Path First area 0 RouterA"
Player: "there is an error with RouterA Open Shortest Path First area 0"
Grade: 100
Feedback: Player identified the Open Shortest Path First area 0 is not running on RouterA, and specifically included the area number.
"""

# Example of using the settings
if DEBUG:
    print("Debug mode is enabled.")