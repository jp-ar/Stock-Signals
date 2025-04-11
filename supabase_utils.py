from supabase import create_client, Client
import streamlit as st

# Usar secrets de Streamlit en la nube
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_tickers_usuario(usuario_id: str):
    response = supabase.table("tickers").select("ticker").eq("usuario_id", usuario_id).execute()
    data = response.data
    return [item['ticker'] for item in data] if data else []
