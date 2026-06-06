import requests
import time

# ============================
# VERSION CONTROL
# ============================

VERSION = "ORION MM ALGO PREMIUM FINAL"

# ============================
# CONFIG
# ============================

TOKEN = 

CHAT_ID = "6974761713"

CANAL_ID = "-1003947013736"

TWELVE_API = "83ae049ec6cf418a9b11adaef4a55706"

# ============================
# TOP COINS
# ============================

TOP_30 = [

"BTC-USDT-SWAP",

]

# ============================
# TELEGRAM
# ============================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:

        requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg
            }
        )

        requests.post(
            url,
            json={
                "chat_id": CANAL_ID,
                "text": msg
            }
        )

    except:

        print("❌ ERROR TELEGRAM")

# ============================
# TIMEFRAMES
# ============================

TF_OKX = [

"5m",
"15m",
"1H",
"4H",
"8H",
"12H",
"1D"

]

TF_SPOT = [

"8h",
"12h",
"1d"

]

TF_FOREX = [

"5min"

]

FOREX_PAIRS = [

"EUR/USD"

]

BYBIT_FOREX = [

"XAUUSDT",
"XAGUSDT"

]

# ============================
# OKX TOP
# ============================

def okx_top():

    try:

        url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"

        data = requests.get(url).json()

        if "data" not in data:
            return []

        ordenado = sorted(
            data["data"],
            key=lambda x: float(x["volCcy24h"]),
            reverse=True
        )

        return [
            x["instId"]
            for x in ordenado
            if "USDT" in x["instId"]
        ][:20]

    except:

        return []

# ============================
# OKX DATA
# ============================

def okx_data(symbol, tf):

    try:

        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={tf}&limit=200"

        r = requests.get(url).json()

        if "data" not in r:
            return None

        return [

            [
                int(x[0]),
                float(x[1]),
                float(x[2]),
                float(x[3]),
                float(x[4]),
                float(x[5])
            ]

            for x in reversed(r["data"])
        ]

    except:

        return None

# ============================
# BINANCE
# ============================

def binance_data(symbol, tf):

    try:

        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=200"

        r = requests.get(url).json()

        if not isinstance(r, list):
            return None

        return [

            [
                int(x[0]),
                float(x[1]),
                float(x[2]),
                float(x[3]),
                float(x[4]),
                float(x[5])
            ]

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

        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=200&apikey={TWELVE_API}"

        r = requests.get(url).json()

        if "values" not in r:
            return None

        data = []

        for x in reversed(r["values"]):

            data.append([

                x["datetime"],
                float(x["open"]),
                float(x["high"]),
                float(x["low"]),
                float(x["close"]),
                float(x.get("volume", 1))

            ])

        return data

    except:

        return None

# ============================
# BYBIT FOREX
# ============================

def bybit_forex_data(symbol, tf):

    try:

        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5&limit=200"

        r = requests.get(url).json()

        if "result" not in r:
            return None

        data = []

        for x in reversed(r["result"]["list"]):

            data.append([

                int(x[0]),
                float(x[1]),
                float(x[2]),
                float(x[3]),
                float(x[4]),
                float(x[5])

            ])

        return data

    except:

        return None

# ============================
# ATR
# ============================

def calcular_atr(data, length=10):

    trs = []

    for i in range(1, len(data)):

        high = data[i][2]
        low = data[i][3]
        prev_close = data[i-1][4]

        tr = max(

            high - low,
            abs(high - prev_close),
            abs(low - prev_close)

        )

        trs.append(tr)

    if len(trs) < length:
        return None

    atrs = []

    for i in range(length, len(trs)+1):

        atrs.append(
            sum(trs[i-length:i]) / length
        )

    return atrs

# ============================
# WINRATE
# ============================

historial = []

estadisticas = {
    "total": 0,
    "wins": 0
}

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

        data = okx_data(
            s["symbol"],
            s["tf"]
        )

        if not data:
            continue

        precio_actual = data[-1][4]

        if (
            s["dir"] == "LONG"
            and precio_actual > s["entry"]
        ) or (
            s["dir"] == "SHORT"
            and precio_actual < s["entry"]
        ):

            estadisticas["wins"] += 1

        estadisticas["total"] += 1

        s["checked"] = True

def obtener_winrate():

    if estadisticas["total"] == 0:
        return "N/A"

    return round(
        (
            estadisticas["wins"]
            / estadisticas["total"]
        ) * 100,
        2
    )

# ============================
# ANTI SPAM
# ============================

ultima_senal = {}

# ============================
# MM ALGO PREMIUM
# ============================

def evaluar(data, key):

    try:

        if not data or len(data) < 50:
            return None

        closes = [x[4] for x in data]
        highs = [x[2] for x in data]
        lows = [x[3] for x in data]

        # =================================
        # SETTINGS MM ALGO PREMIUM
        # =================================

        length = 10
        mult = 10
        sfilter = 0.5

        atrs = calcular_atr(data, length)

        if not atrs:
            return None

        long_stops = []
        short_stops = []
        dirs = []

        dir_actual = 1

        for i in range(length, len(data)):

            hl2 = (highs[i] + lows[i]) / 2

            atr = atrs[i - length] * mult

            long_stop = hl2 - atr * sfilter
            short_stop = hl2 + atr * sfilter

            if len(long_stops) > 0:

                prev_long = long_stops[-1]
                prev_short = short_stops[-1]

                if closes[i-1] > prev_long:
                    long_stop = max(
                        long_stop,
                        prev_long
                    )

                if closes[i-1] < prev_short:
                    short_stop = min(
                        short_stop,
                        prev_short
                    )

                if dir_actual == -1 and closes[i] > prev_short:
                    dir_actual = 1

                elif dir_actual == 1 and closes[i] < prev_long:
                    dir_actual = -1

            long_stops.append(long_stop)
            short_stops.append(short_stop)
            dirs.append(dir_actual)

        if len(dirs) < 3:
            return None

        actual = dirs[-1]
        anterior = dirs[-2]

        señal = None

        # BUY
        if actual == 1 and anterior == -1:
            señal = "LONG"

        # SELL
        elif actual == -1 and anterior == 1:
            señal = "SHORT"

        if not señal:
            return None

        # ============================
        # ANTI SPAM
        # ============================

        if key in ultima_senal:

            if ultima_senal[key] == señal:
                return None

        ultima_senal[key] = señal

        return señal

    except Exception as e:

        print("ERROR EVALUAR:", e)

        return None

# ============================
# LOOP
# ============================

print(f"🚀 INICIANDO {VERSION}")

while True:

    print(f"🔄 ESCANEANDO... ({VERSION})")

    try:

        evaluar_resultados()

        winrate = obtener_winrate()

        symbols = list(
            set(
                TOP_30 + okx_top()
            )
        )

        # ============================
        # FUTUROS
        # ============================

        for s in symbols:

            for tf in TF_OKX:

                data = okx_data(s, tf)

                sig = evaluar(
                    data,
                    f"{s}-{tf}"
                )

                if sig:

                    precio = data[-1][4]

                    guardar_senal(
                        s,
                        tf,
                        sig,
                        precio
                    )

                    limpio = s.replace(
                        "-SWAP",
                        ""
                    )

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {limpio} - Perpetuo
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ============================
        # SPOT
        # ============================

        for s in [

            "BTCUSDT",
            "ETHUSDT"

        ]:

            for tf in TF_SPOT:

                data = binance_data(s, tf)

                sig = evaluar(
                    data,
                    f"{s}-{tf}"
                )

                if sig:

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {s} - Spot
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ============================
        # FOREX
        # ============================

        for pair in FOREX_PAIRS:

            for tf in TF_FOREX:

                data = forex_data(pair, tf)

                sig = evaluar(
                    data,
                    f"{pair}-{tf}"
                )

                if sig:

                    enviar_telegram(f"""
🚨 Proyecto Orion

Activo: {pair} - Forex
Dirección: {sig}
Temporalidad: {tf}
Winrate: {winrate}%
""")

        # ============================
        # ORO / PLATA
        # ============================

        for pair in BYBIT_FOREX:

            for tf in TF_FOREX:

                data = bybit_forex_data(pair, tf)

                sig = evaluar(
                    data,
                    f"{pair}-{tf}"
                )

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
