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
chat_id = int(os.getenv('TELEGRAM_CHAT'))  # Make sure this is -100... format

# 🧠 Initialize Telethon client
client = TelegramClient('session_name', api_id, api_hash)

# Initialize the logger
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

async def main():
    # ✅ Resolve the chat ID to a proper entity
    chat_entity = await client.get_entity(chat_id)

    # ✅ Register event using resolved chat entity
    @client.on(events.NewMessage(chats=chat_entity))
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

    logger.info("Bot started and connected to Telegram.")
    await client.run_until_disconnected()

# ▶️ Start client and run async main
with client:
    client.loop.run_until_complete(main())
