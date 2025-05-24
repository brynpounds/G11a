# remove_unstructured_ticket.py

import json
from redis_client import get_redis_client

def remove_unstructured_issue(issue_id):
    r = get_redis_client()

    # Remove individual key
    r.delete(f"issue:{issue_id}")

    # Remove from array
    current = r.get("network_issues")
    if not current:
        print("⚠️ No network_issues found in Redis.")
        return

    issues = json.loads(current)
    new_issues = [i for i in issues if i["id"] != issue_id]

    if len(issues) == len(new_issues):
        print(f"❌ No issue with ID {issue_id} was found.")
        return

    r.set("network_issues", json.dumps(new_issues))
    print(f"✅ Issue ID {issue_id} removed from Redis.")

if __name__ == "__main__":
    try:
        issue_id = int(input("Enter the unstructured issue ID to remove: "))
        remove_unstructured_issue(issue_id)
    except ValueError:
        print("❌ Invalid ID. Must be an integer.")

