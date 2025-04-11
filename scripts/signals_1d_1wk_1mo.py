import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
import sys
from tickers_mm_acciones import tickers_seleccionados  # Asegúrate de que este módulo contiene la lista de tickers


# Función para actualizar la barra de progreso
def actualizar_progreso(procesados, total):
    porcentaje = (procesados / total) * 100
    barra_longitud = 50  # Longitud de la barra de progreso
    llenado = int(barra_longitud * procesados // total)
    barra = '#' * llenado + '-' * (barra_longitud - llenado)
    sys.stdout.write(f'\rProgreso: |{barra}| {porcentaje:.2f}% Completado')
    sys.stdout.flush()


# Funciones Utilitarias Compartidas
def obtener_precios(ticker, start_date, end_date, interval='1d'):
    try:
        # Convertimos las fechas a UTC
        start_date = pd.to_datetime(start_date).tz_localize('UTC')
        end_date = pd.to_datetime(end_date).tz_localize('UTC')

        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,
            progress=False
        )
        return data
    except Exception as e:
        print(f"\033[91mError al descargar datos para {ticker}: {e}\033[0m")
        return None


def calcular_emas(prices):
    try:
        if len(prices) < 100:  # Verificar que haya suficientes datos
            print("\033[91mNo hay suficientes datos para calcular EMAs.\033[0m")
            return None, None

        ema50 = prices['Close'].ewm(span=50, adjust=False).mean()
        ema200 = prices['Close'].ewm(span=200, adjust=False).mean()
        return ema50, ema200
    except Exception as e:
        print(f"\033[91mError al calcular EMAs: {e}\033[0m")
        return None, None


def detectar_cruce_ema(ema50, ema200):
    if ema50 is None or ema200 is None or len(ema50) < 3 or len(ema200) < 3:
        return None  # No hay suficientes datos para detectar cruce

    cruce_alcista = int(
        (ema50.iloc[-3].item() < ema200.iloc[-3].item()) and (ema50.iloc[-2].item() >= ema200.iloc[-2].item())
    ) + int(
        (ema50.iloc[-2].item() < ema200.iloc[-2].item()) and (ema50.iloc[-1].item() >= ema200.iloc[-1].item())
    )

    cruce_bajista = int(
        (ema50.iloc[-3].item() > ema200.iloc[-3].item()) and (ema50.iloc[-2].item() <= ema200.iloc[-2].item())
    ) + int(
        (ema50.iloc[-2].item() > ema200.iloc[-2].item()) and (ema50.iloc[-1].item() <= ema200.iloc[-1].item())
    )

    if cruce_alcista > 0:
        return "alcista"
    elif cruce_bajista > 0:
        return "bajista"
    else:
        return None


def calcular_emas_1wk_1mo(prices, periodo, ticker=None):
    try:
        if len(prices) < 50:  # Verificar que haya suficientes datos para la EMA50
            print(f"\n\033[93m[AVISO] No hay suficientes datos para calcular EMAs en {periodo} para {ticker}.\033[0m")
            return None, None

        ema20 = prices['Close'].ewm(span=20, adjust=False).mean()
        ema50 = prices['Close'].ewm(span=50, adjust=False).mean()
        return ema20, ema50
    except Exception as e:
        print(f"\n\033[91m[ERROR] No se pudo calcular EMAs en {periodo} para {ticker}: {e}\033[0m")
        return None, None


def detectar_cruce_ema_20_50(ema20, ema50):
    if ema20 is None or ema50 is None or len(ema20) < 3 or len(ema50) < 3:
        return None  # No hay suficientes datos

    cruce_alcista = int(
        (ema20.iloc[-3].item() < ema50.iloc[-3].item()) and (ema20.iloc[-2].item() >= ema50.iloc[-2].item())
    ) + int(
        (ema20.iloc[-2].item() < ema50.iloc[-2].item()) and (ema20.iloc[-1].item() >= ema50.iloc[-1].item())
    )

    cruce_bajista = int(
        (ema20.iloc[-3].item() > ema50.iloc[-3].item()) and (ema20.iloc[-2].item() <= ema50.iloc[-2].item())
    ) + int(
        (ema20.iloc[-2].item() > ema50.iloc[-2].item()) and (ema20.iloc[-1].item() <= ema50.iloc[-1].item())
    )

    if cruce_alcista > 0:
        return "alcista"
    elif cruce_bajista > 0:
        return "bajista"
    else:
        return None


def calcular_macd(prices):
    try:
        macd = prices['Close'].ewm(span=12, adjust=False).mean() - prices['Close'].ewm(span=26, adjust=False).mean()
        signal_line = macd.ewm(span=9, adjust=False).mean()
        return macd, signal_line
    except Exception as e:
        print(f"\033[91mError al calcular MACD: {e}\033[0m")
        return None, None


def detectar_cruce_macd(macd, signal_line):
    if macd is None or signal_line is None or len(macd) < 2 or len(signal_line) < 2:
        return None  # No hay suficientes datos para detectar cruce

    cruce_alcista = int(
        (macd.iloc[-2].item() < signal_line.iloc[-2].item()) and (macd.iloc[-1].item() > signal_line.iloc[-1].item())
    ) + int(
        (macd.iloc[-3].item() < signal_line.iloc[-3].item()) and (macd.iloc[-2].item() > signal_line.iloc[-2].item())
    )
    cruce_bajista = int(
        (macd.iloc[-2].item() > signal_line.iloc[-2].item()) and (macd.iloc[-1].item() < signal_line.iloc[-1].item())
    ) + int(
        (macd.iloc[-3].item() > signal_line.iloc[-3].item()) and (macd.iloc[-2].item() < signal_line.iloc[-2].item())
    )

    if cruce_alcista:
        return "alcista"
    elif cruce_bajista:
        return "bajista"
    else:
        return None


def confirmar_volumen(prices, factor=1.5, window=20):
    """
    Confirma que el volumen actual es superior a un factor multiplicativo de la media móvil del volumen.
    """
    media_movil_volumen = prices['Volume'].rolling(window=window).mean()
    volumen_actual = prices['Volume'].iloc[-1].item()
    media_volumen_actual = media_movil_volumen.iloc[-1].item()
    condicion = volumen_actual > factor * media_volumen_actual
    return condicion, volumen_actual, media_volumen_actual


def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Suavizado de Wilder (equivalente al RMA que usa TradingView)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calcular_adx(df, period=14):
    df = df.copy()

    df["TR"] = np.maximum.reduce([
        df["High"] - df["Low"],
        abs(df["High"] - df["Close"].shift(1)),
        abs(df["Low"] - df["Close"].shift(1))
    ])

    df["+DM"] = np.where((df["High"] - df["High"].shift(1)) > (df["Low"].shift(1) - df["Low"]),
                         np.maximum(df["High"] - df["High"].shift(1), 0), 0)
    df["-DM"] = np.where((df["Low"].shift(1) - df["Low"]) > (df["High"] - df["High"].shift(1)),
                         np.maximum(df["Low"].shift(1) - df["Low"], 0), 0)

    atr = df["TR"].ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    plus_di = 100 * df["+DM"].ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr
    minus_di = 100 * df["-DM"].ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    return adx


# Funciones de Análisis Independientes
async def analizar_multiples_acciones_1d(tickers, resultados):
    cruces_alcistas_ema = []
    cruces_bajistas_ema = []
    cruces_alcistas_macd = []
    cruces_bajistas_macd = []
    sin_datos = []
    sin_procesar = []
    volumen_fuerte_1d = []
    total_procesados = 0
    total_tickers = len(tickers)
    rsi_sobrevendido = []
    rsi_sobrecomprado = []
    adx_fuerte = []

    print("Ejecutando análisis en 1D")
    # Inicializar la barra de progreso
    actualizar_progreso(total_procesados, total_tickers)

    async def procesar_ticker(ticker):
        nonlocal total_procesados
        try:
            # Fechas
            end_date = pd.Timestamp.now() - pd.DateOffset(days=1)
            start_date = end_date - pd.DateOffset(years=2)

            # Precios
            prices = obtener_precios(ticker, start_date, end_date, interval='1d')
            if prices is None or prices.empty:
                sin_datos.append(ticker)
                return

            # RSI
            prices["RSI"] = calcular_rsi(prices["Close"])
            ultimo_rsi = prices["RSI"].iloc[-1] if not prices["RSI"].isna().all() else None

            if ultimo_rsi is not None:
                if ultimo_rsi < 30:
                    rsi_sobrevendido.append(ticker)
                elif ultimo_rsi > 70:
                    rsi_sobrecomprado.append(ticker)

            # ADX
            prices["ADX"] = calcular_adx(prices)
            ultimo_adx = prices["ADX"].iloc[-1] if not prices["ADX"].isna().all() else None

            # Guardar ticker con ADX fuerte
            if ultimo_adx is not None and ultimo_adx > 25:
                adx_fuerte.append(ticker)

            # EMAs
            ema50, ema200 = calcular_emas(prices)
            cruce_ema = detectar_cruce_ema(ema50, ema200)

            # MACD
            macd, signal_line = calcular_macd(prices)
            cruce_macd = detectar_cruce_macd(macd, signal_line)

            # Guardar resultados
            if cruce_ema == "alcista":
                cruces_alcistas_ema.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_ema == "bajista":
                cruces_bajistas_ema.append(ticker)
                resultados['bajistas'].append(ticker)

            if cruce_macd == "alcista":
                cruces_alcistas_macd.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_macd == "bajista":
                cruces_bajistas_macd.append(ticker)
                resultados['bajistas'].append(ticker)

            # Volumen fuerte
            condicion_volumen, volumen_actual, media_volumen_actual = confirmar_volumen(prices)
            if condicion_volumen:
                volumen_fuerte_1d.append(ticker)

            total_procesados += 1
            actualizar_progreso(total_procesados, total_tickers)

        except Exception as e:
            sin_procesar.append(ticker)
            print(f"\033[91mError al procesar {ticker}: {e}\033[0m")

    # Tareas asincrónicas
    tasks = [procesar_ticker(ticker) for ticker in tickers]
    await asyncio.gather(*tasks)

    sys.stdout.write('\n')

    # Mostrar resultados
    print("\n\033[92mResultados del análisis 1D:\033[0m")

    # EMAs
    print("\n\033[94mCruces de EMAs 50/200 1D:\033[0m")
    print(f"Cruces alcistas de EMAs 50/200 1D: {', '.join(cruces_alcistas_ema) if cruces_alcistas_ema else 'Ninguno'}")
    print(f"Cruces bajistas de EMAs 50/200 1D: {', '.join(cruces_bajistas_ema) if cruces_bajistas_ema else 'Ninguno'}")

    # MACD
    print("\n\033[94mCruces de MACD 1D:\033[0m")
    print(f"Cruces alcistas de MACD 1D: {', '.join(cruces_alcistas_macd) if cruces_alcistas_macd else 'Ninguno'}")
    print(f"Cruces bajistas de MACD 1D: {', '.join(cruces_bajistas_macd) if cruces_bajistas_macd else 'Ninguno'}")

    # Volumen
    print("\n\033[94mVolumen Fuerte 1D:\033[0m")
    print(f"{', '.join(volumen_fuerte_1d) if volumen_fuerte_1d else 'Ninguno'}")

    # RSI
    print("\n\033[94mRSI sobrevendido (<30):\033[0m")
    print(f"{', '.join(rsi_sobrevendido) if rsi_sobrevendido else 'Ninguno'}")

    print("\n\033[94mRSI sobrecomprado (>70):\033[0m")
    print(f"{', '.join(rsi_sobrecomprado) if rsi_sobrecomprado else 'Ninguno'}")

    # ADX
    print("\n\033[94mADX fuerte (>25):\033[0m")
    print(f"{', '.join(adx_fuerte) if adx_fuerte else 'Ninguno'}")

    # Final
    if not sin_datos and not sin_procesar:
        print("\n\033[92mTodos los tickers fueron procesados exitosamente.\033[0m")
    else:
        if sin_datos:
            print(f"\033[91mNo se encontraron datos para los siguientes tickers: {', '.join(sin_datos)}\033[0m")
        if sin_procesar:
            print(f"\033[91mNo se pudo procesar los siguientes tickers: {', '.join(sin_procesar)}\033[0m")

    return {
        'alcistas': cruces_alcistas_ema + cruces_alcistas_macd,
        'bajistas': cruces_bajistas_ema + cruces_bajistas_macd,
        'cruces_alcistas_ema': cruces_alcistas_ema,
        'cruces_bajistas_ema': cruces_bajistas_ema,
        'cruces_alcistas_macd': cruces_alcistas_macd,
        'cruces_bajistas_macd': cruces_bajistas_macd,
        'rsi_sobrevendido': rsi_sobrevendido,
        'rsi_sobrecomprado': rsi_sobrecomprado,
        'adx_fuerte': adx_fuerte
    }, volumen_fuerte_1d


async def analizar_multiples_acciones_1wk(tickers, resultados):
    cruces_alcistas_ema = []
    cruces_bajistas_ema = []
    cruces_alcistas_macd = []
    cruces_bajistas_macd = []
    sin_datos = []
    sin_procesar = []
    volumen_fuerte_1wk = []
    rsi_sobrevendido = []
    rsi_sobrecomprado = []
    adx_fuerte = []
    total_procesados = 0
    total_tickers = len(tickers)

    print("Ejecutando análisis en 1WK")
    actualizar_progreso(total_procesados, total_tickers)

    async def procesar_ticker(ticker):
        nonlocal total_procesados
        try:
            end_date = pd.Timestamp.now() - pd.DateOffset(weeks=1)
            start_date = end_date - pd.DateOffset(years=5)  # Ampliamos el histórico para mejor análisis

            # Obtener precios de 1 semana
            prices = obtener_precios(ticker, start_date, end_date, interval='1wk')
            if prices is None or prices.empty:
                sin_datos.append(ticker)
                return

            # Calcular RSI semanal
            prices["RSI"] = calcular_rsi(prices["Close"])
            ultimo_rsi = prices["RSI"].iloc[-1] if not prices["RSI"].isna().all() else None

            if ultimo_rsi is not None:
                if ultimo_rsi < 30:
                    rsi_sobrevendido.append(ticker)
                elif ultimo_rsi > 70:
                    rsi_sobrecomprado.append(ticker)

            # ADX
            prices["ADX"] = calcular_adx(prices)
            ultimo_adx = prices["ADX"].iloc[-1] if not prices["ADX"].isna().all() else None

            # Guardar ticker con ADX fuerte
            if ultimo_adx is not None and ultimo_adx > 25:
                adx_fuerte.append(ticker)

            # Calcular EMA de 20 y 50 semanas (equivalente a 50 y 200 días en gráfico diario)
            ema20, ema50 = calcular_emas_1wk_1mo(prices, periodo="1wk", ticker=ticker)
            cruce_ema = detectar_cruce_ema_20_50(ema20, ema50)

            # Calcular MACD
            macd, signal_line = calcular_macd(prices)
            cruce_macd = detectar_cruce_macd(macd, signal_line)

            # Verificar cruces
            if cruce_ema == "alcista":
                cruces_alcistas_ema.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_ema == "bajista":
                cruces_bajistas_ema.append(ticker)
                resultados['bajistas'].append(ticker)

            if cruce_macd == "alcista":
                cruces_alcistas_macd.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_macd == "bajista":
                cruces_bajistas_macd.append(ticker)
                resultados['bajistas'].append(ticker)

            # Confirmar volumen
            condicion_volumen, volumen_actual, media_volumen_actual = confirmar_volumen(prices)
            if condicion_volumen:
                volumen_fuerte_1wk.append(ticker)

            total_procesados += 1
            actualizar_progreso(total_procesados, total_tickers)

        except Exception as e:
            sin_procesar.append(ticker)
            print(f"\033[91mError al procesar {ticker}: {e}\033[0m")

    tasks = [procesar_ticker(ticker) for ticker in tickers]
    await asyncio.gather(*tasks)

    sys.stdout.write('\n')
    print("\n\033[92mResultados del análisis 1WK:\033[0m")

    print("\n\033[94mCruces de EMAs 20/50 1WK:\033[0m")
    print(f"Cruces alcistas de EMAs 20/50 1WK: {', '.join(cruces_alcistas_ema) if cruces_alcistas_ema else 'Ninguno'}")
    print(f"Cruces bajistas de EMAs 20/50 1WK: {', '.join(cruces_bajistas_ema) if cruces_bajistas_ema else 'Ninguno'}")

    print("\n\033[94mCruces de MACD 1WK:\033[0m")
    print(f"Cruces alcistas de MACD 1WK: {', '.join(cruces_alcistas_macd) if cruces_alcistas_macd else 'Ninguno'}")
    print(f"Cruces bajistas de MACD 1WK: {', '.join(cruces_bajistas_macd) if cruces_bajistas_macd else 'Ninguno'}")

    print("\n\033[94mVolumen Fuerte 1WK:\033[0m")
    print(f"{', '.join(volumen_fuerte_1wk) if volumen_fuerte_1wk else 'Ninguno'}")

    print("\n\033[94mRSI sobrevendido (<30) 1WK:\033[0m")
    print(f"{', '.join(rsi_sobrevendido) if rsi_sobrevendido else 'Ninguno'}")

    print("\n\033[94mRSI sobrecomprado (>70) 1WK:\033[0m")
    print(f"{', '.join(rsi_sobrecomprado) if rsi_sobrecomprado else 'Ninguno'}")

    # ADX
    print("\n\033[94mADX fuerte (>25):\033[0m")
    print(f"{', '.join(adx_fuerte) if adx_fuerte else 'Ninguno'}")

    if not sin_datos and not sin_procesar:
        print("\n\033[92mTodos los tickers fueron procesados exitosamente.\033[0m")
    else:
        if sin_datos:
            print(f"\033[91mNo se encontraron datos para los siguientes tickers: {', '.join(sin_datos)}\033[0m")
        if sin_procesar:
            print(f"\033[91mNo se pudo procesar los siguientes tickers: {', '.join(sin_procesar)}\033[0m")

    return {
        'alcistas': cruces_alcistas_ema + cruces_alcistas_macd,
        'bajistas': cruces_bajistas_ema + cruces_bajistas_macd,
        'cruces_alcistas_ema': cruces_alcistas_ema,
        'cruces_bajistas_ema': cruces_bajistas_ema,
        'cruces_alcistas_macd': cruces_alcistas_macd,
        'cruces_bajistas_macd': cruces_bajistas_macd,
        'rsi_sobrevendido': rsi_sobrevendido,
        'rsi_sobrecomprado': rsi_sobrecomprado,
        'adx_fuerte': adx_fuerte
    }, volumen_fuerte_1wk


async def analizar_multiples_acciones_1mo(tickers, resultados):
    cruces_alcistas_ema = []
    cruces_bajistas_ema = []
    cruces_alcistas_macd = []
    cruces_bajistas_macd = []
    sin_datos = []
    sin_procesar = []
    volumen_fuerte_1mo = []
    rsi_sobrevendido = []
    rsi_sobrecomprado = []
    adx_fuerte = []
    total_procesados = 0
    total_tickers = len(tickers)

    print("Ejecutando análisis en 1MO")
    actualizar_progreso(total_procesados, total_tickers)

    async def procesar_ticker(ticker):
        nonlocal total_procesados
        try:
            end_date = pd.Timestamp.now().replace(day=1) - pd.DateOffset(days=1)
            start_date = end_date - pd.DateOffset(years=20)

            # Obtener precios de 1 mes
            prices = obtener_precios(ticker, start_date, end_date, interval='1mo')
            if prices is None or prices.empty:
                sin_datos.append(ticker)
                return

            # Calcular RSI mensual
            prices["RSI"] = calcular_rsi(prices["Close"])
            ultimo_rsi = prices["RSI"].iloc[-1] if not prices["RSI"].isna().all() else None

            if ultimo_rsi is not None:
                if ultimo_rsi < 30:
                    rsi_sobrevendido.append(ticker)
                elif ultimo_rsi > 70:
                    rsi_sobrecomprado.append(ticker)

            # ADX
            prices["ADX"] = calcular_adx(prices)
            ultimo_adx = prices["ADX"].iloc[-1] if not prices["ADX"].isna().all() else None

            # Guardar ticker con ADX fuerte
            if ultimo_adx is not None and ultimo_adx > 25:
                adx_fuerte.append(ticker)

            # Calcular EMA de 20 y 50 meses
            ema20, ema50 = calcular_emas_1wk_1mo(prices, periodo="1mo", ticker=ticker)
            cruce_ema = detectar_cruce_ema_20_50(ema20, ema50)

            # Calcular MACD
            macd, signal_line = calcular_macd(prices)
            cruce_macd = detectar_cruce_macd(macd, signal_line)

            # Verificar cruces
            if cruce_ema == "alcista":
                cruces_alcistas_ema.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_ema == "bajista":
                cruces_bajistas_ema.append(ticker)
                resultados['bajistas'].append(ticker)

            if cruce_macd == "alcista":
                cruces_alcistas_macd.append(ticker)
                resultados['alcistas'].append(ticker)
            elif cruce_macd == "bajista":
                cruces_bajistas_macd.append(ticker)
                resultados['bajistas'].append(ticker)

            # Confirmar volumen
            condicion_volumen, volumen_actual, media_volumen_actual = confirmar_volumen(prices)
            if condicion_volumen:
                volumen_fuerte_1mo.append(ticker)

            total_procesados += 1
            actualizar_progreso(total_procesados, total_tickers)

        except Exception as e:
            sin_procesar.append(ticker)
            print(f"\033[91mError al procesar {ticker}: {e}\033[0m")

    tasks = [procesar_ticker(ticker) for ticker in tickers]
    await asyncio.gather(*tasks)

    sys.stdout.write('\n')
    print("\n\033[92mResultados del análisis 1MO:\033[0m")

    print("\n\033[94mCruces de EMAs 20/50 1MO:\033[0m")
    print(f"Cruces alcistas de EMAs 20/50 1MO: {', '.join(cruces_alcistas_ema) if cruces_alcistas_ema else 'Ninguno'}")
    print(f"Cruces bajistas de EMAs 20/50 1MO: {', '.join(cruces_bajistas_ema) if cruces_bajistas_ema else 'Ninguno'}")

    print("\n\033[94mCruces de MACD 1MO:\033[0m")
    print(f"Cruces alcistas de MACD 1MO: {', '.join(cruces_alcistas_macd) if cruces_alcistas_macd else 'Ninguno'}")
    print(f"Cruces bajistas de MACD 1MO: {', '.join(cruces_bajistas_macd) if cruces_bajistas_macd else 'Ninguno'}")

    print("\n\033[94mVolumen Fuerte 1MO:\033[0m")
    print(f"{', '.join(volumen_fuerte_1mo) if volumen_fuerte_1mo else 'Ninguno'}")

    print("\n\033[94mRSI sobrevendido (<30) 1MO:\033[0m")
    print(f"{', '.join(rsi_sobrevendido) if rsi_sobrevendido else 'Ninguno'}")

    print("\n\033[94mRSI sobrecomprado (>70) 1MO:\033[0m")
    print(f"{', '.join(rsi_sobrecomprado) if rsi_sobrecomprado else 'Ninguno'}")

    # ADX
    print("\n\033[94mADX fuerte (>25):\033[0m")
    print(f"{', '.join(adx_fuerte) if adx_fuerte else 'Ninguno'}")

    if not sin_datos and not sin_procesar:
        print("\n\033[92mTodos los tickers fueron procesados exitosamente.\033[0m")
    else:
        if sin_datos:
            print(f"\033[91mNo se encontraron datos para los siguientes tickers: {', '.join(sin_datos)}\033[0m")
        if sin_procesar:
            print(f"\033[91mNo se pudo procesar los siguientes tickers: {', '.join(sin_procesar)}\033[0m")

    return {
        'alcistas': cruces_alcistas_ema + cruces_alcistas_macd,
        'bajistas': cruces_bajistas_ema + cruces_bajistas_macd,
        'cruces_alcistas_ema': cruces_alcistas_ema,
        'cruces_bajistas_ema': cruces_bajistas_ema,
        'cruces_alcistas_macd': cruces_alcistas_macd,
        'cruces_bajistas_macd': cruces_bajistas_macd,
        'rsi_sobrevendido': rsi_sobrevendido,
        'rsi_sobrecomprado': rsi_sobrecomprado,
        'adx_fuerte': adx_fuerte
    }, volumen_fuerte_1mo


# Función para verificar coincidencias generales
async def verificar_coincidencias_generales(
    resultados_1d, resultados_1wk, resultados_1mo,
    volumen_fuerte_1d, volumen_fuerte_1wk, volumen_fuerte_1mo,
    rsi_sobrevendido_1d, rsi_sobrevendido_1wk, rsi_sobrevendido_1mo,
    rsi_sobrecomprado_1d, rsi_sobrecomprado_1wk, rsi_sobrecomprado_1mo,
    adx_fuerte_1d, adx_fuerte_1wk, adx_fuerte_1mo
):
    # Diccionarios para almacenar coincidencias
    coincidencias_alcistas_fuertes = {}
    coincidencias_alcistas_vol = {}
    coincidencias_alcistas_rsi = {}

    coincidencias_bajistas_fuertes = {}
    coincidencias_bajistas_vol = {}
    coincidencias_bajistas_rsi = {}

    coincidencias_adx = {}

    # Función auxiliar para agregar detalle
    def agregar_detalle(ticker, tipo, fuente, intervalo):
        entrada = f"{fuente} {intervalo}"
        if fuente in ["EMA", "MACD"]:
            if tipo == "alcista":
                coincidencias_alcistas_fuertes.setdefault(ticker, []).append(entrada)
            else:
                coincidencias_bajistas_fuertes.setdefault(ticker, []).append(entrada)
        elif fuente == "VOL":
            if tipo == "alcista":
                coincidencias_alcistas_vol.setdefault(ticker, []).append(entrada)
            else:
                coincidencias_bajistas_vol.setdefault(ticker, []).append(entrada)
        elif fuente == "RSI":
            if tipo == "alcista":
                coincidencias_alcistas_rsi.setdefault(ticker, []).append(entrada)
            else:
                coincidencias_bajistas_rsi.setdefault(ticker, []).append(entrada)
        elif fuente == "ADX":
            coincidencias_adx.setdefault(ticker, []).append(entrada)

    # Procesar señales fuertes (EMA y MACD)
    for datos, intervalo in [(resultados_1d, "1d"), (resultados_1wk, "1wk"), (resultados_1mo, "1mo")]:
        for ticker in datos['alcistas']:
            if ticker in datos['cruces_alcistas_ema']:
                agregar_detalle(ticker, "alcista", "EMA", intervalo)
            if ticker in datos['cruces_alcistas_macd']:
                agregar_detalle(ticker, "alcista", "MACD", intervalo)
        for ticker in datos['bajistas']:
            if ticker in datos['cruces_bajistas_ema']:
                agregar_detalle(ticker, "bajista", "EMA", intervalo)
            if ticker in datos['cruces_bajistas_macd']:
                agregar_detalle(ticker, "bajista", "MACD", intervalo)

    # Agregar volumen si hay al menos 2 señales fuertes
    def agregar_volumen_neutral(ticker, intervalo):
        if ticker in coincidencias_alcistas_fuertes and len(coincidencias_alcistas_fuertes[ticker]) >= 2:
            agregar_detalle(ticker, "alcista", "VOL", intervalo)
        if ticker in coincidencias_bajistas_fuertes and len(coincidencias_bajistas_fuertes[ticker]) >= 2:
            agregar_detalle(ticker, "bajista", "VOL", intervalo)

    for ticker in volumen_fuerte_1d:
        agregar_volumen_neutral(ticker, "1d")
    for ticker in volumen_fuerte_1wk:
        agregar_volumen_neutral(ticker, "1wk")
    for ticker in volumen_fuerte_1mo:
        agregar_volumen_neutral(ticker, "1mo")

    # Agregar RSI si hay al menos 2 señales fuertes
    def agregar_rsi_neutral(ticker, intervalo, tipo):
        if tipo == "alcista":
            if ticker in coincidencias_alcistas_fuertes and len(coincidencias_alcistas_fuertes[ticker]) >= 2:
                print(f"[RSI] ✅ Agregando RSI sobrevendido como señal alcista para {ticker} ({intervalo})")
                agregar_detalle(ticker, "alcista", "RSI", intervalo)
        elif tipo == "bajista":
            if ticker in coincidencias_bajistas_fuertes and len(coincidencias_bajistas_fuertes[ticker]) >= 2:
                print(f"[RSI] 🔻 Agregando RSI sobrecomprado como señal bajista para {ticker} ({intervalo})")
                agregar_detalle(ticker, "bajista", "RSI", intervalo)

    for ticker in rsi_sobrevendido_1d:
        agregar_rsi_neutral(ticker, "1d", "alcista")
    for ticker in rsi_sobrevendido_1wk:
        agregar_rsi_neutral(ticker, "1wk", "alcista")
    for ticker in rsi_sobrevendido_1mo:
        agregar_rsi_neutral(ticker, "1mo", "alcista")

    for ticker in rsi_sobrecomprado_1d:
        agregar_rsi_neutral(ticker, "1d", "bajista")
    for ticker in rsi_sobrecomprado_1wk:
        agregar_rsi_neutral(ticker, "1wk", "bajista")
    for ticker in rsi_sobrecomprado_1mo:
        agregar_rsi_neutral(ticker, "1mo", "bajista")

    # ✅ Agregar ADX como refuerzo neutral
    def agregar_adx_neutral(ticker, intervalo):
        if (
            (ticker in coincidencias_alcistas_fuertes and len(coincidencias_alcistas_fuertes[ticker]) >= 2) or
            (ticker in coincidencias_bajistas_fuertes and len(coincidencias_bajistas_fuertes[ticker]) >= 2)
        ):
            agregar_detalle(ticker, "neutral", "ADX", intervalo)

    for ticker in adx_fuerte_1d:
        agregar_adx_neutral(ticker, "1d")
    for ticker in adx_fuerte_1wk:
        agregar_adx_neutral(ticker, "1wk")
    for ticker in adx_fuerte_1mo:
        agregar_adx_neutral(ticker, "1mo")

    # Verifica contradicción con RSI
    def contradice_rsi(ticker, tipo):
        if tipo == "bajista":
            return (
                ticker in rsi_sobrevendido_1d or
                ticker in rsi_sobrevendido_1wk or
                ticker in rsi_sobrevendido_1mo
            )
        elif tipo == "alcista":
            return (
                ticker in rsi_sobrecomprado_1d or
                ticker in rsi_sobrecomprado_1wk or
                ticker in rsi_sobrecomprado_1mo
            )
        return False

    # Colorear señales
    def colorear_detalle(detalle):
        if detalle.startswith("EMA"):
            return f"\033[92m{detalle}\033[0m"  # Verde
        elif detalle.startswith("MACD"):
            return f"\033[94m{detalle}\033[0m"  # Azul
        elif detalle.startswith("VOL"):
            return f"\033[91m{detalle}\033[0m"  # Rojo
        elif detalle.startswith("RSI"):
            return f"\033[93m⭐ {detalle}\033[0m"  # Amarillo + estrella
        elif detalle.startswith("ADX"):
            return f"\033[96m{detalle}\033[0m"  # Cian + ícono
        return detalle

    # Mostrar resultados alcistas
    print("\n\033[1m\033[94mCruces alcistas con coincidencias fuertes (min 2):\033[0m")
    for ticker, detalles in coincidencias_alcistas_fuertes.items():
        if len(detalles) >= 2:
            extras_vol = coincidencias_alcistas_vol.get(ticker, [])
            extras_rsi = coincidencias_alcistas_rsi.get(ticker, [])
            extras_adx = coincidencias_adx.get(ticker, [])
            todos = detalles + extras_vol + extras_rsi + extras_adx
            detalles_coloreados = [colorear_detalle(d) for d in todos]

            advertencia = ""
            if contradice_rsi(ticker, "alcista"):
                advertencia = f"\033[93m ⚠️ {ticker} tiene RSI sobrecomprado (posible contradicción)\033[0m"

            print(f"{ticker} ({' + '.join(detalles_coloreados)}){advertencia}")

    # Mostrar resultados bajistas
    print("\n\033[1m\033[94mCruces bajistas con coincidencias fuertes (min 2):\033[0m")
    for ticker, detalles in coincidencias_bajistas_fuertes.items():
        if len(detalles) >= 2:
            extras_vol = coincidencias_bajistas_vol.get(ticker, [])
            extras_rsi = coincidencias_bajistas_rsi.get(ticker, [])
            extras_adx = coincidencias_adx.get(ticker, [])
            todos = detalles + extras_vol + extras_rsi + extras_adx
            detalles_coloreados = [colorear_detalle(d) for d in todos]

            advertencia = ""
            if contradice_rsi(ticker, "bajista"):
                advertencia = f"\033[93m ⚠️ {ticker} tiene RSI sobrevendido (posible contradicción)\033[0m"

            print(f"{ticker} ({' + '.join(detalles_coloreados)}){advertencia}")

# Función Principal con Menú de Selección
async def main():
    while True:
        print("\nSeleccione el análisis que desea ejecutar:")
        print("1. Análisis intervalo 1D")
        print("2. Análisis intervalo 1WK")
        print("3. Análisis intervalo 1MO")
        print("4. Ejecutar todos los análisis")
        print("5. Salir")

        opcion = input("Ingrese el número de la opción deseada: ")

        if opcion == '1':
            print("\nIniciando análisis de 1 día...\n")
            resultados_1d, volumen_fuerte_1d = await analizar_multiples_acciones_1d(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )
            print("\nAnálisis 1D completado.")

        elif opcion == '2':
            print("\nIniciando análisis de 1 semana...\n")
            resultados_1wk, volumen_fuerte_1wk = await analizar_multiples_acciones_1wk(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )
            print("\nAnálisis 1WK completado.")

        elif opcion == '3':
            print("\nIniciando análisis de 1 mes...\n")
            resultados_1mo, volumen_fuerte_1mo = await analizar_multiples_acciones_1mo(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )
            print("\nAnálisis 1MO completado.")

        elif opcion == '4':
            print("\nIniciando todos los análisis...\n")

            # Análisis 1D
            resultados_1d, volumen_fuerte_1d = await analizar_multiples_acciones_1d(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )

            # Análisis 1WK
            resultados_1wk, volumen_fuerte_1wk = await analizar_multiples_acciones_1wk(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )

            # Análisis 1MO
            resultados_1mo, volumen_fuerte_1mo = await analizar_multiples_acciones_1mo(
                tickers_seleccionados,
                {'alcistas': [], 'bajistas': []}
            )

            # Verificación de coincidencias generales con RSI, Volumen y ADX como señales adicionales
            await verificar_coincidencias_generales(
                resultados_1d, resultados_1wk, resultados_1mo,
                volumen_fuerte_1d, volumen_fuerte_1wk, volumen_fuerte_1mo,
                resultados_1d.get('rsi_sobrevendido', []),
                resultados_1wk.get('rsi_sobrevendido', []),
                resultados_1mo.get('rsi_sobrevendido', []),
                resultados_1d.get('rsi_sobrecomprado', []),
                resultados_1wk.get('rsi_sobrecomprado', []),
                resultados_1mo.get('rsi_sobrecomprado', []),
                resultados_1d.get('adx_fuerte', []),
                resultados_1wk.get('adx_fuerte', []),
                resultados_1mo.get('adx_fuerte', [])
            )

            print("\nAnálisis completo ejecutado correctamente.")

        elif opcion == '5':
            print("Saliendo del programa.")
            break

        else:
            print("Opción no válida. Por favor, intente de nuevo.")


if __name__ == "__main__":
    asyncio.run(main())
