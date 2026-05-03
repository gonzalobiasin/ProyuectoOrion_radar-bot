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
    except Exception as e:
        print("Error Telegram:", e)

enviar_telegram("🚀 ORION VWAP OKX ACTIVO")

# TIMEFRAMES OKX
timeframes = ["5m", "15m", "1H", "4H", "8H", "12H", "1D"]

# ============================
# TOP CRYPTO OKX (PERPETUOS)
# ============================

def obtener_top_crypto():
    url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
    data = requests.get(url).json()

    if "data" not in data:
        print("Error OKX:", data)
        return []

    ordenado = sorted(data["data"], key=lambda x: float(x["volCcy24h"]), reverse=True)

    symbols = []
    for x in ordenado:
        if "USDT" in x["instId"]:
            symbols.append(x["instId"])

    return symbols[:20]

# ============================
# DATOS
# ============================

def obtener_datos(symbol, tf):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={tf}&limit=100"
    data = requests.get(url).json()

    if "data" not in data:
        print("ERROR OKX:", data)
        return None

    return data["data"]

# ============================
# VWAP
# ============================

def calcular_vwap(data):
    pv = 0
    vol = 0
    vwap_list = []

    for d in reversed(data):
        h = float(d[2])
        l = float(d[3])
        c = float(d[4])
        v = float(d[5])

        tp = (h + l + c) / 3
        pv += tp * v
        vol += v

        vwap_list.append(pv / vol if vol != 0 else 0)

    return vwap_list

# ============================
# CONTROL DE VELA (ANTI SPAM REAL)
# ============================

ultima_vela = {}

# ============================
# LÓGICA EXACTA TRADINGVIEW
# ============================

def evaluar(symbol, tf):
    data = obtener_datos(symbol, tf)

    if data is None or len(data) < 3:
        return None

    data = list(reversed(data))

    timestamp = data[-1][0]
    key_vela = f"{symbol}-{tf}"

    if key_vela in ultima_vela and ultima_vela[key_vela] == timestamp:
        return None

    ultima_vela[key_vela] = timestamp

    closes = [float(x[4]) for x in data]
    vwap = calcular_vwap(data)

    c = closes[-1]
    c_prev = closes[-2]

    v = vwap[-1]
    v_prev = vwap[-2]

    # CONDICIONES EXACTAS
    cond_long = [
        c > v,
        c > c_prev,
        v > v_prev
    ]

    cond_short = [
        c < v,
        c < c_prev,
        v < v_prev
    ]

    score_long = sum(cond_long)
    score_short = sum(cond_short)

    # CRUCE REAL (SIN FLEXIBILIDAD)
    cross_up = c_prev < v_prev and c > v
    cross_down = c_prev > v_prev and c < v

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

# ============================
# LOOP
# ============================

while True:
    print("🔄 ESCANEANDO OKX...")

    try:
        activos = obtener_top_crypto()

        for s in activos:
            for tf in timeframes:

                sig = evaluar(s, tf)

                if sig:
                    msg = f"""
🚨 ORION VWAP

{s}
TF: {tf}
{sig}
{datetime.now().strftime("%H:%M:%S")}
"""
                    print(msg)
                    enviar_telegram(msg)
                    time.sleep(1)

    except Exception as e:
        print("ERROR GENERAL:", e)

    time.sleep(30)
