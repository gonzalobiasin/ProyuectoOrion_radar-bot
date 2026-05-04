import requests
import time
import os

# ============================
# CONFIG
# ============================

TOKEN = "8515428568:AAEkRcVKkdePqrtRrZITC60Nc7ExYu7BU7g"

CHAT_ID = "6974761713"
CANAL_ID = "-1003947013736"

# ============================
# TELEGRAM (ENVÍO SEGURO)
# ============================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        r1 = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("CHAT:", r1.json())
    except Exception as e:
        print("Error chat:", e)

    try:
        r2 = requests.post(url, json={
            "chat_id": CANAL_ID,
            "text": msg
        })
        print("CANAL:", r2.json())
    except Exception as e:
        print("Error canal:", e)

# 🔥 TEST
enviar_telegram("🔥 TEST DEFINITIVO CANAL")

# ============================
# LOOP SIMPLE (para probar)
# ============================

while True:
    print("BOT ACTIVO...")
    time.sleep(60)
