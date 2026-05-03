import requests
import time
import os

# =========================
# CONFIG
# =========================
TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

# =========================
# ACTIVOS (SOLO VÁLIDOS BINANCE)
# =========================
SYMBOLS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","MATICUSDT",
    "TRXUSDT","LTCUSDT","DOTUSDT","ATOMUSDT","NEARUSDT",
    "APTUSDT","ARBUSDT","OPUSDT","SUIUSDT","INJUSDT"
]

TIMEFRAMES = ["5m","15m","30m","1h","4h"]

# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Faltan TOKEN o CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)

# =========================
# DATA BINANCE (PROTEGIDO)
# =========================
def get_data(symbol, tf):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=100"
        data = requests.get(url).json()

        # VALIDACIÓN 🔥
        if not isinstance(data, list) or len(data) < 2:
            return None

        closes = [float(x[4]) for x in data]
        highs = [float(x[2]) for x in data]
        lows = [float(x[3]) for x in data]
        volumes = [float(x[5]) for x in data]

        return closes, highs, lows, volumes

    except Exception as e:
        print(f"Error datos {symbol}: {e}")
        return None

# =========================
# VWAP
# =========================
def vwap_calc(h, l, c, v):
    pv = 0
    vol = 0
    vwap = []

    for i in range(len(c)):
        tp = (h[i] + l[i] + c[i]) / 3
        pv += tp * v[i]
        vol += v[i]
        vwap.append(pv / vol)

    return vwap

# =========================
# SEÑALES (TU LÓGICA EXACTA)
# =========================
def signal(symbol, tf):

    data = get_data(symbol, tf)
    if data is None:
        return None

    c, h, l, v = data
    vw = vwap_calc(h, l, c, v)

    if len(c) < 2:
        return None

    price = c[-1]
    prev = c[-2]

    vwap_now = vw[-1]
    vwap_prev = vw[-2]

    # CONDICIONES LONG
    cond1_long = price > vwap_now
    cond2_long = price > prev
    cond3_long = vwap_now > vwap_prev

    # CONDICIONES SHORT
    cond1_short = price < vwap_now
    cond2_short = price < prev
    cond3_short = vwap_now < vwap_prev

    score_long = sum([cond1_long, cond2_long, cond3_long])
    score_short = sum([cond1_short, cond2_short, cond3_short])

    # CRUCE VWAP
    cross_long = prev < vwap_prev and price > vwap_now
    cross_short = prev > vwap_prev and price < vwap_now

    # REGLAS SEGÚN TF
    min_score = 2 if tf == "5m" else 3

    # SEÑALES
    if score_long >= min_score and cross_long:
        return "LONG", score_long

    if score_short >= min_score and cross_short:
        return "SHORT", score_short

    return None

# =========================
# LOOP PRINCIPAL
# =========================
print("🚀 ORION RADAR PRO ACTIVO")
enviar_telegram("✅ BOT FUNCIONANDO")
while True:
    try:
        for symbol in SYMBOLS:
            for tf in TIMEFRAMES:

                s = signal(symbol, tf)

                if s:
                    tipo, score = s

                    msg = f"""
🚨 SEÑAL ORION

📊 {symbol}
⏱ TF: {tf}
📈 Tipo: {tipo}
🔥 Score: {score}

VWAP + Momentum + Tendencia
"""

                    print(msg)
                    enviar_telegram(msg)

        time.sleep(60)

    except Exception as e:
        print("ERROR GENERAL:", e)
        time.sleep(60)
