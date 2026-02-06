from pynput import mouse
from datetime import datetime
import json
import os

LOG_FILE = "clicks_log.json"

# Загружаем предыдущие данные
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {}

today = datetime.now().strftime("%Y-%m-%d")
if today not in data:
    data[today] = 0

clicks_today = data[today]

def on_click(x, y, button, pressed):
    global clicks_today
    if pressed and button == mouse.Button.left:
        clicks_today += 1
        data[today] = clicks_today
        with open(LOG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"\rКликов сегодня: {clicks_today}", end='')

# Запускаем слушателя
with mouse.Listener(on_click=on_click) as listener:
    print(f"Считаем клики мыши. Дата: {today}")
    print("Нажми Ctrl+C для остановки.")
    listener.join()