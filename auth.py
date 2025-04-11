import streamlit as st
from supabase_client import supabase

def login():
    st.sidebar.header("🔐 Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            st.session_state["user"] = res.user
            st.success("Logged in successfully")
            st.experimental_rerun()
        except Exception as e:
            st.error("Login failed")

def signup():
    st.sidebar.header("🆕 Sign Up")

    email = st.sidebar.text_input("New Email")
    password = st.sidebar.text_input("New Password", type="password")

    if st.sidebar.button("Create Account"):
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            st.success("Account created! Please check your email.")
        except Exception as e:
            st.error("Signup failed")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.success("Logged out")
        st.experimental_rerun()
