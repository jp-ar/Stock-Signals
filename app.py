import streamlit as st
import yfinance as yf
import requests
from db import get_tickers, add_ticker, remove_ticker
from auth import login, signup, logout
from supabase_client import supabase
from scripts.macd_1mo import analizar_macd_mensual

st.set_page_config(page_title="Stock Signals", layout="centered")

# Función para sugerencias de tickers desde Yahoo Finance
def buscar_tickers_similares(entrada):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={entrada}"
    try:
        response = requests.get(url)
        resultados = response.json()
        sugerencias = [r["symbol"] for r in resultados.get("quotes", []) if "symbol" in r]
        return sugerencias
    except:
        return []

# Autenticación
if "user" not in st.session_state:
    login()
    signup()
    st.stop()

user = st.session_state["user"]
user_id = user.id
st.sidebar.markdown(f"👤 **{user.email}**")
logout()

st.title("📊 Stock Signals")

# Mostrar tickers guardados
st.header("📈 Your Tickers")
tickers = get_tickers(user_id)

if tickers:
    for ticker in tickers:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {ticker}")
        with col2:
            if st.button("❌", key=f"rm_{ticker}"):
                remove_ticker(user_id, ticker)
                st.experimental_rerun()
else:
    st.info("No tickers added yet.")

# Agregar nuevo ticker
st.subheader("➕ Add a ticker")
new_ticker = st.text_input("Example: AAPL").strip().upper()

if st.button("Add Ticker"):
    if new_ticker:
        try:
            data = yf.Ticker(new_ticker).info
            if data:  # Si info no está vacío
                add_ticker(user_id, new_ticker)
                st.success(f"{new_ticker} added.")
                st.experimental_rerun()
            else:
                raise ValueError("Empty info")
        except:
            st.error("❌ Invalid ticker.")
            sugerencias = buscar_tickers_similares(new_ticker)
            if sugerencias:
                st.info("🔍 Did you mean one of these?")
                for s in sugerencias[:5]:
                    st.markdown(f"- **{s}**")
            else:
                st.info("No similar tickers found.")

st.divider()

# Ejecutar análisis
st.subheader("⚙️ Choose analysis")
option = st.selectbox("Select script:", [
    "Signals 1H + 4H + 1D",
    "Signals 1D + 1WK + 1MO",
    "MACD 1WK",
    "MACD 1MO"
])

if st.button("Run analysis"):
    if not tickers:
        st.warning("You must add at least one ticker.")
    else:
        st.info("🔍 Running analysis...")
        st.write("Tickers:", tickers)

        if option == "MACD 1MO":
            resultados = analizar_macd_mensual(tickers)

            if resultados["alcistas_actual"]:
                st.success("📈 Cruce alcista actual:")
                for ticker in resultados["alcistas_actual"]:
                    st.markdown(f"- **{ticker}**")

            if resultados["bajistas_actual"]:
                st.error("📉 Cruce bajista actual:")
                for ticker in resultados["bajistas_actual"]:
                    st.markdown(f"- **{ticker}**")

            if resultados["alcistas_anterior"]:
                st.info("ℹ️ Cruce alcista anterior:")
                for ticker in resultados["alcistas_anterior"]:
                    st.markdown(f"- **{ticker}**")

            if resultados["bajistas_anterior"]:
                st.warning("⚠️ Cruce bajista anterior:")
                for ticker in resultados["bajistas_anterior"]:
                    st.markdown(f"- **{ticker}**")

            if resultados["sin_procesar"]:
                st.markdown("❓ Tickers sin procesar:")
                for ticker in resultados["sin_procesar"]:
                    st.markdown(f"- {ticker}")

coffee_link = st.secrets["BUYMEACOFFEE_LINK"]

st.markdown("---")
st.markdown("## ☕ Support this project")
st.markdown(
    f"""
    <a href="{coffee_link}" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=jp_ar&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" />
    </a>
    """,
    unsafe_allow_html=True
)