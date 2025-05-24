import json
from redis_client import get_redis_client

r = get_redis_client()

def check_user(username, use_streamlit=False):
    username = username.strip().lower().replace(" ", "_")
    user_key = f"user:{username}"
    total_key = f"user:{username}:total_score"

    if not r.exists(user_key):
        msg = f"❌ User '{username}' does not exist."
        if use_streamlit:
            import streamlit as st
            st.error(msg)
        else:
            print(msg)
        return

    if use_streamlit:
        import streamlit as st
        st.markdown(f"### 👤 User: `{username}`")
        st.markdown("#### 📦 Account Info:")
        for key, value in r.hgetall(user_key).items():
            st.markdown(f"- `{key}`: {value}")

        total_score = r.get(total_key) or "0"
        st.markdown(f"#### 🎯 Total Score: `{total_score}`")

        st.markdown("#### 📝 Ticket Scores:")
        keys = r.keys(f"user:{username}:ticket:*")
        if not keys:
            st.markdown("- No tickets found.")
        else:
            for key in keys:
                ticket_id = key.split(":")[-1]
                score = r.get(key)
                st.markdown(f"- Ticket `{ticket_id}`: `{score}` points")
    else:
        print(f"\n👤 User: {username}")
        print("📦 Account Info:")
        for key, value in r.hgetall(user_key).items():
            print(f"  {key}: {value}")
        print(f"\n🎯 Total Score: {r.get(total_key) or '0'}")
        print("\n📝 Ticket Scores:")
        keys = r.keys(f"user:{username}:ticket:*")
        if not keys:
            print("  No tickets found.")
        else:
            for key in keys:
                ticket_id = key.split(":")[-1]
                score = r.get(key)
                print(f"  Ticket {ticket_id}: {score} points")

if __name__ == "__main__":
    username = input("🔍 Enter username to check: ").strip()
    if username:
        check_user(username)
    else:
        print("❌ Username cannot be blank.")

