# structured_llm_grading.py

import requests
import json
import random
from normalize import normalize_sentence
from sentence_transformer import calculate_cosine_similarity

# Replace with your running Ollama URL
OLLAMA_URL = "http://localhost:11434/api/generate"

# Few-shot examples for grading prompt
few_shot_examples = """
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

def llm_grade(player_response, ticket):
    print("🚨 [LLM INPUT DEBUG] Player response being graded:")
    print(player_response)
    prompt = f"""
You are a network troubleshooting grader. Be strict.

Rules:
- If player identifies all Minimal Credit concepts: 25 points.
- If player identifies all Partial Credit concepts: 60 points.
- If player identifies all Full Credit concepts including numbers: 100 points.
- Don't get caught up with specific description terms. wrong = incorrect = bad = "error with"
- Be forgiving if different non-technical words mean the same thing.
- Be careful with numbers in full credit (e.g. VLAN 101). They are meaningful.
- Otherwise: 0 points.

{few_shot_examples}

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

    response = requests.post(OLLAMA_URL, json=payload)

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

