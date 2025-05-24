# app.py

import streamlit as st
import json
from record_score import record_player_score
from normalize import normalize_sentence
from check_redis_structured_cache_for_entry import check_redis_structured_cache
from sentence_transformer import calculate_cosine_similarity
from structured_llm_grading import llm_grade
from write_to_structured_cache import write_structured_entry_to_cache
from unstructured_llm_grading import evaluate_unstructured_from_root_cause
from get_snarkey_comment import get_random_snark
from auth import create_user, user_exists, validate_user
from redis_client import get_redis_client
from settings import SHOW_DEBUG_UI
from get_random_joke import get_random_joke
from get_random_trivia import get_random_trivia
from settings import SNARKY_MODE_DEFAULT

# ✅ Initialize Redis once via redis_client.py
r = get_redis_client()

# Session state for login
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🌐 Welcome to Guardians of the Network")
    st.markdown("Please login. If this is your first time, enter an email and password to create an account for your Network Trials.")

    with st.form("login_form"):
        username = st.text_input("Email", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")
        submitted = st.form_submit_button("Login or Register")

    if submitted:
        if user_exists(username):
            if validate_user(username, password):
                st.session_state.user = username
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
        else:
            success, message = create_user(username, password)
            if success:
                st.session_state.user = username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.stop()  # Prevent access to rest of app until logged in

# --- Simulate user auth ---
USER_EMAIL = st.session_state.user

# Sidebar
st.sidebar.title("👤 Player")
st.sidebar.markdown(f"**Logged in as:** {USER_EMAIL}")

# Show total score
score_key = f"user:{USER_EMAIL}:total_score"
total_score = r.get(score_key) or 0
st.sidebar.markdown(f"**Total Score:** `{total_score}` points")

# Retrieve all user scores
keys = r.keys("user:*:total_score")
scores = [(key.split(":")[1], int(r.get(key))) for key in keys]
scores.sort(key=lambda x: x[1], reverse=True)

# Calculate rank
player_rank = next((i + 1 for i, (user, score) in enumerate(scores) if user == USER_EMAIL), None)
total_players = len(scores)

# Display rank
if player_rank:
    if player_rank == 1:
        st.sidebar.markdown("## 🥇 **You're in the lead!**")
    else:
        st.sidebar.markdown(f"**Rank:** `{player_rank}` out of `{total_players}` players")
        if player_rank <= 5:
            st.sidebar.success("🎉 You're approaching the lead!")
else:
    st.sidebar.info("Keep going.  You got this!")

# Navigation
page = st.sidebar.radio(
    "🧭 Navigate",
    ["Known Trouble Tickets", "Unguided Troubleshooting", "Networking Trivia", "Networking Jokes", "Your Scores So Far", "Leaderboard", "Instructions"]
)

# Snarky Mode toggle
st.sidebar.markdown("### 🤡 Snarky Mode")
snarky_enabled = st.sidebar.toggle("Enable Snarky Comments?", value=SNARKY_MODE_DEFAULT)

# Main Title
st.title("Guardians of the Network")

# Content Area
st.markdown(f"### 🧾 You selected: {page}")

# Known Trouble Tickets
if page == "Known Trouble Tickets":
    # Retrieve trouble tickets from Redis
    trouble_tickets_json = r.get("trouble_tickets")
    trouble_tickets = json.loads(trouble_tickets_json) if trouble_tickets_json else []

    # Create dropdown options
    ticket_options = []
    for ticket in trouble_tickets:
        ticket_id = str(ticket["id"])
        score_key = f"user:{USER_EMAIL}:ticket:{ticket_id}"
        score = r.get(score_key)

        # Only include tickets where the player has not reached the max score
        if not score or int(score) < 100:
            ticket_options.append(f"{ticket['id']} - {ticket['description']}")

    # Display the dropdown
    if ticket_options:
        selected_ticket = st.selectbox("Select a Trouble Ticket", ticket_options)
    else:
        st.info("🎉 You have already achieved the maximum score for all trouble tickets!")

    st.markdown("### 🧠 Submit Your Diagnosis")

    with st.form(key="diagnosis_form", clear_on_submit=True):
        diagnosis_input = st.text_input("Enter your diagnosis and press Enter")
        submitted = st.form_submit_button("Submit", use_container_width=True)

    if submitted:
        ticket_id = selected_ticket.split(" - ")[0].strip()
        normalized = normalize_sentence(diagnosis_input)
        cache_hit = check_redis_structured_cache(ticket_id, normalized)

        if SHOW_DEBUG_UI:
            st.success(f"Diagnosis submitted for ticket: {selected_ticket}")
            st.markdown(f"📝 **Original Answer:** {diagnosis_input}")
            st.markdown(f"🔍 **Normalized Answer:** {normalized}")

        if cache_hit:
            if SHOW_DEBUG_UI:
                st.markdown("### ✅ Cache Hit:")
                st.json(cache_hit)

            try:
                score = int(cache_hit.get("grade", 0))
                total = record_player_score(USER_EMAIL, ticket_id, score)
                if total is not None:
                    st.success(f"🎯 {score} points recorded. Total score: {total}")
                else:
                    st.info("🛑 You've already earned full credit for this ticket.")
            except Exception as e:
                st.error(f"❌ Failed to record score: {e}")

        else:
            if SHOW_DEBUG_UI:
                st.markdown("### ❌ Cache Miss:")
                st.write("No matching graded entry found in structured Redis cache.")
            st.write("## Handing your diagnosis to our AI grader...")

            ticket = next((t for t in trouble_tickets if str(t["id"]) == ticket_id), None)
            if ticket:
                # Cosine similarity checks
                threshold = 0.4
                matches = []
                for level in ["minimal_credit", "partial_credit", "full_credit"]:
                    expected = ticket.get(level)
                    if expected:
                        similarity = calculate_cosine_similarity(normalized, normalize_sentence(expected))
                        if similarity > threshold:
                            matches.append((level, similarity, expected))

                if matches:
                    if SHOW_DEBUG_UI:
                        st.markdown("### 🔍 Cosine Similarity Matches Above 0.4")
                    st.write("## The AI grader will now consider your diagnosis...")

                    # 🔥 Optional snark
                    if snarky_enabled:
                        snark = get_random_snark()
                        st.markdown(f"🤡 **Snarky Comment:** _{snark}_")

                    for level, sim, text in matches:
                        if SHOW_DEBUG_UI:
                            st.markdown(f"- **{level.replace('_', ' ').title()}** → `{sim:.2f}`\n> _{text}_")

                    # Grade with LLM
                    grade, feedback = llm_grade(normalized, ticket)
                    st.markdown("### 🤖 The AI Grader has considered your diagnosis:")
                    st.markdown(f"- **Grade:** `{grade}`")
                    if SHOW_DEBUG_UI:
                        st.markdown(f"- **Feedback:** {feedback}")

                    try:
                        # Cache graded entry
                        cache_entry = {
                            "ticket_id": int(ticket_id),
                            "input": diagnosis_input,
                            "grade": grade,
                            "feedback": feedback
                        }
                        write_structured_entry_to_cache(cache_entry)

                        # Record player score
                        try:
                            score = int(grade)

                            # 🚫 Penalty for brute-force guessing
                            if score == 0:
                                penalty = -10
                                total = record_player_score(USER_EMAIL, ticket_id, penalty)
                                st.error("🚫 To protect from players brute forcing answers, we deduct 10 points for answers that don't meet the minimum diagnosis requirements.")
                                if total is not None:
                                    st.markdown(f"❌ You lost 10 points. Current score: `{total}`")

                                if snarky_enabled:
                                    snark = get_random_snark()
                                    st.markdown(f"🤡 **Snarky Comment:** _{snark}_")
                            else:
                                total = record_player_score(USER_EMAIL, ticket_id, score)
                                if total is not None:
                                    st.success(f"🎯 {score} points recorded. Total score: {total}")
                                else:
                                    st.info("🛑 You've already earned full credit for this ticket.")
                        except Exception as e:
                            st.error(f"❌ Failed to record score: {e}")

                        if SHOW_DEBUG_UI:
                            st.success("📝 LLM result cached successfully.")
                    except Exception as e:
                        st.error(f"❌ Failed to cache LLM result: {e}")
                else:
                    if SHOW_DEBUG_UI:
                        st.markdown("### 🚫 No meaningful semantic similarity found above 0.4")
                    st.markdown("### 🤖 The AI grader doesn't find this diagnosis close enough to the root cause to grade.")

                    # 🚫 Deduct points for a poor diagnosis
                    penalty_total = record_player_score(USER_EMAIL, ticket_id, -10)
                    st.warning("🚫 To protect from players brute forcing answers, we deduct 10 points for answers that don't meet the minimum diagnosis requirements.")
                    if penalty_total is not None:
                        st.markdown(f"❌ You lost 10 points. Current score: `{penalty_total}`")

                    # 🤡 Show snark if enabled
                    if snarky_enabled:
                        from get_snarkey_comment import get_random_snark
                        snark = get_random_snark()
                        st.markdown(f"🤡 **Snarky Comment:** _{snark}_")

            else:
                st.warning("❗ Ticket details not found.")

# Unguided Troubleshooting
elif page == "Unguided Troubleshooting":
    st.title("🕵️ Unguided Troubleshooting")
    st.markdown("""
    Welcome to the **pure investigation** part of *Guardians of the Network*.

    Your mission: **Find any issue** on the network that nobody else knows about yet.
    Trust your instincts, follow the anomalies — and document your findings below.
    """)

    # Form with a unique key
    with st.form(key="unstructured_form_unique", clear_on_submit=True):
        unstructured_input = st.text_input("🔍 What did you find?")
        unstructured_submitted = st.form_submit_button("Submit", use_container_width=True)

    if unstructured_submitted:
        normalized = normalize_sentence(unstructured_input)

        st.success("## Our AI grader has received your diagnosis for consideration.")
        if SHOW_DEBUG_UI:
            st.markdown(f"📝 **Original:** {unstructured_input}")
            st.markdown(f"🔍 **Normalized:** {normalized}")

        # Step 1: Check Redis cache using fixed "unstructured" ticket_id
        cache_hit = check_redis_structured_cache("unstructured", normalized)

        if cache_hit:
            if SHOW_DEBUG_UI:
                st.markdown("### ✅ Cache Hit:")
                st.json(cache_hit)
            st.markdown("### 🤖 The AI grader has seen this diagnosis before")

            # ✅ Record score from cache
            try:
                score = int(cache_hit.get("grade", 0))
                total = record_player_score(USER_EMAIL, "unstructured", score)
                if total is not None:
                    st.success(f"🎯 {score} points recorded. Total score: {total}")
                else:
                    st.info("🛑 You've already earned full credit for this report.")
                    # 🤡 Show snark if enabled
                    if snarky_enabled:
                        snark = get_random_snark()
                        st.markdown(f"🤡 **Snarky Comment:** _{snark}_")

            except Exception as e:
                st.error(f"❌ Failed to record score: {e}")

        else:
            if SHOW_DEBUG_UI:
                st.markdown("### ❌ Cache Miss:")
                st.write("No matching cached entry found for this unstructured report.")
            st.write("## The AI grader hasn't seen this diagnosis before.  It will consider it now.")

            # ✅ Step 2: Get network issues from array or individual keys
            network_issues_json = r.get("network_issues")
            network_issues = json.loads(network_issues_json) if network_issues_json else []

            # 🔄 If network_issues is empty, fallback to individual issue:* keys
            if not network_issues:
                issue_keys = r.keys("issue:*")
                for key in issue_keys:
                    issue_data = r.get(key)
                    if issue_data:
                        try:
                            issue = json.loads(issue_data)
                            network_issues.append(issue)
                        except Exception:
                            continue  # skip malformed

            matched_cause = None
            highest_score = 0

            for issue in network_issues:
                cause = issue.get("root_cause", "")
                if cause:
                    similarity = calculate_cosine_similarity(normalized, normalize_sentence(cause))
                    if similarity > highest_score:
                        highest_score = similarity
                        matched_cause = cause
                        matched_issue_id = issue.get("id")  # ✅ Save correct issue ID


            # Debug view
            if SHOW_DEBUG_UI:
                st.markdown("### 🧪 Debug View")
                st.markdown(f"**Highest Similarity:** `{highest_score:.2f}`")
                st.markdown(f"**Best-Matched Root Cause:** `{matched_cause}`")

            if highest_score > 0.7:
                grade, feedback = evaluate_unstructured_from_root_cause(matched_cause, normalized)
                if SHOW_DEBUG_UI:
                    st.markdown("### 🧾 Matched Root Cause")
                    st.markdown(f"> _{matched_cause}_")
            else:
                grade = 0
                feedback = "No known root cause matched above similarity threshold."
                matched_issue_id = None

            # Step 4: Cache result and record score
            st.markdown("### 🤖 Auto-Evaluation:")
            st.markdown(f"- **Grade:** `{grade}`")
            if SHOW_DEBUG_UI:
                st.markdown(f"- **Feedback:** {feedback}")

            try:
                cache_entry = {
                    "ticket_id": matched_issue_id if matched_issue_id is not None else "unstructured",
                    "input": unstructured_input,
                    "grade": grade,
                    "feedback": feedback
                }
                write_structured_entry_to_cache(cache_entry)

                try:
                    if matched_issue_id is not None:
                        ticket_key = f"user:{USER_EMAIL}:ticket:{matched_issue_id}"
                        existing_score = int(r.get(ticket_key) or 0)
                        total = record_player_score(USER_EMAIL, matched_issue_id, grade)

                        if total is not None:
                            st.success(f"🎯 {grade} points recorded. Total score: {total}")
                        elif existing_score >= 100:
                            st.info("🛑 You've already earned full credit for this issue.")
                        elif int(grade) <= existing_score:
                            st.info(f"⚠️ Your submitted grade ({grade}) did not improve your current score ({existing_score}). No change made.")
                        else:
                            st.warning("⚠️ Your score could not be recorded due to unknown reasons.")



                    else:
                        if SHOW_DEBUG_UI:
                            st.warning("⚠️ No matched issue ID found — score not recorded.")
                except Exception as e:
                    st.error(f"❌ Failed to record score: {e}")

                if SHOW_DEBUG_UI:
                    st.success("📝 Result cached successfully.")
            except Exception as e:
                st.error(f"❌ Failed to cache result: {e}")


# Your Scores So Far
elif page == "Your Scores So Far":
    st.title("📊 Your Scores So Far")

    # Retrieve trouble tickets and network issues from Redis
    trouble_tickets_json = r.get("trouble_tickets")
    trouble_tickets = json.loads(trouble_tickets_json) if trouble_tickets_json else []

    network_issues_json = r.get("network_issues")
    network_issues = json.loads(network_issues_json) if network_issues_json else []

    st.markdown("### 🧾 Structured Trouble Ticket Scores")

    # Structured ticket scores
    for ticket in trouble_tickets:
        ticket_id = str(ticket["id"])
        issue = ticket["description"]
        key = f"user:{USER_EMAIL}:ticket:{ticket_id}"
        
        score = r.get(key)

        if score:
            score = int(score)
            if score >= 100:
                st.markdown(f"✅ **Ticket {ticket_id}:** {issue} — 🟢 **MAX**")
            else:
                st.markdown(f"🔹 **Ticket {ticket_id}:** {issue} — `{score}` points")
        else:
            st.markdown(f"⚪ **Ticket {ticket_id}:** {issue} — _Not attempted_")

    st.markdown("---")
    st.markdown("### 🧠 Unstructured Network Issue Scores")

    # 🧠 Unstructured issue scores (only show if player has scored)
    for issue in network_issues:
        issue_id = str(issue.get("id"))
        issue_text = issue.get("issue")
    
        key = f"user:{USER_EMAIL}:ticket:{issue_id}"
        score = r.get(key)
    
        if score:
            score = int(score)
            if score >= 100:
                st.markdown(f"✅ **Issue {issue_id}:** {issue_text} — 🟢 **MAX**")
            else:
                st.markdown(f"🔹 **Issue {issue_id}:** {issue_text} — `{score}` points")

elif page == "Instructions":
    st.title("📜 Instructions")
    st.markdown("""
    Welcome to **Guardians of the Network**! Here's how to play:

    ### 🛠 Known Trouble Tickets
    - Select a trouble ticket from the dropdown.
    - Diagnose the issue and submit your answer.
    - Earn points based on the accuracy of your diagnosis.

    ### 🕵️ Unguided Troubleshooting
    - Investigate the network for hidden issues.
    - Submit your findings and earn points for uncovering root causes.

    ### 📚 Networking Trivia
    - Learn fun and interesting facts about networking.

    ### 😂 Networking Jokes
    - Enjoy some lighthearted humor while troubleshooting.

    ### 📊 Your Scores So Far
    - Track your progress and see how many points you've earned.

    ### 🏆 Leaderboard
    - Compete with other players and climb to the top of the leaderboard.

    ---
    Good luck, and may the packets be ever in your favor! 🚀
    """)

elif page == "Networking Trivia":
    st.title("📚 Networking Trivia")

    st.markdown("### Did you know?")
    trivia = get_random_trivia(st.session_state)
    st.markdown(f"- {trivia}")

elif page == "Networking Jokes":
    st.title("😂 Networking Jokes")

    st.markdown("### Here's a joke for you:")
    joke = get_random_joke(st.session_state)
    st.markdown(f"- {joke}")

elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.markdown("### Top Players")

    # Retrieve all user scores
    keys = r.keys("user:*:total_score")
    scores = [(key.split(":")[1], int(r.get(key))) for key in keys]
    scores.sort(key=lambda x: x[1], reverse=True)

    # Display leaderboard
    if scores:
        for i, (user, score) in enumerate(scores):
            st.markdown(f"{i + 1}. **{user}** - `{score}` points")
    else:
        st.info("No scores available yet.")
