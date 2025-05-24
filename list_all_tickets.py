# list_all_tickets.py

import json
from redis_client import get_redis_client

def list_all_tickets():
    r = get_redis_client()

    # Structured trouble tickets
    structured_raw = r.get("trouble_tickets")
    structured = json.loads(structured_raw) if structured_raw else []

    # Unstructured network issues
    unstructured_raw = r.get("network_issues")
    unstructured = json.loads(unstructured_raw) if unstructured_raw else []

    print("\n📋 Structured Trouble Tickets:")
    for t in structured:
        print(f"""
🆔 ID: {t['id']}
📝 Description: {t['description']}
🔍 Root Cause: {t['root_cause']}
⚠️ Minimal Credit: {t['minimal_credit']}
✅ Partial Credit: {t['partial_credit']}
🏆 Full Credit: {t['full_credit']}
""")

    print("\n📋 Unstructured Network Issues:")
    for i in unstructured:
        print(f"""
🆔 ID: {i['id']}
🛠️ Issue: {i['issue']}
🔍 Root Cause: {i['root_cause']}
🎯 Scoring: {i['scoring']}
""")

if __name__ == "__main__":
    list_all_tickets()

