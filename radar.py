import requests
import time
import os

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"
CANAL_ID = "-1003947013736"

TWELVE_API = "83ae049ec6cf418a9b11adaef4a55706"

# ============================
# TELEGRAM
# ============================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Error chat")

    try:
        requests.post(url, json={"chat_id": CANAL_ID, "text": msg})
    except:
        print("Error canal")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = ["5m","15m","1H","4H","8H","12H","1D"]
TF_SPOT = ["8h","12h","1d"]
TF_FOREX = ["5min","1h"]

# ============================
# FOREX
# ============================

FOREX_PAIRS = ["EUR/USD","GBP/USD"]

# ============================
# VWAP
# ============================

def calcular_vwap(data):
    pv, vol = 0, 0
    vwap_list = []

    for _,h,l,c,v in data:
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
        [int(x[0]), float(x[2]), float(x[3]), float(x[4]), float(x[5])]
        for x in reversed(r["data"])
    ]

# ============================
# BINANCE
# ============================

def binance_data(symbol, tf):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"
    r = requests.get(url).json()

    if not isinstance(r, list):
        return None

    return [
        [int(x[0]), float(x[2]), float(x[3]), float(x[4]), float(x[5])]
        for x in r
    ]

# ============================
# FOREX DATA
# ============================

def forex_data(pair, tf):
    if not TWELVE_API:
        return None

    symbol = pair.replace("/", "")

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=50&apikey={TWELVE_API}"

    r = requests.get(url).json()

    if "values" not in r:
        return None

    data = []

    for x in reversed(r["values"]):
        t = x["datetime"]
        h = float(x["high"])
        l = float(x["low"])
        c = float(x["close"])
        v = float(x.get("volume", 1))

        data.append([t,h,l,c,v])

    return data

# ============================
# ANTI-SPAM CORRECTO
# ============================

ultima_senal = {}

# ============================
# LÓGICA
# ============================

def evaluar(data, key, tf):
    if not data or len(data) < 3:
        return None

    closes = [x[3] for x in data]
    vwap = calcular_vwap(data)

    c, cp = closes[-1], closes[-2]
    v, vp = vwap[-1], vwap[-2]

    cond_long = [c > v, c > cp, v > vp]
    cond_short = [c < v, c < cp, v < vp]

    cross_up = cp < vp and c > v
    cross_dn = cp > vp and c < v

    señal = None

    if tf in ["5m","5min"]:
        if sum(cond_long) >= 2 and cross_up:
            señal = "LONG"
        elif sum(cond_short) >= 2 and cross_dn:
            señal = "SHORT"
    else:
        if sum(cond_long) >= 2 and cross_up:
            señal = "LONG"
        elif sum(cond_short) >= 2 and cross_dn:
            señal = "SHORT"

    if not señal:
        return None

    # 🔥 SOLO BLOQUEA SI REPITE MISMA DIRECCIÓN
    if key in ultima_senal and ultima_senal[key] == señal:
        return None

    ultima_senal[key] = señal

    return señal

# ============================
# LIMPIAR TEXTO
# ============================

def limpiar_activo(symbol):
    return symbol.replace("-SWAP", "")

# ============================
# LOOP
# ============================

while True:

    print("🔄 ESCANEANDO ORION...")

    try:

        # CRYPTO
        for s in okx_top():
            for tf in TF_OKX:

                sig = evaluar(okx_data(s, tf), f"OKX-{s}-{tf}", tf)

                if sig:
                    limpio = limpiar_activo(s)

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {limpio}-Perpetual
Dirección: {sig}
Temporalidad: {tf}
""")

        # SPOT
        for s in ["BTCUSDT","ETHUSDT"]:
            for tf in TF_SPOT:

                sig = evaluar(binance_data(s, tf), f"SPOT-{s}-{tf}", tf)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion SPOT

Activo: {s}
Dirección: {sig}
Temporalidad: {tf}
""")

        # FOREX
        for pair in FOREX_PAIRS:
            for tf in TF_FOREX:

                sig = evaluar(forex_data(pair, tf), f"FX-{pair}-{tf}", tf)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion Forex

Par: {pair}
Dirección: {sig}
Temporalidad: {tf}
""")

    except Exception as e:
        print("ERROR:", e)

    time.sleep(60)
