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
        requests.post(url, json={"chat_id": CANAL_ID, "text": msg})
    except:
        print("Error Telegram")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = ["5m","15m","1H","4H","8H","12H","1D"]
TF_SPOT = ["8h","12h","1d"]
TF_FOREX = ["5min"]

FOREX_PAIRS = ["EUR/USD"]

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
    principales = [
        "BTC-USDT-SWAP",
        "ETH-USDT-SWAP",
        "SOL-USDT-SWAP",
        "DOGE-USDT-SWAP"
    ]

    url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
    data = requests.get(url).json()

    if "data" not in data:
        return principales

    ordenado = sorted(data["data"], key=lambda x: float(x["volCcy24h"]), reverse=True)
    top = [x["instId"] for x in ordenado if "USDT" in x["instId"]][:20]

    return list(set(principales + top))

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
# FOREX
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
# WINRATE
# ============================

historial = []
estadisticas = {"total": 0, "wins": 0}

def guardar_senal(symbol, tf, direccion, precio):
    historial.append({
        "symbol": symbol,
        "tf": tf,
        "dir": direccion,
        "entry": precio,
        "time": time.time(),
        "checked": False
    })

def evaluar_resultados():
    for s in historial:
        if s["checked"]:
            continue

        if time.time() - s["time"] < 180:
            continue

        data = okx_data(s["symbol"], s["tf"])
        if not data:
            continue

        precio_actual = data[-1][3]

        win = False
        if s["dir"] == "LONG" and precio_actual > s["entry"]:
            win = True
        elif s["dir"] == "SHORT" and precio_actual < s["entry"]:
            win = True

        estadisticas["total"] += 1
        if win:
            estadisticas["wins"] += 1

        s["checked"] = True

def obtener_winrate():
    if estadisticas["total"] == 0:
        return "N/A"
    return round((estadisticas["wins"] / estadisticas["total"]) * 100, 2)

# ============================
# ANTI SPAM
# ============================

ultima_senal = {}

# ============================
# LÓGICA
# ============================

def evaluar(data, key, tf):
    if not data or len(data) < 6:
        return None

    closes = [x[3] for x in data]
    vwap = calcular_vwap(data)

    c, cp = closes[-1], closes[-2]
    v, vp = vwap[-1], vwap[-2]

    tendencia_alcista = vwap[-1] > vwap[-3]
    tendencia_bajista = vwap[-1] < vwap[-3]

    cond_long = [c > v, c > cp, v > vp]
    cond_short = [c < v, c < cp, v < vp]

    cross_up = c > v and vp <= v
    cross_dn = c < v and vp >= v

    señal = None

    # 🔥 SOLO MODIFICADO 5M
    if tf in ["5m","5min"]:
        movimiento_fuerte = abs(closes[-1] - closes[-3]) > (vwap[-1] * 0.001)

        if sum(cond_long) >= 2 and cross_up and tendencia_alcista and movimiento_fuerte:
            señal = "LONG"
        elif sum(cond_short) >= 2 and cross_dn and tendencia_bajista and movimiento_fuerte:
            señal = "SHORT"

    else:
        if sum(cond_long) >= 2 and cross_up and tendencia_alcista:
            señal = "LONG"
        elif sum(cond_short) >= 2 and cross_dn and tendencia_bajista:
            señal = "SHORT"

    if not señal:
        return None

    if key in ultima_senal and ultima_senal[key] == señal:
        return None

    ultima_senal[key] = señal
    return señal

# ============================
# LOOP
# ============================

while True:

    print("🔄 ESCANEANDO ORION...")

    try:

        evaluar_resultados()
        winrate = obtener_winrate()

        # CRYPTO
        for s in okx_top():
            for tf in TF_OKX:

                data = okx_data(s, tf)
                sig = evaluar(data, f"OKX-{s}-{tf}", tf)

                if sig:
                    precio = data[-1][3]
                    guardar_senal(s, tf, sig, precio)

                    limpio = s.replace("-SWAP", "")

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {limpio}-Perpetual
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # SPOT
        for s in ["BTCUSDT","ETHUSDT"]:
            for tf in TF_SPOT:

                data = binance_data(s, tf)
                sig = evaluar(data, f"SPOT-{s}-{tf}", tf)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion SPOT

Activo: {s}
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # FOREX
        for pair in FOREX_PAIRS:
            for tf in TF_FOREX:

                data = forex_data(pair, tf)
                sig = evaluar(data, f"FX-{pair}-{tf}", tf)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion Forex

Par: {pair}
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

    except Exception as e:
        print("ERROR:", e)

    time.sleep(60)
