import requests
import time
from datetime import datetime

# =====================
# CONFIG
# =====================
TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

# Binance FUTUROS
BASE_URL = "https://fapi.binance.com/fapi/v1"

TIMEFRAMES = ["5m", "15m", "1h", "4h"]

# Forex (Binance pares contra USDT)
FOREX = [
    "EURUSDT", "GBPUSDT", "AUDUSDT",
    "USDJPY", "USDCAD", "USDCHF"
]

# =====================
# TELEGRAM
# =====================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)

# =====================
# TOP 20 CRYPTO DINÁMICAS
# =====================
def get_top_cryptos():
    try:
        url = f"{BASE_URL}/ticker/24hr"
        data = requests.get(url).json()

        # filtrar solo USDT perpetuos
        pares = [d for d in data if d["symbol"].endswith("USDT")]

        # ordenar por volumen
        pares.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)

        top = [p["symbol"] for p in pares[:20]]

        return top
    except:
        return ["BTCUSDT", "ETHUSDT"]

# =====================
# DATA
# =====================
def get_klines(symbol, interval):
    try:
        url = f"{BASE_URL}/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 100}
        data = requests.get(url, params=params).json()
        return data
    except:
        return []

# =====================
# VWAP
# =====================
def calcular_vwap(klines):
    total_pv = 0
    total_vol = 0

    for k in klines:
        close = float(k[4])
        volume = float(k[5])
        total_pv += close * volume
        total_vol += volume

    if total_vol == 0:
        return 0

    return total_pv / total_vol

# =====================
# CONDICIONES
# =====================
def evaluar(symbol, tf):
    klines = get_klines(symbol, tf)
    if len(klines) < 50:
        return None

    cierres = []
    for c in klines:
        try:
            cierres.append(float(c[4]))
        except:
            return None

    vwap = calcular_vwap(klines)

    precio = cierres[-1]
    prev = cierres[-2]

    # tendencia simple
    tendencia_alcista = precio > vwap and prev < precio
    tendencia_bajista = precio < vwap and prev > precio

    condiciones = 0

    # condición 1: VWAP
    if precio > vwap:
        condiciones += 1

    # condición 2: momentum
    if precio > prev:
        condiciones += 1

    # condición 3: micro tendencia
    if cierres[-1] > cierres[-5]:
        condiciones += 1

    # lógica según TF
    if tf == "5m":
        if condiciones >= 2 and tendencia_alcista:
            return "LONG"
        if condiciones >= 2 and tendencia_bajista:
            return "SHORT"

    else:
        if condiciones >= 3 and tendencia_alcista:
            return "LONG"
        if condiciones >= 3 and tendencia_bajista:
            return "SHORT"

    return None

# =====================
# LOOP PRINCIPAL
# =====================
def run():
    enviar_telegram("🚀 ORION RADAR PRO ACTIVO")

    while True:
        try:
            cryptos = get_top_cryptos()
            activos = cryptos + FOREX

            print("Activos:", activos)

            for symbol in activos:
                for tf in TIMEFRAMES:

                    señal = evaluar(symbol, tf)

                    if señal:
                        mensaje = f"""
📡 SEÑAL DETECTADA

Activo: {symbol}
TF: {tf}
Dirección: {señal}
Hora: {datetime.now().strftime('%H:%M:%S')}
"""
                        print(mensaje)
                        enviar_telegram(mensaje)

                    time.sleep(0.5)

            time.sleep(60)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# =====================
# START
# =====================
run()
