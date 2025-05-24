from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# DEBUG mode from the .env file
SHOW_DEBUG_UI = os.getenv("SHOW_DEBUG_UI", "False").lower() in ("true", "1", "yes")

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
You are acting as a strict and precise network troubleshooting instructor evaluating student responses.

Your goal is to train elite troubleshooters. Students must demonstrate complete understanding by including all required diagnostic elements. Responses must be technically accurate and location-specific when relevant.

Scoring Criteria:
- Award 200 points ONLY if the response includes ALL of the following:
  1. The correct **site or location**, if one is mentioned in the original issue.
  2. The correct **technical concept** (e.g., a product name, protocol, or configuration).
  3. The correct **problem or action** (e.g., "is missing", "not configured", "disabled").

Clarifications:
- Accept natural phrasing and paraphrasing, but all 3 elements must be clearly stated.
- If a location is specified in the original issue, the student **must explicitly name it**.
  - Examples: “at [site name]”, “[site name] network”, “in [site name]”
  - Do **not** infer from context — the name must be present.
- Do not award credit for vague responses like “there’s a problem” or “something is wrong.”
- Do not award partial credit — **all or nothing**.

Scoring:
- If all 3 required elements are found → score: 200
- If any element is missing or unclear → score: 0

Respond ONLY in this JSON format:
{
  "score": (integer, 200 or 0),
  "reason": "Brief feedback message."
}
"""

# Structured Grading Prompt
STRUCTURED_GRADING_PROMPT = """
You are a network troubleshooting grader. Be strict.

Rules:
- If player identifies all Minimal Credit concepts: 10 points.
- If player identifies all Partial Credit concepts: 30 points.
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
Feedback: Player identified the Open Shortest Path First area 0 is not running on RouterA, and specifically included the area number. We can infer that "an error" means the same thing as "incorrect".

Example 3:
"root_cause": "Cisco Meraki MX in Kansas City has high CPU",
"minimal_credit": "high CPU",
"partial_credit": "Cisco Meraki MX high CPU",
"full_credit": "Cisco Meraki MX in Kansas City has high CPU"
Player: "The Meraki MX has high CPU"
Grade: 60
Feedback: Partial Credit because Player identified the Cisco Meraki MX has high CPU, but missed the key detail of it being in Kansas City.

Example 4:
"root_cause": "Cisco Umbrella is not configured at Site9",
"minimal_credit": "Cisco Umbrella",
"partial_credit": "Cisco Umbrella not configured",
"full_credit": "Cisco Umbrella is not configured at Site9"
Player: "Cisco Umbrella is unconfigured"
Grade: 60
Feedback: Partial Credit because Player identified Cisco Umbrella is not configured, but missed the key detail of it being at Site9.

Example 5:
"root_cause": "TALOS is not configured at Site10",
"minimal_credit": "TALOS not configured",
"partial_credit": "",
"full_credit": "TALOS is not configured at Site10"
Player: "Site10 has lots of problems"
Grade: 0
Feedback: Zero credit. All the player did was write a vague answer with the site name and their answer included nothing about network troubleshooting.

Example 6:
"root_cause": "Domain Name System setting is incorrect",
"minimal_credit": "Domain Name System",
"partial_credit": "",
"full_credit": "Domain Name System setting is incorrect"
Player: "wrong dns"
Grade: 100
Feedback: Full credit. The player identified the issue. We can infer that "incorrect" and the players use of the word "wrong" mean the same thing in this diagnosis.
"""

# Example of using the settings
if DEBUG:
    print("Debug mode is enabled.")
