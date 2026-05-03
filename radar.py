import requests
import time
import os

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"
# ============================
# TELEGRAM
# ============================

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Error Telegram:", e)

# ============================
# TEST INICIO
# ============================

enviar_telegram("🚀 ORION RADAR PRO ACTIVO")

# ============================
# ACTIVOS
# ============================

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "TRXUSDT", "ETCUSDT", "ATOMUSDT",
    "XLMUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "NEARUSDT"
]

timeframes = ["5m", "15m", "1h"]

# ============================
# DATOS BINANCE FUTUROS
# ============================

def obtener_datos(symbol, interval):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=50"
    response = requests.get(url)
    data = response.json()
    return data

# ============================
# EVALUAR (FORZADO PARA TEST)
# ============================

def evaluar(symbol, tf):
    try:
        data = obtener_datos(symbol, tf)

        # Debug
        print(f"{symbol} {tf} datos recibidos:", len(data))

        # 🔥 TEST FORZADO
        return "LONG"

    except Exception as e:
        print("Error evaluar:", e)
        return None

# ============================
# LOOP PRINCIPAL
# ============================

while True:
    print("🔄 escaneando mercado...")

    for symbol in symbols:
        for tf in timeframes:

            señal = evaluar(symbol, tf)

            if señal:
                mensaje = f"""
🚨 SEÑAL

Activo: {symbol}
TF: {tf}
Dirección: {señal}
"""

                print("Enviando señal:", mensaje)
                enviar_telegram(mensaje)

                time.sleep(1)

    time.sleep(20)
