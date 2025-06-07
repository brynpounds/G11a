# add_investigation.py

from redis_client import get_redis_client

def add_investigation(issue_id: str, question: str, expected_answer: str):
    """
    Store a new investigation question and expected answer in Redis.
    """
    r = get_redis_client()
    r.set(f"investigation:{issue_id}:question", question)
    r.set(f"investigation:{issue_id}:answer", expected_answer)
    print(f"\n✅ Investigation '{issue_id}' added successfully.")


if __name__ == "__main__":
    print("🧠 Add a New Investigation\n")

    def prompt(label):
        while True:
            value = input(f"{label}: ").strip()
            if value:
                return value
            print(f"❌ {label} cannot be empty. Try again.")

    issue_id = prompt("Enter issue ID (e.g., inv001)")
    question = prompt("Enter investigation question")
    expected_answer = prompt("Enter expected answer")

    add_investigation(issue_id, question, expected_answer)

