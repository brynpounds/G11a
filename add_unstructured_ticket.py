# add_unstructured_ticket.py

import json
from redis_client import get_redis_client

def prompt_for_unstructured_issue():
    print("📝 Enter details for the new unstructured network issue:")
    issue = {
        "id": int(input("ID: ")),
        "issue": input("Issue Summary: "),
        "root_cause": input("Root Cause: "),
        "scoring": input("Scoring Instructions: ")
    }
    return issue

def add_unstructured_issue(issue):
    r = get_redis_client()

    # Add to individual Redis key
    redis_key = f"issue:{issue['id']}"
    r.set(redis_key, json.dumps(issue))

    # Add to the full array
    current = r.get("network_issues")
    network_issues = json.loads(current) if current else []
    
    if any(i["id"] == issue["id"] for i in network_issues):
        print(f"❌ Issue with ID {issue['id']} already exists.")
        return

    network_issues.append(issue)
    r.set("network_issues", json.dumps(network_issues))
    print(f"✅ Issue ID {issue['id']} added to Redis.")

if __name__ == "__main__":
    new_issue = prompt_for_unstructured_issue()
    add_unstructured_issue(new_issue)

