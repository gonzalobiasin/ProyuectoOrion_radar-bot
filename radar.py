import requests
import time

# ============================
# VERSION CONTROL
# ============================
VERSION = "ORION FINAL V3 (FORMATO CORREGIDO)"

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"
CANAL_ID = "-1003947013736"
TWELVE_API = "83ae049ec6cf418a9b11adaef4a55706"

# ============================
# TOP 30
# ============================

TOP_30 = [
"BTC-USDT-SWAP","ETH-USDT-SWAP","SOL-USDT-SWAP","BNB-USDT-SWAP","XRP-USDT-SWAP",
"TON-USDT-SWAP","DOGE-USDT-SWAP","ADA-USDT-SWAP","AVAX-USDT-SWAP","TRX-USDT-SWAP",
"LINK-USDT-SWAP","DOT-USDT-SWAP","MATIC-USDT-SWAP","LTC-USDT-SWAP","BCH-USDT-SWAP",
"UNI-USDT-SWAP","NEAR-USDT-SWAP","ICP-USDT-SWAP","XLM-USDT-SWAP","FIL-USDT-SWAP",
"ARB-USDT-SWAP","OP-USDT-SWAP","RNDR-USDT-SWAP","INJ-USDT-SWAP","APT-USDT-SWAP",
"SUI-USDT-SWAP","TIA-USDT-SWAP","KAS-USDT-SWAP","SEI-USDT-SWAP","STX-USDT-SWAP"
]

# ============================
# TELEGRAM
# ============================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
        requests.post(url, json={"chat_id": CANAL_ID, "text": msg})
    except:
        print("❌ Error Telegram")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = ["5m","15m","1H","4H","8H","12H","1D"]
TF_SPOT = ["8h","12h","1d"]
TF_FOREX = ["5min"]

FOREX_PAIRS = ["EUR/USD"]
BYBIT_FOREX = ["XAUUSDT","XAGUSDT"]

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
    try:
        url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
        data = requests.get(url).json()

        if "data" not in data:
            return []

        ordenado = sorted(data["data"], key=lambda x: float(x["volCcy24h"]), reverse=True)
        return [x["instId"] for x in ordenado if "USDT" in x["instId"]][:20]

    except:
        return []

def okx_data(symbol, tf):
    try:
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={tf}&limit=50"
        r = requests.get(url).json()
        if "data" not in r:
            return None

        return [
            [int(x[0]), float(x[2]), float(x[3]), float(x[4]), float(x[5])]
            for x in reversed(r["data"])
        ]
    except:
        return None

# ============================
# BINANCE
# ============================

def binance_data(symbol, tf):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"
        r = requests.get(url).json()

        if not isinstance(r, list):
            return None

        return [
            [int(x[0]), float(x[2]), float(x[3]), float(x[4]), float(x[5])]
            for x in r
        ]
    except:
        return None

# ============================
# FOREX
# ============================

def forex_data(pair, tf):
    try:
        symbol = pair.replace("/", "")
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=50&apikey={TWELVE_API}"
        r = requests.get(url).json()

        if "values" not in r:
            return None

        data = []
        for x in reversed(r["values"]):
            data.append([x["datetime"], float(x["high"]), float(x["low"]), float(x["close"]), float(x.get("volume", 1))])
        return data
    except:
        return None

# ============================
# BYBIT FOREX
# ============================

def bybit_forex_data(symbol, tf):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5&limit=50"
        r = requests.get(url).json()

        if "result" not in r:
            return None

        data = []
        for x in reversed(r["result"]["list"]):
            data.append([int(x[0]), float(x[2]), float(x[3]), float(x[4]), float(x[5])])
        return data
    except:
        return None

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

        if (s["dir"] == "LONG" and precio_actual > s["entry"]) or \
           (s["dir"] == "SHORT" and precio_actual < s["entry"]):
            estadisticas["wins"] += 1

        estadisticas["total"] += 1
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

def evaluar(data, key, es_top=False):
    if not data or len(data) < 6:
        return None

    closes = [x[3] for x in data]
    vwap = calcular_vwap(data)

    c = closes[-1]
    cp = closes[-2]
    v = vwap[-1]
    vp = vwap[-2]
    vpp = vwap[-3]

    trendUp = v > vpp
    trendDown = v < vpp

    scoreLong = (c > v) + (c > cp) + trendUp
    scoreShort = (c < v) + (c < cp) + trendDown

    crossUp = c > v and cp <= vp
    crossDown = c < v and cp >= vp

    señal = None

    if scoreLong == 3 and crossUp:
        señal = "LONG"
    elif scoreShort == 3 and crossDown:
        señal = "SHORT"

    if not señal and es_top:
        if scoreLong >= 2 and trendUp:
            señal = "LONG"
        elif scoreShort >= 2 and trendDown:
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

print(f"🚀 INICIANDO {VERSION}")

while True:

    print(f"🔄 ESCANEANDO... ({VERSION})")

    try:
        evaluar_resultados()
        winrate = obtener_winrate()

        symbols = list(set(TOP_30 + okx_top()))

        # ===== FUTUROS =====
        for s in symbols:
            es_top = s in TOP_30

            for tf in TF_OKX:
                data = okx_data(s, tf)
                sig = evaluar(data, f"{s}-{tf}", es_top)

                if sig:
                    precio = data[-1][3]
                    guardar_senal(s, tf, sig, precio)

                    limpio = s.replace("-SWAP", "")

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {limpio} - Perpetuo
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ===== SPOT =====
        for s in ["BTCUSDT","ETHUSDT"]:
            for tf in TF_SPOT:
                data = binance_data(s, tf)
                sig = evaluar(data, f"{s}-{tf}", True)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {s} - Spot
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ===== FOREX =====
        for pair in FOREX_PAIRS:
            for tf in TF_FOREX:
                data = forex_data(pair, tf)
                sig = evaluar(data, f"{pair}-{tf}", True)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {pair} - Forex
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ===== FOREX BYBIT =====
        for pair in BYBIT_FOREX:
            for tf in TF_FOREX:
                data = bybit_forex_data(pair, tf)
                sig = evaluar(data, f"{pair}-{tf}", True)

                if sig:
                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {pair} - Forex
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(60)
