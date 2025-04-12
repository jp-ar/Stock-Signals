import streamlit as st
from supabase_client import supabase  # Asegúrate de que este cliente esté correctamente configurado


def login():
    st.sidebar.header("🔐 Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    login_button = st.sidebar.button("Login")

    if login_button:
        if not email or not password:
            st.error("❌ Please fill in both fields.")
            return

        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                # Guardar en sesión
                st.session_state["user"] = res.user
                st.success("✅ Logged in successfully")

                # Verificar si el usuario ya existe en la tabla `users`
                existing = supabase.table("users").select("id").eq("id", res.user.id).execute()

                if not existing.data:
                    # Insertar usuario en la tabla si no existe aún
                    supabase.table("users").insert({
                        "id": res.user.id,
                        "username": email
                    }).execute()
                    st.info("👤 User inserted into 'users' table.")

                st.rerun()

            else:
                st.error("❌ Login failed. Please check your credentials.")

        except Exception as e:
            st.error("❌ Login failed. Please try again.")
            st.exception(e)  # Puedes quitar esto en producción

def signup():
    st.sidebar.header("🆕 Sign Up")

    email = st.sidebar.text_input("New Email")
    password = st.sidebar.text_input("New Password", type="password")

    if st.sidebar.button("Create Account"):
        if not email or not password:
            st.error("❌ Please enter both email and password.")
            return

        if '@' not in email or len(password) < 6:
            st.error("❌ Please enter a valid email and a password with at least 6 characters.")
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
                st.write("User ID:", user.id)
                st.success("✅ Account created. Please check your email to confirm it.")
            else:
                st.info("✅ Signup successful. Please check your email to confirm your account before logging in.")

        except Exception as e:
            st.error("❌ Signup failed. Please try again.")
            st.exception(e)


def confirm_account():
    st.title("✅ Account Confirmed!")
    st.write("Thank you for confirming your account. You can now log in with your email and password.")

    if st.button("Go to Login"):
        st.session_state.pop("user", None)
        st.success("🔓 Session cleared. You can now log in.")
        st.rerun()


def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.success("✅ Logged out")
        st.rerun()
