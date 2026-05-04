import requests
import time
import os

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"

CHAT_ID = "6974761713"
CANAL_ID = "-1003900599071"

# ============================
# TELEGRAM (DOBLE ENVÍO + DEBUG)
# ============================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        r1 = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("CHAT:", r1.text)
    except Exception as e:
        print("Error chat:", e)

    try:
        r2 = requests.post(url, data={"chat_id": CANAL_ID, "text": msg})
        print("CANAL:", r2.text)
    except Exception as e:
        print("Error canal:", e)

# 🔥 TEST
enviar_telegram("🔥 TEST FINAL CANAL")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = ["5m","15m","1H","4H","8H","12H","1D"]
TF_SPOT = ["8h","12h","1d"]

# ============================
# VWAP
# ============================

def calcular_vwap(data):
    pv, vol = 0, 0
    vwap_list = []

    for h,l,c,v in data:
        tp = (h + l + c) / 3
        pv += tp * v
        vol += v
        vwap_list.append(pv / vol if vol else 0)

    return vwap_list

# ============================
# OKX
# ============================

def okx_top():
    url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
    data = requests.get(url).json()

    if "data" not in data:
        return []

    ordenado = sorted(data["data"], key=lambda x: float(x["volCcy24h"]), reverse=True)

    return [x["instId"] for x in ordenado if "USDT" in x["instId"]][:20]

def okx_data(symbol, tf):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={tf}&limit=50"
    r = requests.get(url).json()

    if "data" not in r:
        return None

    return [
        [float(x[2]), float(x[3]), float(x[4]), float(x[5])]
        for x in reversed(r["data"])
    ]

# ============================
# BINANCE SPOT
# ============================

def binance_data(symbol, tf):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"
    r = requests.get(url).json()

    if not isinstance(r, list):
        return None

    return [
        [float(x[2]), float(x[3]), float(x[4]), float(x[5])]
        for x in r
    ]

# ============================
# ANTI SPAM
# ============================

ultima_vela = {}

# ============================
# LÓGICA
# ============================

def evaluar(data, key, tf):
    if not data or len(data) < 3:
        return None

    if key in ultima_vela:
        return None

    ultima_vela[key] = True

    closes = [x[2] for x in data]
    vwap = calcular_vwap(data)

    c, cp = closes[-1], closes[-2]
    v, vp = vwap[-1], vwap[-2]

    cond_long = [c > v, c > cp, v > vp]
    cond_short = [c < v, c < cp, v < vp]

    cross_up = cp < vp and c > v
    cross_dn = cp > vp and c < v

    if tf == "5m":
        if sum(cond_long) >= 2 and cross_up:
            return "LONG"
        if sum(cond_short) >= 2 and cross_dn:
            return "SHORT"
    else:
        if sum(cond_long) >= 3 and cross_up:
            return "LONG"
        if sum(cond_short) >= 3 and cross_dn:
            return "SHORT"

    return None

# ============================
# LIMPIAR TEXTO
# ============================

def limpiar_activo(symbol):
    return symbol.replace("-SWAP", "")

# ============================
# LOOP
# ============================

while True:

    print("🔄 ESCANEANDO...")

    try:
        # OKX
        for s in okx_top():
            for tf in TF_OKX:

                sig = evaluar(okx_data(s, tf), f"{s}-{tf}", tf)

                if sig:
                    limpio = limpiar_activo(s)

                    enviar_telegram(f"""
🚨 Señal Proyecto Orion

Activo: {limpio}-Perpetual
Temporalidad: {tf}
Dirección: {sig}
""")

        # BINANCE SPOT
        for s in ["BTCUSDT", "ETHUSDT"]:
            for tf in TF_SPOT:

                sig = evaluar(binance_data(s, tf), f"{s}-{tf}", "X")

                if sig:
                    enviar_telegram(f"""
🚨 Señal Proyecto Orion

Activo: {s}-SPOT
Temporalidad: {tf}
Dirección: {sig}
""")

    except Exception as e:
        print("ERROR GENERAL:", e)

    time.sleep(60)
