import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import asyncio
import datetime

# --- ENV VARIABLES ---
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

if not TOKEN:
    raise ValueError("BOT_TOKEN missing")

if not GROUP_ID:
    raise ValueError("GROUP_ID missing")

GROUP_ID = int(GROUP_ID)

# --- INIT ---
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

last_schedule = ""

# --- PARSER ---
def get_schedule():
    url = "https://dekanat.nung.edu.ua/cgi-bin/timetable.cgi"

    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()

        if "КІ-25-1" not in text:
            return None

        lines = text.split("\n")
        group_data = []

        capture = False

        for line in lines:
            if "КІ-25-1" in line:
                capture = True
            if capture:
                if line.strip() == "":
                    break
                group_data.append(line.strip())

        return "\n".join(group_data)

    except Exception as e:
        print("Parser error:", e)
        return None

# --- SEND TODAY ---
async def send_today_schedule():
    schedule = get_schedule()
    if schedule:
        today = datetime.datetime.now().strftime("%d.%m")
        await bot.send_message(GROUP_ID, f"📅 Розклад КІ-25-1 на {today}:\n\n{schedule}")

# --- CHECK CHANGES ---
async def check_changes():
    global last_schedule
    new_schedule = get_schedule()

    if new_schedule and last_schedule and new_schedule != last_schedule:
        await bot.send_message(GROUP_ID, "⚠️ У розкладі є зміни!")
        await bot.send_message(GROUP_ID, new_schedule)

    if new_schedule:
        last_schedule = new_schedule

# --- LOOP ---
async def scheduler_loop():
    await send_today_schedule()
    while True:
        await check_changes()
        await asyncio.sleep(600)

# --- STARTUP ---
async def on_startup(dp):
    asyncio.create_task(scheduler_loop())

# --- COMMAND ---
@dp.message_handler(commands=["today"])
async def today_cmd(message: types.Message):
    schedule = get_schedule()
    if schedule:
        await message.reply(f"📅 Розклад на сьогодні:\n\n{schedule}")
    else:
        await message.reply("Не вдалося отримати розклад 😢")

# --- START ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
