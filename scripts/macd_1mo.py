import yfinance as yf
import pandas as pd


def obtener_precios_mensuales(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date, interval='1mo', auto_adjust=False)
    return data['Close']


def calcular_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data.ewm(span=short_window, adjust=False).mean()
    long_ema = data.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal_line


def detectar_cruce_mensual(macd, signal_line):
    cruces = {
        'alcista_actual': False,
        'bajista_actual': False,
        'alcista_anterior': False,
        'bajista_anterior': False
    }
    if len(macd) < 3:
        return cruces

    cruces['alcista_actual'] = (macd.iloc[-2] < signal_line.iloc[-2]) and (macd.iloc[-1] > signal_line.iloc[-1])
    cruces['bajista_actual'] = (macd.iloc[-2] > signal_line.iloc[-2]) and (macd.iloc[-1] < signal_line.iloc[-1])
    cruces['alcista_anterior'] = (macd.iloc[-3] < signal_line.iloc[-3]) and (macd.iloc[-2] > signal_line.iloc[-2])
    cruces['bajista_anterior'] = (macd.iloc[-3] > signal_line.iloc[-3]) and (macd.iloc[-2] < signal_line.iloc[-2])
    return cruces


def analizar_macd_mensual(tickers):
    resultados = {
        "alcistas_actual": [],
        "bajistas_actual": [],
        "alcistas_anterior": [],
        "bajistas_anterior": [],
        "sin_procesar": []
    }

    end_date = pd.Timestamp.now()
    start_date = end_date - pd.DateOffset(years=5)

    for ticker in tickers:
        try:
            prices = obtener_precios_mensuales(ticker, start_date, end_date)
            macd, signal_line = calcular_macd(prices)
            cruces = detectar_cruce_mensual(macd, signal_line)

            if cruces['alcista_actual']:
                resultados['alcistas_actual'].append(ticker)
            if cruces['bajista_actual']:
                resultados['bajistas_actual'].append(ticker)
            if cruces['alcista_anterior']:
                resultados['alcistas_anterior'].append(ticker)
            if cruces['bajista_anterior']:
                resultados['bajistas_anterior'].append(ticker)

        except Exception as e:
            resultados['sin_procesar'].append(ticker)

    return resultados
