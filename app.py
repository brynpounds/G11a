# app.py

import streamlit as st
import redis
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
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_DECODE_RESPONSES
from redis.sentinel import Sentinel
from settings import REDIS_USE_SENTINEL, REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_SERVICE_NAME, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_DECODE_RESPONSES

if REDIS_USE_SENTINEL:
    sentinel_hosts = [tuple(host.split(":")) for host in REDIS_SENTINEL_HOSTS]
    sentinel = Sentinel(sentinel_hosts, decode_responses=REDIS_DECODE_RESPONSES)
    r = sentinel.master_for(REDIS_SENTINEL_SERVICE_NAME, db=REDIS_DB)
else:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)


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
# --- Actual user session from login ---
USER_EMAIL = st.session_state.user

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        header {
            visibility: hidden;
        }
        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.title("👤 Player")
user_email = USER_EMAIL  # Hardcoded for now
st.sidebar.markdown(f"**Logged in as:** {user_email}")

# Show total score
score_key = f"user:{user_email}:total_score"
total_score = r.get(score_key) or 0
st.sidebar.markdown(f"**Total Score:** `{total_score}` points")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)

# Get total score for the current user
score_key = f"user:{USER_EMAIL}:total_score"
total_score = int(r.get(score_key) or 0)

# Build full leaderboard
all_keys = r.keys("user:*:total_score")
leaderboard = []
for key in all_keys:
    username = key.split(":")[1]
    score = int(r.get(key) or 0)
    leaderboard.append((username, score))

# Sort leaderboard descending by score
leaderboard.sort(key=lambda x: x[1], reverse=True)

# Get rank of current user
rank = next((i + 1 for i, (u, _) in enumerate(leaderboard) if u == USER_EMAIL), None)
total_players = len(leaderboard)

#st.sidebar.title("👤 User")
#st.sidebar.markdown(f"**Logged in as:** `{USER_EMAIL}`")
#st.sidebar.markdown(f"**Total Score:** `{total_score}` points")

# Add rank position
if rank:
    place_suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank if rank < 20 else rank % 10, "th")
    st.sidebar.markdown(f"**🏅 Rank:** `{rank}{place_suffix} out of {total_players} Guardians`")
else:
    st.sidebar.markdown("**🏅 Rank:** Not ranked")

# Snarky Mode Toggle
snarky_mode = st.sidebar.checkbox("😈 Enable Snarky Mode", value=False)

# Navigation
page = st.sidebar.radio(
    "🧭 Navigate",
    ["Structured Trouble Tickets", "Unstructured Troubleshooting", "Networking Trivia", "Networking Jokes", "Your Scores So Far", "Leaderboard", "Instructions"]
)

# Main Title
st.title("Guardians of the Network (bryn version)")

# Content Area
st.markdown(f"### 🧾 You selected: {page}")

# Placeholder content
if page == "Structured Trouble Tickets":
    import json

    # Load structured ticket data
    with open("game_data.json", "r") as f:
        ticket_data = json.load(f)["trouble_tickets"]

    # Create dropdown options
    ticket_options = []
    for ticket in ticket_data:
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

        st.success(f"Diagnosis submitted for ticket: {selected_ticket}")
        st.markdown(f"📝 **Original Answer:** {diagnosis_input}")
        st.markdown(f"🔍 **Normalized Answer:** {normalized}")

        if cache_hit:
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
            st.markdown("### ❌ Cache Miss:")
            st.write("No matching graded entry found in structured Redis cache.")

            ticket = next((t for t in ticket_data if str(t["id"]) == ticket_id), None)
            if ticket:
                # Cosine similarity checks
                threshold = 0.5
                matches = []
                for level in ["minimal_credit", "partial_credit", "full_credit"]:
                    expected = ticket.get(level)
                    if expected:
                        similarity = calculate_cosine_similarity(normalized, normalize_sentence(expected))
                        if similarity > threshold:
                            matches.append((level, similarity, expected))

                if matches:
                    st.markdown("### 🔍 Cosine Similarity Matches Above 0.5")
                    for level, sim, text in matches:
                        st.markdown(f"- **{level.replace('_', ' ').title()}** → `{sim:.2f}`\n> _{text}_")

                    # Grade with LLM
                    grade, feedback = llm_grade(normalized, ticket)
                    print(f"[DEBUG] Raw: {diagnosis_input}")
                    print(f"[DEBUG] Normalized: {normalized}")
                    

                    st.markdown("### 🤖 LLM Evaluation:")
                    st.markdown(f"- **Grade:** `{grade}`")
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
                            total = record_player_score(USER_EMAIL, ticket_id, score)
                            if total is not None:
                                st.success(f"🎯 {score} points recorded. Total score: {total}")
                            else:
                                st.info("🛑 You've already earned full credit for this ticket.")
                        except Exception as e:
                            st.error(f"❌ Failed to record score: {e}")

                        st.success("📝 LLM result cached successfully.")
                    except Exception as e:
                        st.error(f"❌ Failed to cache LLM result: {e}")
                else:
                    st.markdown("### 🚫 No meaningful semantic similarity found above 0.5")
            else:
                st.warning("❗ Ticket details not found.")

        # Snarky mode comment
        if snarky_mode:
            st.divider()
            st.markdown("😈 **Snarky Mode Activated**")
            snark = get_random_snark()
            st.markdown(f"> _{snark}_")





elif page == "Unstructured Troubleshooting":
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

        st.success("Your investigation report has been received.")
        st.markdown(f"📝 **Original:** {unstructured_input}")
        st.markdown(f"🔍 **Normalized:** {normalized}")

        # Step 1: Check Redis cache using fixed "unstructured" ticket_id
        cache_hit = check_redis_structured_cache("unstructured", normalized)

        if cache_hit:
            st.markdown("### ✅ Cache Hit:")
            st.json(cache_hit)

            # ✅ Record score from cache
            try:
                score = int(cache_hit.get("grade", 0))
                total = record_player_score(USER_EMAIL, "unstructured", score)
                if total is not None:
                    st.success(f"🎯 {score} points recorded. Total score: {total}")
                else:
                    st.info("🛑 You've already earned full credit for this report.")
            except Exception as e:
                st.error(f"❌ Failed to record score: {e}")

        else:
            st.markdown("### ❌ Cache Miss:")
            st.write("No matching cached entry found for this unstructured report.")

            # Step 2: Load known root causes from Redis
            import redis
            import json
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)
            game_data = json.loads(r.get("game_data") or "{}")
            network_issues = game_data.get("network_issues", [])

            # Step 3: Compare player input to all root causes
            matched_cause = None
            highest_score = 0

            for issue in network_issues:
                cause = issue.get("root_cause", "")
                if cause:
                    similarity = calculate_cosine_similarity(normalized, normalize_sentence(cause))
                    if similarity > highest_score:
                        highest_score = similarity
                        matched_cause = cause
                        matched_issue_id = issue.get("id")  # ✅ Save the correct issue ID

            # Debug view
            st.markdown("### 🧪 Debug View")
            st.markdown(f"**Highest Similarity:** `{highest_score:.2f}`")
            st.markdown(f"**Best-Matched Root Cause:** `{matched_cause}`")

            if highest_score > 0.7:
                grade, feedback = evaluate_unstructured_from_root_cause(matched_cause, normalized)
                st.markdown("### 🧾 Matched Root Cause")
                st.markdown(f"> _{matched_cause}_")
                print(f"[DEBUG] matched_issue_id: {matched_issue_id} → grade: {grade}")
                print(f"[REDIS WRITE] user:{USER_EMAIL}:ticket:{matched_issue_id} → {grade}")
            else:
                grade = 0
                feedback = "No known root cause matched above similarity threshold."
                matched_issue_id = None  # explicitly null it out


            # Step 4: Cache result and record score
            st.markdown("### 🤖 Auto-Evaluation:")
            st.markdown(f"- **Grade:** `{grade}`")
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
                        total = record_player_score(USER_EMAIL, matched_issue_id, grade)
                        if total is not None:
                            st.success(f"🎯 {grade} points recorded. Total score: {total}")
                        else:
                            st.info("🛑 You've already earned full credit for this issue.")
                    else:
                        st.warning("⚠️ No matched issue ID found — score not recorded.")
                except Exception as e:
                    st.error(f"❌ Failed to record score: {e}")

                st.success("📝 Result cached successfully.")
            except Exception as e:
                st.error(f"❌ Failed to cache result: {e}")

        # Snarky comment (if enabled)
        if snarky_mode:
            st.divider()
            st.markdown("😈 **Snarky Mode Activated**")
            snark = get_random_snark()
            st.markdown(f"> _{snark}_")
    

elif page == "Unstructured Troubleshooting":
    st.write("This is the Unstructured Troubleshooting section.")
elif page == "Networking Trivia":
    from get_random_trivia import get_random_trivia

    st.title("📡 Networking Trivia")
    st.markdown("Boost your network IQ with a random fact from the vault!")

    if st.button("🎲 Give Me a Random Trivia Fact"):
        fact = get_random_trivia()
        st.markdown(f"🧠 **Trivia:** {fact}")

elif page == "Networking Jokes":
    from get_random_joke import get_random_joke

    st.title("🤣 Networking Jokes")
    st.markdown("Because even packet drops deserve a punchline.")

    if st.button("🎲 Tell Me a Joke"):
        joke = get_random_joke()
        st.markdown(f"😂 **Joke:** {joke}")
        
elif page == "Your Scores So Far":
    st.title("📊 Your Scores So Far")

    # Redis setup
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)

    # Load game data from Redis
    game_data = json.loads(r.get("game_data") or "{}")
    structured = game_data.get("trouble_tickets", [])
    unstructured_issues = game_data.get("network_issues", [])

    st.markdown("### 🧾 Structured Trouble Ticket Scores")

    # Structured ticket scores
    for ticket in structured:
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
    for issue in unstructured_issues:
        issue_id = str(issue.get("id"))
        issue_text = issue.get("issue")
    
        key = f"user:{USER_EMAIL}:ticket:{issue_id}"
        score = r.get(key)
        print(f"[DEBUG] Checking key: {key} → {score}")
    
        if score:
            score = int(score)
            if score >= 100:
                st.markdown(f"✅ **Issue {issue_id}:** {issue_text} — 🟢 **MAX**")
            else:
                st.markdown(f"🔹 **Issue {issue_id}:** {issue_text} — `{score}` points")



elif page == "Leaderboard":
    st.title("🏆 Leaderboard")

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=REDIS_DECODE_RESPONSES)

    # Fetch all user keys
    all_keys = r.keys("user:*:total_score")

    leaderboard = []
    for key in all_keys:
        username = key.split(":")[1]
        score = int(r.get(key) or 0)
        leaderboard.append((username, score))

    # Sort descending and take top 10
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    top_10 = leaderboard[:10]

    if not top_10:
        st.info("No players have scored yet. Be the first Guardian!")
    else:
        st.markdown("### 🥇 Top 10 Guardians of the Network")

        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        for i, (username, score) in enumerate(top_10):
            medal = medals[i] if i < len(medals) else "🏅"
            st.markdown(f"{medal} **{username}** — `{score}` points")




elif page == "Instructions":
    st.write("Here’s how to play the Guardians of the Network game...")

# Show if snarky mode is enabled
if snarky_mode:
    st.markdown("💬 *Snarky Mode is ON. Expect sass.*")

