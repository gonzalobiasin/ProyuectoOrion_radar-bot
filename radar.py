import requests
import time
import json
import os

# ==============================
# 🔐 TELEGRAM
# ==============================
TOKEN = "TU_TOKEN"
CHAT_IDS = ["TU_ID", "TU_CANAL"]

def send_telegram(msg):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
        except:
            pass

# ==============================
# 📁 HISTORIAL
# ==============================
FILE = "historial.json"

if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump([], f)

def load_history():
    with open(FILE, "r") as f:
        return json.load(f)

def save_history(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

# ==============================
# 🧠 WINRATE
# ==============================
def winrate(symbol, direction):
    h = load_history()
    trades = [t for t in h if t["symbol"] == symbol and t["dir"] == direction and t["res"] != "PENDING"]

    if not trades:
        return 0

    wins = sum(1 for t in trades if t["res"] == "WIN")
    return round((wins / len(trades)) * 100, 2)

# ==============================
# 🔄 UPDATE TRADES
# ==============================
def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        return float(requests.get(url).json()["price"])
    except:
        return None

def update_trades():
    h = load_history()

    for t in h:
        if t["res"] != "PENDING":
            continue

        price = get_price(t["symbol"])
        if price is None:
            continue

        if t["dir"] == "LONG":
            if price >= t["tp"]:
                t["res"] = "WIN"
            elif price <= t["sl"]:
                t["res"] = "LOSS"

        if t["dir"] == "SHORT":
            if price <= t["tp"]:
                t["res"] = "WIN"
            elif price >= t["sl"]:
                t["res"] = "LOSS"

    save_history(h)

# ==============================
# 📊 TOP 20 CRYPTO DINÁMICO
# ==============================
def get_top_crypto():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url).json()

        usdt = [x for x in data if "USDT" in x["symbol"]]
        sorted_pairs = sorted(usdt, key=lambda x: abs(float(x["priceChangePercent"])), reverse=True)

        return [x["symbol"] for x in sorted_pairs[:20]]
    except:
        return ["BTCUSDT"]

# ==============================
# 📊 DATA
# ==============================
def get_klines_binance(symbol, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=200"
        return requests.get(url).json()
    except:
        return []

def get_klines_yahoo(symbol, interval="5m"):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval={interval}"
        r = requests.get(url)

        data = r.json()["chart"]["result"][0]["indicators"]["quote"][0]

        closes = data["close"]
        highs = data["high"]
        lows = data["low"]
        volumes = data["volume"]

        result = []
        for i in range(len(closes)):
            if closes[i] is not None:
                result.append([highs[i], lows[i], closes[i], volumes[i]])

        return result
    except:
        return []

# ==============================
# 🧠 VWAP
# ==============================
def vwap(data, binance=True):
    pv, vol = 0, 0
    values = []

    for c in data:
        if binance:
            h, l, cl, v = float(c[2]), float(c[3]), float(c[4]), float(c[5])
        else:
            h, l, cl, v = c

        if v is None or v == 0:
            values.append(0)
            continue

        t = (h + l + cl) / 3
        pv += t * v
        vol += v
        values.append(pv / vol if vol else 0)

    return values

# ==============================
# 🚀 CONFIG
# ==============================
forex = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X"
]

commodities = [
    "XAUUSD=X","XAGUSD=X","CL=F"
]

timeframes = {
    "5m":"5m",
    "15m":"15m",
    "1h":"1h",
    "2h":"2h",
    "4h":"4h"
}

print("🚀 RADAR DINÁMICO + WINRATE\n")
send_telegram("✅ BOT ACTIVO")

# ==============================
# 🔁 LOOP
# ==============================
while True:

    update_trades()
    crypto = get_top_crypto()

    print("TOP CRYPTO:", crypto)

    def evaluate(symbol, tf_name, closes, vw):
        price = closes[-1]
        prev_price = closes[-2]

        vwap_now = vw[-1]
        vwap_prev = vw[-2]

        scoreLong = (price > vwap_now) + (price > prev_price) + (vwap_now > vwap_prev)
        scoreShort = (price < vwap_now) + (price < prev_price) + (vwap_now < vwap_prev)

        crossover = prev_price < vwap_prev and price > vwap_now
        crossunder = prev_price > vwap_prev and price < vwap_now

        # DEBUG
        print(f"{symbol} {tf_name} | L:{scoreLong} S:{scoreShort} | cross:{crossover}/{crossunder}")

        if tf_name == "5m":
            longSignal = scoreLong >= 2 and crossover
            shortSignal = scoreShort >= 2 and crossunder
        else:
            longSignal = scoreLong == 3 and crossover
            shortSignal = scoreShort == 3 and crossunder

        return longSignal, shortSignal

    # ===== CRYPTO =====
    for s in crypto:
        for tf_name, tf in timeframes.items():

            data = get_klines_binance(s, tf)
            if not data:
                continue

            closes = [float(c[4]) for c in data]
            vw = vwap(data, True)

            if len(closes) < 3:
                continue

            longSignal, shortSignal = evaluate(s, tf_name, closes, vw)

            if longSignal or shortSignal:
                direction = "LONG" if longSignal else "SHORT"
                wr = winrate(s, direction)

                msg = f"""🚨 CRYPTO
{s} | {tf_name}
{direction}
Winrate: {wr}%"""

                send_telegram(msg)

                h = load_history()
                price = closes[-1]

                h.append({
                    "symbol": s,
                    "dir": direction,
                    "entry": price,
                    "tp": price * 1.02 if direction == "LONG" else price * 0.98,
                    "sl": price * 0.99 if direction == "LONG" else price * 1.01,
                    "res": "PENDING"
                })

                save_history(h)

    time.sleep(60)