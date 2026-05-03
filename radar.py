import requests
import time
from datetime import datetime

# =========================
# CONFIG
# =========================
TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

SYMBOLS = ["BTCUSDT", "ETHUSDT"]

TIMEFRAMES = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h"
}

# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data)
    except:
        pass

# =========================
# DATA BINANCE
# =========================
def obtener_datos(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    data = requests.get(url).json()

    closes = [float(c[4]) for c in data]
    highs = [float(c[2]) for c in data]
    lows = [float(c[3]) for c in data]
    volumes = [float(c[5]) for c in data]

    return closes, highs, lows, volumes

# =========================
# VWAP REAL
# =========================
def calcular_vwap(highs, lows, closes, volumes):
    vwap = []
    cumulative_pv = 0
    cumulative_vol = 0

    for i in range(len(closes)):
        typical_price = (highs[i] + lows[i] + closes[i]) / 3
        pv = typical_price * volumes[i]

        cumulative_pv += pv
        cumulative_vol += volumes[i]

        vwap.append(cumulative_pv / cumulative_vol)

    return vwap

# =========================
# DETECTOR DE SEÑAL
# =========================
def detectar_senal(symbol, tf):

    closes, highs, lows, volumes = obtener_datos(symbol, tf)
    vwap = calcular_vwap(highs, lows, closes, volumes)

    if len(closes) < 2:
        return None

    c = closes[-1]
    c_prev = closes[-2]

    v = vwap[-1]
    v_prev = vwap[-2]

    # =========================
    # CONDICIONES
    # =========================
    cond1_long = c > v
    cond2_long = c > c_prev
    cond3_long = v > v_prev

    cond1_short = c < v
    cond2_short = c < c_prev
    cond3_short = v < v_prev

    score_long = sum([cond1_long, cond2_long, cond3_long])
    score_short = sum([cond1_short, cond2_short, cond3_short])

    # =========================
    # CRUCE
    # =========================
    cruce_long = c_prev < v_prev and c > v
    cruce_short = c_prev > v_prev and c < v

    # =========================
    # REGLAS SEGÚN TF
    # =========================
    if tf == "5m":
        min_score = 2
    else:
        min_score = 3

    # =========================
    # SEÑALES
    # =========================
    if score_long >= min_score and cruce_long:
        return "LONG", score_long

    if score_short >= min_score and cruce_short:
        return "SHORT", score_short

    return None

# =========================
# LOOP PRINCIPAL
# =========================
print("🚀 ORION RADAR INICIADO")

while True:
    try:
        for symbol in SYMBOLS:
            for tf in TIMEFRAMES:

                resultado = detectar_senal(symbol, tf)

                if resultado:
                    tipo, score = resultado

                    mensaje = f"""
🚨 SEÑAL ORION

📊 {symbol}
⏱ TF: {tf}
📈 Tipo: {tipo}
🔥 Score: {score}

🧠 Basado en VWAP + Momentum + Tendencia
"""

                    print(mensaje)
                    enviar_telegram(mensaje)

        time.sleep(60)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(60)
