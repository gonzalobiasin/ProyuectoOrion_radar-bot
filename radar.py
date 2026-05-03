import requests
import time
import os
from datetime import datetime

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

enviar_telegram("🚀 ORION DEBUG ACTIVO")

timeframes = ["5m", "15m", "1h"]

def obtener_top_crypto():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    data = requests.get(url).json()
    data = [x for x in data if x["symbol"].endswith("USDT")]
    data = sorted(data, key=lambda x: float(x["quoteVolume"]), reverse=True)
    return [x["symbol"] for x in data[:10]]  # SOLO 10 PARA DEBUG

forex = ["EURUSDT", "GBPUSDT"]

def obtener_datos(symbol, tf):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=50"
    return requests.get(url).json()

def calcular_vwap(data):
    pv = 0
    vol = 0
    vwap_list = []

    for d in data:
        h, l, c, v = float(d[2]), float(d[3]), float(d[4]), float(d[5])
        tp = (h + l + c) / 3
        pv += tp * v
        vol += v
        vwap_list.append(pv / vol if vol != 0 else 0)

    return vwap_list

def evaluar(symbol, tf):
    data = obtener_datos(symbol, tf)

    # 🔴 VALIDACIÓN CRÍTICA
    if not isinstance(data, list) or len(data) < 3:
        print(f"⚠️ SIN DATOS: {symbol} {tf}")
        return None

    closes = [float(x[4]) for x in data]
    vwap = calcular_vwap(data)

    c = closes[-1]
    c_prev = closes[-2]

    v = vwap[-1]
    v_prev = vwap[-2]

    score_long = sum([c > v, c > c_prev, v > v_prev])
    score_short = sum([c < v, c < c_prev, v < v_prev])

    cross_up = c > v and (c_prev < v_prev or abs(c - v) / v < 0.005)
    cross_down = c < v and (c_prev > v_prev or abs(c - v) / v < 0.005)

    # 🔥 DEBUG REAL
    print(f"{symbol} {tf} | price={c:.2f} vwap={v:.2f} scoreL={score_long} scoreS={score_short}")

    if tf == "5m":
        if score_long >= 2 and cross_up:
            print("➡️ LONG DETECTADO")
            return "LONG"
        if score_short >= 2 and cross_down:
            print("➡️ SHORT DETECTADO")
            return "SHORT"
    else:
        if score_long >= 3 and cross_up:
            print("➡️ LONG DETECTADO")
            return "LONG"
        if score_short >= 3 and cross_down:
            print("➡️ SHORT DETECTADO")
            return "SHORT"

    return None

while True:
    print("🔄 ESCANEANDO...")

    try:
        activos = obtener_top_crypto() + forex

        for s in activos:
            for tf in timeframes:

                sig = evaluar(s, tf)

                if sig:
                    msg = f"""
🚨 SEÑAL DEBUG

{s} | {tf}
{sig}
{datetime.now().strftime("%H:%M:%S")}
"""
                    enviar_telegram(msg)

    except Exception as e:
        print("ERROR:", e)

    time.sleep(20)
