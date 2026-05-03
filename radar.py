import requests
import time
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

TIMEFRAMES = ["5m", "15m", "1h", "2h", "4h"]

# ==============================
# TELEGRAM
# ==============================
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)

# ==============================
# TOP CRYPTO DINÁMICO
# ==============================
def top_crypto():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()

    usdt = [x for x in data if "USDT" in x["symbol"]]
    usdt.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)

    return [x["symbol"] for x in usdt[:20]]

# ==============================
# DATOS
# ==============================
def get_klines(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    return requests.get(url).json()

# ==============================
# ANALISIS
# ==============================
def analizar(symbol, tf):
    datos = get_klines(symbol, tf)

    # FIX ERROR (evita crash)
    cierres = [float(c[4]) for c in datos if isinstance(c, list) and len(c) > 4]

    if len(cierres) < 50:
        return None

    ema20 = sum(cierres[-20:]) / 20
    ema50 = sum(cierres[-50:]) / 50

    if ema20 > ema50:
        return "LONG"
    elif ema20 < ema50:
        return "SHORT"

    return None

# ==============================
# MAIN LOOP
# ==============================
def main():
    print("🚀 RADAR ACTIVO")

    while True:
        try:
            cryptos = top_crypto()
            print("TOP:", cryptos[:5])

            for symbol in cryptos:
                for tf in TIMEFRAMES:

                    resultado = analizar(symbol, tf)

                    if resultado:
                        mensaje = f"""🚨 CRYPTO
{symbol} | {tf}
Dirección: {resultado}
Hora: {datetime.now().strftime('%H:%M:%S')}"""

                        print(mensaje)
                        enviar_telegram(mensaje)

            print("----- ESCANEO -----\n")
            time.sleep(60)

        except Exception as e:
            print("ERROR GENERAL:", e)
            time.sleep(30)

# ==============================
# START
# ==============================
if __name__ == "__main__":
    main()
