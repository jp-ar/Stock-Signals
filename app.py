import streamlit as st

st.title("Stock Signals 📊")

tickers_input = st.text_input("Ingresá tus tickers separados por comas", "AAPL, MSFT, TSLA")

if st.button("Analizar"):
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
    st.write(f"Procesando {len(tickers)} tickers: {', '.join(tickers)}")
    # Acá iría tu función principal que analiza los tickers
