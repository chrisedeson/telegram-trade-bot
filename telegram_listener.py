from dotenv import load_dotenv
import os
from telethon import TelegramClient, events
from parser import parse_signal
import logging
from trading_bot import send_to_broker

# 🔒 Load environment variables from .env
load_dotenv()

# 📲 Fetch your Telegram credentials
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
chat = os.getenv('TELEGRAM_CHAT')

# 🧠 Initialize Telethon client (session is saved as session_name.session)
client = TelegramClient('session_name', api_id, api_hash)

# Initialize the logger
logger = logging.getLogger()

# ✅ Define your handler
@client.on(events.NewMessage(chats=chat))
async def handler(event):
    msg = event.message.message
    logger.info(f"📩 New message: {msg}")

    # Parse the trade signal
    signal = parse_signal(msg)
    if signal:
        logger.info(f"✅ Parsed signal: {signal}")
        send_to_broker(signal)
    else:
        logger.warning(f"❌ Invalid or unrecognized message: {msg}")

# ▶️ Start the client
client.start()
logger.info("Bot started and connected to Telegram.")
client.run_until_disconnected()
