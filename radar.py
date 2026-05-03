import requests
import time
from datetime import datetime

# =====================
# CONFIG
# =====================
TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

BASE_URL = "https://fapi.binance.com/fapi/v1"

TIMEFRAMES = ["5m", "15m", "1h", "4h"]

FOREX = [
    "EURUSDT", "GBPUSDT", "AUDUSDT"
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
# TOP 20 CRYPTO
# =====================
def get_top_cryptos():
    try:
        url = f"{BASE_URL}/ticker/24hr"
        data = requests.get(url).json()

        pares = [d for d in data if d["symbol"].endswith("USDT")]
        pares.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)

        return [p["symbol"] for p in pares[:20]]

    except:
        return ["BTCUSDT", "ETHUSDT"]

# =====================
# LOOP PRINCIPAL
# =====================
def run():
    enviar_telegram("🚀 TEST ORION ACTIVO")

    while True:
        try:
            cryptos = get_top_cryptos()
            activos = cryptos + FOREX

            for symbol in activos:
                for tf in TIMEFRAMES:

                    # 🔥 TEST: FORZAMOS SEÑAL
                    if tf == "5m" and symbol == "BTCUSDT":

                        mensaje = f"""
🚨 TEST SEÑAL

Activo: {symbol}
TF: {tf}
Dirección: LONG
Hora: {datetime.now().strftime('%H:%M:%S')}
"""
                        print(mensaje)
                        enviar_telegram(mensaje)

                    time.sleep(0.2)

            time.sleep(30)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# =====================
# START
# =====================
run()
