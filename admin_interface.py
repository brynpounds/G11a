# admin_interface.py

import streamlit as st
import json
from redis_client import get_redis_client
from remove_trouble_ticket import remove_ticket_by_id
from add_trouble_ticket import append_trouble_ticket
from update_player_total_score import update_total_score
from add_unstructured_ticket import add_unstructured_issue
from remove_unstructured_ticket import remove_unstructured_issue

# Sidebar password check
st.title("🔐 Admin Panel")
password = st.text_input("Enter admin password", type="password")
if password != "Cisco123#":
    st.stop()

st.success("✅ Access granted.")

# Connect to Redis
r = get_redis_client()

# Admin action selector
action = st.selectbox("Choose an action", [
    "Check Player Info",
    "Add Trouble Ticket",
    "Remove Trouble Ticket",
    "Update Player Total Score",
    "Add Unstructured Issue",
    "Remove Unstructured Issue",
    "Delete Player"
])

# Fetch all player usernames for dropdown
all_user_keys = r.keys("user:*")
player_usernames = sorted(set(
    key.split(":")[1] for key in all_user_keys
    if len(key.split(":")) == 2 and not key.endswith(":total_score")
))

# Action: Check Player Info
if action == "Check Player Info":
    selected_user = st.selectbox("Select Player Email", player_usernames)
    if st.button("Lookup Info"):
        username = selected_user.strip().lower().replace(" ", "_")
        user_key = f"user:{username}"
        total_key = f"user:{username}:total_score"

        if not r.exists(user_key):
            st.error(f"❌ User '{username}' does not exist.")
        else:
            st.markdown("### 📦 Account Info")
            user_data = r.hgetall(user_key)
            for key, value in user_data.items():
                st.write(f"**{key}**: {value}")

            st.markdown("### 🎯 Total Score")
            total_score = r.get(total_key) or "0"
            st.write(f"`{total_score}` points")

            st.markdown("### 📝 Ticket Scores")
            ticket_keys = r.keys(f"user:{username}:ticket:*")
            all_ticket_ids = set()
            for ticket in json.loads(r.get("trouble_tickets") or "[]"):
                all_ticket_ids.add(str(ticket["id"]))
            for issue in json.loads(r.get("network_issues") or "[]"):
                all_ticket_ids.add(str(issue["id"]))

            for ticket_id in sorted(all_ticket_ids, key=int):
                ticket_key = f"user:{username}:ticket:{ticket_id}"
                score = r.get(ticket_key) or "0"
                st.write(f"Ticket `{ticket_id}`: `{score}` points")

# Action: Add Trouble Ticket
elif action == "Add Trouble Ticket":
    with st.form("add_ticket_form"):
        ticket_id = st.number_input("Ticket ID", step=1)
        description = st.text_input("Description")
        root_cause = st.text_input("Root Cause")
        minimal = st.text_input("Minimal Credit")
        partial = st.text_input("Partial Credit")
        full = st.text_input("Full Credit")
        submitted = st.form_submit_button("Add Ticket")

    if submitted:
        ticket = {
            "id": int(ticket_id),
            "description": description,
            "root_cause": root_cause,
            "minimal_credit": minimal,
            "partial_credit": partial,
            "full_credit": full
        }
        append_trouble_ticket(ticket)
        st.success(f"✅ Ticket {ticket_id} added.")

# Action: Remove Trouble Ticket
elif action == "Remove Trouble Ticket":
    ticket_id = st.number_input("Enter Ticket ID to remove", step=1)
    if st.button("Remove Ticket"):
        remove_ticket_by_id(int(ticket_id))
        st.success(f"✅ Ticket {ticket_id} removed.")

# Action: Update Player Total Score
elif action == "Update Player Total Score":
    selected_user = st.selectbox("Select Player Username", player_usernames)
    if selected_user:
        username = selected_user.strip().lower().replace(" ", "_")
        total_key = f"user:{username}:total_score"
        current_total = int(r.get(total_key) or 0)

        st.markdown("### 🎯 Update Total Score")
        new_total = st.number_input("New Total Score", value=current_total, step=1)

        st.markdown("### 📝 Update Individual Ticket Scores")
        all_ticket_ids = set()
        for ticket in json.loads(r.get("trouble_tickets") or "[]"):
            all_ticket_ids.add(str(ticket["id"]))
        for issue in json.loads(r.get("network_issues") or "[]"):
            all_ticket_ids.add(str(issue["id"]))

        ticket_scores = {}
        for ticket_id in sorted(all_ticket_ids, key=int):
            ticket_key = f"user:{username}:ticket:{ticket_id}"
            current_score = int(r.get(ticket_key) or 0)
            new_score = st.number_input(f"Ticket {ticket_id}", value=current_score, step=1, key=f"ticket_{ticket_id}")
            ticket_scores[ticket_key] = new_score

        if st.button("Apply All Updates"):
            r.set(total_key, new_total)
            for key, score in ticket_scores.items():
                r.set(key, score)
            st.success(f"✅ Updated total score and ticket scores for {username}.")

# Action: Add Unstructured Issue
elif action == "Add Unstructured Issue":
    with st.form("add_unstructured_form"):
        issue_id = st.number_input("Issue ID", step=1)
        issue_summary = st.text_input("Issue Summary")
        root_cause = st.text_input("Root Cause")
        scoring = st.text_area("Scoring Instructions")
        submitted = st.form_submit_button("Add Issue")

    if submitted:
        issue = {
            "id": int(issue_id),
            "issue": issue_summary,
            "root_cause": root_cause,
            "scoring": scoring
        }
        add_unstructured_issue(issue)
        st.success(f"✅ Unstructured issue ID {issue_id} added.")

# Action: Remove Unstructured Issue
elif action == "Remove Unstructured Issue":
    issue_id = st.number_input("Enter Issue ID to remove", step=1)
    if st.button("Remove Issue"):
        remove_unstructured_issue(int(issue_id))
        st.success(f"✅ Unstructured issue ID {issue_id} removed.")

# Action: Delete Player
elif action == "Delete Player":
    selected_user = st.selectbox("Select Player to Delete", player_usernames)
    confirm = st.checkbox("Yes, I really want to delete this player")

    if st.button("Delete Player") and confirm:
        try:
            username = selected_user.strip().lower().replace(" ", "_")
            user_key = f"user:{username}"
            total_key = f"user:{username}:total_score"
            ticket_pattern = f"user:{username}:ticket:*"

            if not r.exists(user_key):
                st.error(f"❌ Player '{username}' does not exist.")
            else:
                r.delete(user_key)
                r.delete(total_key)
                for key in r.keys(ticket_pattern):
                    r.delete(key)
                st.success(f"🗑️ Player '{username}' and all associated scores deleted.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

