import yfinance as yf
import pandas as pd
from colorama import Fore, Style
from tickers_mm_acciones import tickers_seleccionados  # Importa los tickers


# Función para obtener los precios históricos agrupados por semana
def obtener_precios_semanales(ticker, start_date, end_date):
    # Obtener los precios con el intervalo '1wk' (semanal)
    data = yf.download(ticker, start=start_date, end=end_date, interval='1wk', auto_adjust=False)
    return data['Close']


# Función para calcular el MACD y la línea de señal
def calcular_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data.ewm(span=short_window, adjust=False).mean()
    long_ema = data.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal_line


# Función para detectar cruces semanales del MACD
def detectar_cruce_semanal(macd, signal_line):
    cruces = {
        'alcista_actual': False,
        'bajista_actual': False,
        'alcista_anterior': False,
        'bajista_anterior': False
    }
    if len(macd) < 3:  # Necesitamos al menos 3 semanas de datos
        return cruces

    # Verificar cruces de la semana actual
    cruces['alcista_actual'] = (macd.iloc[-2] < signal_line.iloc[-2]).item() and (macd.iloc[-1] > signal_line.iloc[-1]).item()
    cruces['bajista_actual'] = (macd.iloc[-2] > signal_line.iloc[-2]).item() and (macd.iloc[-1] < signal_line.iloc[-1]).item()

    # Verificar cruces de la semana anterior
    cruces['alcista_anterior'] = (macd.iloc[-3] < signal_line.iloc[-3]).item() and (macd.iloc[-2] > signal_line.iloc[-2]).item()
    cruces['bajista_anterior'] = (macd.iloc[-3] > signal_line.iloc[-3]).item() and (macd.iloc[-2] < signal_line.iloc[-2]).item()

    return cruces


# Función principal para analizar múltiples acciones
def analizar_macd_semanal():
    cruces_alcistas_actual = []
    cruces_bajistas_actual = []
    cruces_alcistas_anterior = []
    cruces_bajistas_anterior = []
    sin_procesar = []

    for ticker in tickers_seleccionados:
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=2)  # Últimos 2 años para obtener suficiente historial semanal

        try:
            # Obtener precios semanales
            prices = obtener_precios_semanales(ticker, start_date, end_date)

            # Calcular el MACD y la línea de señal
            macd, signal_line = calcular_macd(prices)

            # Detectar cruces semanales
            cruces = detectar_cruce_semanal(macd, signal_line)

            print(f"\nAnálisis para: {ticker}")
            print(f"MACD más reciente: {macd.iloc[-1].item():.2f}")
            print(f"Línea de señal más reciente: {signal_line.iloc[-1].item():.2f}")
            print(f"MACD anterior: {macd.iloc[-2].item():.2f}")
            print(f"Línea de señal anterior: {signal_line.iloc[-2].item():.2f}")

            # Registrar los cruces detectados
            if cruces['alcista_actual']:
                print("\033[92mCruce alcista en la semana actual.\033[0m")
                cruces_alcistas_actual.append(ticker)
            if cruces['bajista_actual']:
                print("\033[91mCruce bajista en la semana actual.\033[0m")
                cruces_bajistas_actual.append(ticker)
            if cruces['alcista_anterior']:
                print("\033[94mCruce alcista en la semana anterior.\033[0m")
                cruces_alcistas_anterior.append(ticker)
            if cruces['bajista_anterior']:
                print("\033[93mCruce bajista en la semana anterior.\033[0m")
                cruces_bajistas_anterior.append(ticker)

        except Exception as e:
            sin_procesar.append(ticker)
            print(f"\033[91mError procesando {ticker}: {e}\033[0m")

    # Resultados finales
    print("\nResumen de señales detectadas:\n")

    # Cruces alcistas
    print(
        f"{Fore.GREEN}Cruces alcistas de la semana actual:{Style.RESET_ALL} "
        f"{', '.join(cruces_alcistas_actual) if cruces_alcistas_actual else 'Ninguno'}")
    print(
        f"{Fore.GREEN}Cruces alcistas de la semana anterior:{Style.RESET_ALL} "
        f"{', '.join(cruces_alcistas_anterior) if cruces_alcistas_anterior else 'Ninguno'}\n")

    # Cruces bajistas
    print(
        f"{Fore.RED}Cruces bajistas de la semana actual:{Style.RESET_ALL} "
        f"{', '.join(cruces_bajistas_actual) if cruces_bajistas_actual else 'Ninguno'}")
    print(
        f"{Fore.RED}Cruces bajistas de la semana anterior:{Style.RESET_ALL} "
        f"{', '.join(cruces_bajistas_anterior) if cruces_bajistas_anterior else 'Ninguno'}\n")

    # Tickers sin procesar
    print(f"Tickers sin procesar: {', '.join(sin_procesar) if sin_procesar else 'Ninguno'}")


# Ejecutar el análisis
analizar_macd_semanal()
