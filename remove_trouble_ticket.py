# remove_trouble_ticket.py

import json
from redis_client import get_redis_client

def remove_ticket_by_id(ticket_id):
    r = get_redis_client()

    try:
        current_data = r.get("trouble_tickets")
        if not current_data:
            print("⚠️ No trouble_tickets found in Redis.")
            return

        tickets = json.loads(current_data)
        original_count = len(tickets)

        # Filter out ticket with matching ID
        updated_tickets = [t for t in tickets if t["id"] != ticket_id]

        if len(updated_tickets) == original_count:
            print(f"❌ No ticket with ID {ticket_id} was found.")
        else:
            r.set("trouble_tickets", json.dumps(updated_tickets))
            print(f"✅ Ticket ID {ticket_id} removed from Redis.")
    except Exception as e:
        print(f"❌ Error removing trouble_ticket: {e}")

if __name__ == "__main__":
    try:
        ticket_id = int(input("Enter the trouble_ticket ID to remove: "))
        remove_ticket_by_id(ticket_id)
    except ValueError:
        print("❌ Invalid ID. Must be an integer.")

