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
                st.session_state["user"] = res.user
                st.success("Logged in successfully")
                st.rerun()  # Recarga la página después del login exitoso
            else:
                st.error("Login failed. Please check your credentials.")

        except Exception as e:
            st.error(f"Login failed: {e}")


def signup():
    st.sidebar.header("🆕 Sign Up")

    email = st.sidebar.text_input("New Email")
    password = st.sidebar.text_input("New Password", type="password")

    if st.sidebar.button("Create Account"):
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    # Asegúrate de que esta URL esté registrada en la configuración de Supabase
                    "email_redirect_to": "https://stock-signals.streamlit.app/confirm-account"
                }
            })

            user = res.user

            # Insertamos el usuario en la tabla "users" después de crear la cuenta
            if user:
                supabase.table("users").insert({
                    "id": user.id,
                    "username": email,
                    "password": password  # No es necesario si solo usas Supabase Auth
                }).execute()

            st.success("✅ Account created. Please check your email for confirmation.")
        except Exception as e:
            st.error(f"❌ Signup failed: {e}")


def confirm_account():
    # Esta página se muestra después de que el usuario hace clic en el enlace de confirmación
    st.title("Account Confirmed!")
    st.write("Thank you for confirming your account. You can now log in with your email and password.")

    # Agregar un botón para ir a la página de login
    if st.button("Go to Login"):
        st.session_state.pop("user", None)  # Limpiar cualquier sesión de usuario actual
        st.success("Logged out. Now you can login.")
        st.rerun()


def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.success("Logged out")
        st.rerun()  # También puedes usar st.rerun() aquí para recargar la página
