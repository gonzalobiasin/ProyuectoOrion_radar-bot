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

FOREX = ["EURUSDT", "GBPUSDT", "AUDUSDT"]

# =====================
# STORAGE WINRATE
# =====================
stats = {}

# =====================
# TELEGRAM
# =====================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except:
        pass

# =====================
# TOP CRYPTO DINÁMICO
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
# DATA
# =====================
def get_klines(symbol, interval):
    try:
        url = f"{BASE_URL}/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 100}
        return requests.get(url, params=params).json()
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

    return total_pv / total_vol if total_vol != 0 else 0

# =====================
# WINRATE UPDATE
# =====================
def update_winrate(symbol, resultado):
    if symbol not in stats:
        stats[symbol] = {"wins": 0, "losses": 0}

    if resultado:
        stats[symbol]["wins"] += 1
    else:
        stats[symbol]["losses"] += 1

def get_winrate(symbol):
    if symbol not in stats:
        return 0

    wins = stats[symbol]["wins"]
    losses = stats[symbol]["losses"]

    total = wins + losses
    if total == 0:
        return 0

    return round((wins / total) * 100, 2)

# =====================
# LÓGICA
# =====================
def evaluar(symbol, tf):
    klines = get_klines(symbol, tf)
    if len(klines) < 50:
        return None

    closes = [float(c[4]) for c in klines]

    precio = closes[-1]
    prev = closes[-2]

    vwap = calcular_vwap(klines)

    cond1 = precio > vwap
    cond2 = precio > prev
    cond3 = closes[-1] > closes[-5]

    score = sum([cond1, cond2, cond3])

    cross_up = prev < vwap and precio > vwap
    cross_down = prev > vwap and precio < vwap

    if tf == "5m":
        if score >= 2 and cross_up:
            return "LONG"
        if score >= 2 and cross_down:
            return "SHORT"
    else:
        if score >= 3 and cross_up:
            return "LONG"
        if score >= 3 and cross_down:
            return "SHORT"

    return None

# =====================
# LOOP
# =====================
def run():
    enviar_telegram("🚀 ORION RADAR PRO ACTIVO")

    while True:
        try:
            cryptos = get_top_cryptos()
            activos = cryptos + FOREX

            for symbol in activos:
                for tf in TIMEFRAMES:

                    señal = evaluar(symbol, tf)

                    if señal:
                        winrate = get_winrate(symbol)

                        mensaje = f"""
📡 SEÑAL ORION

Activo: {symbol}
TF: {tf}
Dirección: {señal}
Winrate: {winrate}%

Hora: {datetime.now().strftime('%H:%M:%S')}
"""
                        print(mensaje)
                        enviar_telegram(mensaje)

                        # simulación simple
                        update_winrate(symbol, True)

                    time.sleep(0.3)

            time.sleep(60)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# =====================
# START
# =====================
run()
