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

enviar_telegram("🚀 ORION VWAP RADAR ACTIVO")

timeframes = ["5m", "15m", "1h", "4h", "8h", "12h", "1d"]

def obtener_top_crypto():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    data = requests.get(url).json()
    data = [x for x in data if x["symbol"].endswith("USDT")]
    data = sorted(data, key=lambda x: float(x["quoteVolume"]), reverse=True)
    return [x["symbol"] for x in data[:20]]

forex = ["EURUSDT", "GBPUSDT", "AUDUSDT"]

def obtener_datos(symbol, tf):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=100"
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

ultimas = {}

def permitido(key):
    ahora = time.time()
    if key in ultimas and ahora - ultimas[key] < 900:
        return False
    ultimas[key] = ahora
    return True

def evaluar(symbol, tf):
    data = obtener_datos(symbol, tf)
    if len(data) < 3:
        return None

    closes = [float(x[4]) for x in data]
    vwap = calcular_vwap(data)

    c = closes[-1]
    c_prev = closes[-2]

    v = vwap[-1]
    v_prev = vwap[-2]

    cond_long = [c > v, c > c_prev, v > v_prev]
    cond_short = [c < v, c < c_prev, v < v_prev]

    score_long = sum(cond_long)
    score_short = sum(cond_short)

    # 🔥 CRUCE MEJORADO
    cross_up = c > v and (c_prev < v_prev or abs(c - v) / v < 0.003)
    cross_down = c < v and (c_prev > v_prev or abs(c - v) / v < 0.003)

    if tf == "5m":
        if score_long >= 2 and cross_up:
            return "LONG"
        if score_short >= 2 and cross_down:
            return "SHORT"
    else:
        if score_long >= 3 and cross_up:
            return "LONG"
        if score_short >= 3 and cross_down:
            return "SHORT"

    return None

while True:
    print("escaneando...")

    try:
        activos = obtener_top_crypto() + forex

        for s in activos:
            for tf in timeframes:

                sig = evaluar(s, tf)

                if sig:
                    key = f"{s}-{tf}-{sig}"

                    if permitido(key):
                        msg = f"""
🚨 SEÑAL ORION VWAP

{s} | {tf}
{sig}
{datetime.now().strftime("%H:%M:%S")}
"""
                        print(msg)
                        enviar_telegram(msg)
                        time.sleep(1)

    except Exception as e:
        print("error:", e)

    time.sleep(30)
