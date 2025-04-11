from supabase import create_client
import os

# Si estás corriendo en Streamlit Cloud, usá st.secrets
try:
    import streamlit as st
    SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets["SUPABASE_URL"])
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets["SUPABASE_KEY"])
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
