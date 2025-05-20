# add_trouble_ticket.py

import json
from redis_client import get_redis_client

def prompt_for_ticket():
    print("📝 Enter details for the new trouble ticket:")
    ticket = {
        "id": int(input("ID: ")),
        "description": input("Description: "),
        "root_cause": input("Root Cause: "),
        "minimal_credit": input("Minimal Credit: "),
        "partial_credit": input("Partial Credit: "),
        "full_credit": input("Full Credit: ")
    }
    return ticket

def append_trouble_ticket(ticket):
    r = get_redis_client()
    
    try:
        # Fetch existing tickets from Redis
        current_data = r.get("trouble_tickets")
        tickets = json.loads(current_data) if current_data else []

        # Add new ticket
        tickets.append(ticket)

        # Save back to Redis
        r.set("trouble_tickets", json.dumps(tickets))
        print(f"✅ Added trouble_ticket ID {ticket['id']} to Redis.")
    except Exception as e:
        print(f"❌ Error appending trouble_ticket: {e}")

if __name__ == "__main__":
    new_ticket = prompt_for_ticket()
    append_trouble_ticket(new_ticket)

