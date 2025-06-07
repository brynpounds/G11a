# list_investigations.py

import re
from redis_client import get_redis_client

def list_investigations():
    """
    List all investigation questions stored in Redis.
    Returns a list of dicts: [{"issue_id": ..., "question": ..., "redis_key": ...}, ...]
    """
    r = get_redis_client()
    keys = r.keys("investigation:*:question")
    
    investigations = []
    for key in keys:
        # Ensure key is a string
        if isinstance(key, bytes):
            key = key.decode()

        match = re.match(r"investigation:(.*):question", key)
        if match:
            issue_id = match.group(1)
            question = r.get(key)
            if isinstance(question, bytes):
                question = question.decode()
            investigations.append({
                "issue_id": issue_id,
                "question": question,
                "redis_key": key
            })
    
    return sorted(investigations, key=lambda x: x["issue_id"])


if __name__ == "__main__":
    print("📋 Stored Investigations:\n")
    for inv in list_investigations():
        print(f"- Key: {inv['redis_key']}")
        print(f"  ID: {inv['issue_id']}")
        print(f"  Q:  {inv['question']}\n")

