from dotenv import load_dotenv
import os
from telethon import TelegramClient, events
from parser import parse_signal

# 🔒 Load environment variables from .env
load_dotenv()

# 📲 Fetch your Telegram credentials
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
chat = os.getenv('TELEGRAM_CHAT')

# 🧠 Initialize Telethon client (session is saved as session_name.session)
client = TelegramClient('session_name', api_id, api_hash)

# ✅ Define your handler
@client.on(events.NewMessage(chats=chat))
async def handler(event):
    msg = event.message.message
    print("📩 New message:", msg)

    signal = parse_signal(msg)
    if signal:
        print("✅ Parsed signal:", signal)
        # 🚧 Placeholder: send_to_broker needs to be defined
        # send_to_broker(signal)  # <-- Uncomment once implemented

# ▶️ Start the client
client.start()
client.run_until_disconnected()
