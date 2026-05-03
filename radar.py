import requests
import time
import os
from datetime import datetime

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"
CHAT_ID = "6974761713"

# ============================
# TELEGRAM
# ============================

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Error Telegram:", e)

# ============================
# INICIO
# ============================

enviar_telegram("🚀 ORION RADAR PRO ACTIVO")

# ============================
# TIMEFRAMES (ACTUALIZADO)
# ============================

timeframes = ["5m", "15m", "1h", "4h", "8h", "12h", "1d"]

# ============================
# TOP 20 CRYPTO DINÁMICAS (FUTUROS)
# ============================

def obtener_top_crypto():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    data = requests.get(url).json()

    filtrado = [x for x in data if "USDT" in x["symbol"]]
    ordenado = sorted(filtrado, key=lambda x: float(x["quoteVolume"]), reverse=True)

    return [x["symbol"] for x in ordenado[:20]]

# ============================
# FOREX
# ============================

forex = ["EURUSDT", "GBPUSDT", "AUDUSDT", "JPYUSDT", "CHFUSDT"]

# ============================
# DATOS
# ============================

def obtener_datos(symbol, interval):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=50"
    return requests.get(url).json()

# ============================
# INDICADORES
# ============================

def ema(valores, periodo):
    k = 2 / (periodo + 1)
    ema_val = valores[0]
    for precio in valores:
        ema_val = precio * k + ema_val * (1 - k)
    return ema_val

def calcular_vwap(data):
    total_vol = 0
    total_price_vol = 0

    for d in data:
        high = float(d[2])
        low = float(d[3])
        close = float(d[4])
        vol = float(d[5])

        precio = (high + low + close) / 3
        total_price_vol += precio * vol
        total_vol += vol

    return total_price_vol / total_vol if total_vol != 0 else 0

# ============================
# EVALUAR
# ============================

def evaluar(symbol, tf):
    try:
        data = obtener_datos(symbol, tf)

        closes = [float(d[4]) for d in data]

        precio = closes[-1]
        ema20 = ema(closes[-20:], 20)
        ema50 = ema(closes[-50:], 50)
        vwap = calcular_vwap(data)

        # TENDENCIA
        alcista = ema20 > ema50
        bajista = ema20 < ema50

        # MOMENTUM
        momentum_up = closes[-1] > closes[-3]
        momentum_down = closes[-1] < closes[-3]

        # CRUCE (OBLIGATORIO)
        cross_up = closes[-2] < ema20 and closes[-1] > ema20
        cross_down = closes[-2] > ema20 and closes[-1] < ema20

        # VWAP BASE
        sobre_vwap = precio > vwap
        bajo_vwap = precio < vwap

        # SCORE
        score_long = 0
        score_short = 0

        if alcista:
            score_long += 1
        if momentum_up:
            score_long += 1

        if bajista:
            score_short += 1
        if momentum_down:
            score_short += 1

        # ============================
        # REGLAS
        # ============================

        # 🔥 TF 5m → 2 condiciones + cruce + VWAP
        if tf == "5m":
            if score_long >= 2 and cross_up and sobre_vwap:
                return "LONG"

            if score_short >= 2 and cross_down and bajo_vwap:
                return "SHORT"

        # 🔥 TF 15m en adelante → 3 condiciones + cruce + VWAP
        else:
            if score_long >= 2 and alcista and cross_up and sobre_vwap:
                return "LONG"

            if score_short >= 2 and bajista and cross_down and bajo_vwap:
                return "SHORT"

        return None

    except Exception as e:
        print("Error evaluar:", e)
        return None

# ============================
# ANTI SPAM
# ============================

ultimas_senales = {}

def ya_enviada(symbol, tf, señal):
    key = f"{symbol}-{tf}-{señal}"
    ahora = time.time()

    if key in ultimas_senales:
        if ahora - ultimas_senales[key] < 900:
            return True

    ultimas_senales[key] = ahora
    return False

# ============================
# LOOP PRINCIPAL
# ============================

while True:
    print("🔄 escaneando mercado...")

    try:
        cryptos = obtener_top_crypto()
        activos = cryptos + forex

        for symbol in activos:
            for tf in timeframes:

                señal = evaluar(symbol, tf)

                if señal and not ya_enviada(symbol, tf, señal):

                    mensaje = f"""
🚨 SEÑAL ORION

Activo: {symbol}
TF: {tf}
Dirección: {señal}
Hora: {datetime.now().strftime("%H:%M:%S")}
"""

                    print("Señal:", mensaje)
                    enviar_telegram(mensaje)
                    time.sleep(1)

    except Exception as e:
        print("Error general:", e)

    time.sleep(30)
