import streamlit as st
from supabase_client import supabase

def login():
    st.sidebar.header("🔐 Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    login_button = st.sidebar.button("Login")

    if login_button:
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                user = res.user
                st.session_state["user"] = user

                # Verificamos si ya existe en la tabla 'users'
                existing = supabase.table("users").select("id").eq("id", user.id).execute()

                if not existing.data:
                    supabase.table("users").insert({
                        "id": user.id,
                        "username": email,
                        "password": password  # opcional
                    }).execute()

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
        try:
            # Solo creamos la cuenta con Supabase Auth
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            st.success("✅ Cuenta creada. Revisa tu correo para confirmar tu email antes de iniciar sesión.")

        except Exception as e:
            st.error(f"❌ Signup failed: {e}")


def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.success("Logged out")
        st.rerun()
