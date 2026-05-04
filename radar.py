import requests
import time
import os

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"

CHAT_ID = "6974761713"
GRUPO_ID = "-1003900599071"

# ============================
# TELEGRAM (DOBLE ENVÍO)
# ============================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    # 👉 envío a vos
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Error enviando a chat")

    # 👉 envío al grupo
    try:
        requests.post(url, data={"chat_id": GRUPO_ID, "text": msg})
    except:
        print("Error enviando a grupo")

# mensaje inicial
enviar_telegram("🚀 ORION MULTI ACTIVO")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = ["5m","15m","1H","4H","8H","12H","1D"]
TF_SPOT = ["8h","12h","1d"]

# ============================
# VWAP
# ============================

def calcular_vwap(data):
    pv = 0
    vol = 0
    vwap_list = []

    for h,l,c,v in data:
        tp = (h + l + c) / 3
        pv += tp * v
        vol += v
        vwap_list.append(pv / vol if vol != 0 else 0)

    return vwap_list

# ============================
# OKX PERPETUOS
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
# LÓGICA TRADING
# ============================

def evaluar(data, key, tf):
    if not data or len(data) < 3:
        return None

    if key in ultima_vela:
        return None

    ultima_vela[key] = True

    closes = [x[2] for x in data]
    vwap = calcular_vwap(data)

    c = closes[-1]
    cp = closes[-2]

    v = vwap[-1]
    vp = vwap[-2]

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
# LOOP
# ============================

while True:

    print("🔄 ESCANEANDO...")

    try:
        # OKX
        for s in okx_top():
            for tf in TF_OKX:

                sig = evaluar(okx_data(s, tf), f"OKX-{s}-{tf}", tf)

                if sig:
                    enviar_telegram(f"""
🚨 Señal Proyecto Orion

Activo: {s}-Perpetual
Temporalidad: {tf}
Dirección: {sig}
""")

        # BINANCE SPOT
        for s in ["BTCUSDT", "ETHUSDT"]:
            for tf in TF_SPOT:

                sig = evaluar(binance_data(s, tf), f"SPOT-{s}-{tf}", "X")

                if sig:
                    enviar_telegram(f"""
🚨 Señal Proyecto Orion

Activo: {s}-SPOT
Temporalidad: {tf}
Dirección: {sig}
""")

    except Exception as e:
        print("ERROR:", e)

    time.sleep(60)
