import streamlit as st
from supabase_client import supabase  # Asegúrate de tener esto bien configurado


def login():
    st.sidebar.header("🔐 Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    login_button = st.sidebar.button("Login")

    if login_button:
        if not email or not password:
            st.error("Please fill in both fields.")
            return

        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                st.session_state["user"] = res.user
                st.success("✅ Logged in successfully")
                st.rerun()
            else:
                st.error("❌ Login failed. Please check your credentials.")

        except Exception as e:
            st.error(f"❌ Login failed: {e}")


def signup():
    st.sidebar.header("🆕 Sign Up")

    email = st.sidebar.text_input("New Email")
    password = st.sidebar.text_input("New Password", type="password")

    if st.sidebar.button("Create Account"):
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": "https://stock-signals.streamlit.app/confirm-account"
                }
            })

            user = res.user

            if user:
                # Insertar solo el id y username (email) — no la contraseña
                insert_res = supabase.table("users").insert({
                    "id": user.id,        # Este debe coincidir con auth.uid() para la política RLS
                    "username": email
                }).execute()

                st.success("✅ Account created. Please check your email to confirm it.")

        except Exception as e:
            st.error(f"❌ Signup failed: {e}")


def confirm_account():
    st.title("✅ Account Confirmed!")
    st.write("Thank you for confirming your account. You can now log in with your email and password.")

    if st.button("Go to Login"):
        st.session_state.pop("user", None)
        st.success("Session cleared. You can now log in.")
        st.rerun()


def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.success("✅ Logged out")
        st.rerun()
