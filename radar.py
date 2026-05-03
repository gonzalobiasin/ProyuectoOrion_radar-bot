import requests
import time
import os

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g")
CHAT_ID = os.getenv("6974761713")

# =========================
# ACTIVOS (20 CRIPTO + EXTRA)
# =========================
SYMBOLS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","MATICUSDT",
    "TRXUSDT","LTCUSDT","DOTUSDT","ATOMUSDT","NEARUSDT",
    "APTUSDT","ARBUSDT","OPUSDT","SUIUSDT","INJUSDT",

    # FOREX / COMMODITIES
    "EURUSDT","GBPUSDT","XAUUSDT"
]

TIMEFRAMES = ["5m","15m","30m","1h","4h"]

# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# =========================
# DATA BINANCE
# =========================
def get_data(symbol, tf):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=100"
    data = requests.get(url).json()

    closes = [float(x[4]) for x in data]
    highs = [float(x[2]) for x in data]
    lows = [float(x[3]) for x in data]
    volumes = [float(x[5]) for x in data]

    return closes, highs, lows, volumes

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

    c, h, l, v = get_data(symbol, tf)
    vw = vwap_calc(h, l, c, v)

    if len(c) < 2:
        return None

    price = c[-1]
    prev = c[-2]

    vwap_now = vw[-1]
    vwap_prev = vw[-2]

    # CONDICIONES
    long_cond = [
        price > vwap_now,
        price > prev,
        vwap_now > vwap_prev
    ]

    short_cond = [
        price < vwap_now,
        price < prev,
        vwap_now < vwap_prev
    ]

    score_long = sum(long_cond)
    score_short = sum(short_cond)

    # CRUCE
    cross_long = prev < vwap_prev and price > vwap_now
    cross_short = prev > vwap_prev and price < vwap_now

    # REGLAS
    min_score = 2 if tf == "5m" else 3

    if score_long >= min_score and cross_long:
        return "LONG", score_long

    if score_short >= min_score and cross_short:
        return "SHORT", score_short

    return None

# =========================
# LOOP
# =========================
print("🚀 ORION RADAR PRO ACTIVO")

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
⏱ {tf}
📈 {tipo}
🔥 Score: {score}

VWAP + Momentum + Tendencia
"""

                    print(msg)
                    enviar_telegram(msg)

        time.sleep(60)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(60)
