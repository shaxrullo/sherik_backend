"""
Render Keep-Alive Pinger
Har 8 daqiqada frontend va backendga so'rov yuborib,
Render Free tier containerlari uxlab qolishining (spin down) oldini oladi.
Natijada foydalanuvchilar "Application Loading..." ekranini ko'rmaydi.
"""
import time
import requests
from datetime import datetime

URLS = [
    "https://sherik-frontend.onrender.com",
    "https://sherik-backend.onrender.com/api/v1/listings/",
]

def ping_servers():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for url in URLS:
        try:
            r = requests.get(url, timeout=15)
            print(f"[{now}] PING OK: {url} -> {r.status_code}")
        except Exception as e:
            print(f"[{now}] PING ERROR: {url} -> {e}")

if __name__ == "__main__":
    print("🚀 Keep-Alive Pinger ishga tushdi (Har 8 daqiqada)...")
    while True:
        ping_servers()
        time.sleep(480) # 8 daqiqa (Render 15 daqiqada uxlaydi)

