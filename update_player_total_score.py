from redis_client import get_redis_client

def update_total_score(username, new_score, use_streamlit=False):
    username = username.strip().lower().replace(" ", "_")
    total_key = f"user:{username}:total_score"

    try:
        new_score = int(new_score)
        r = get_redis_client()

        if not r.exists(f"user:{username}"):
            msg = f"❌ User '{username}' does not exist."
            if use_streamlit:
                import streamlit as st
                st.error(msg)
            else:
                print(msg)
            return

        r.set(total_key, new_score)
        msg = f"✅ Updated total score for {username} to {new_score}"
        if use_streamlit:
            import streamlit as st
            st.success(msg)
        else:
            print(msg)
    except ValueError:
        err = "❌ Score must be an integer."
        if use_streamlit:
            import streamlit as st
            st.error(err)
        else:
            print(err)
    except Exception as e:
        err = f"❌ Error updating score: {e}"
        if use_streamlit:
            import streamlit as st
            st.error(err)
        else:
            print(err)

if __name__ == "__main__":
    print("🛠️  Manually update a player's total score\n")
    username = input("🔍 Enter username: ").strip()
    new_score = input("🎯 Enter new total score: ").strip()
    if username and new_score:
        update_total_score(username, new_score)
    else:
        print("❌ Both fields are required.")

