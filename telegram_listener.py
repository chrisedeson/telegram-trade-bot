import sys
import os
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events
from collections import defaultdict

# -------------------------------
# Load the correct .env file
# -------------------------------
env_file = sys.argv[1] if len(sys.argv) > 1 else ".env"
os.environ["ENV_FILE"] = env_file
load_dotenv(dotenv_path=env_file)

print("🔍 Using env file:", env_file)
print("🧪 TELEGRAM_SESSION_NAME:", os.getenv("TELEGRAM_SESSION_NAME"))

# -------------------------------
# Only import now that env is loaded
# -------------------------------
from parser import parse_signal
from trading_bot import send_to_broker, update_trade

# -------------------------------
# Environment Variables
# -------------------------------
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
chat_id = int(os.getenv("TELEGRAM_CHAT"))
session_name = os.getenv("TELEGRAM_SESSION_NAME", "session_default")

# -------------------------------
# Setup Telegram client
# -------------------------------
client = TelegramClient(session_name, api_id, api_hash)
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
processed_signals = defaultdict(dict)

# -------------------------------
# Signal Handling
# -------------------------------
async def handle_signal(event, is_edit=False):
    msg = event.message.message
    msg_id = event.message.id
    logger.info(f"{'✏️ Edited' if is_edit else '📩 New'} message: {msg}")

    signal = parse_signal(msg)
    if not signal:
        logger.warning("❌ Could not parse signal.")
        return

    logger.info(f"✅ Parsed: {signal}")
    previous = processed_signals.get(msg_id)

    if not previous:
        logger.info("🟢 New trade signal.")
        send_to_broker(signal, message_id=msg_id)
        processed_signals[msg_id] = signal
    elif signal != previous:
        logger.info("🔁 Updating modified trade.")
        update_trade(msg_id, signal)
        processed_signals[msg_id] = signal
    else:
        logger.info("⏸️ No changes to signal.")

# -------------------------------
# Telegram event bindings
# -------------------------------
@client.on(events.NewMessage(chats=chat_id))
async def new_handler(event):
    await handle_signal(event, is_edit=False)

@client.on(events.MessageEdited(chats=chat_id))
async def edit_handler(event):
    await handle_signal(event, is_edit=True)

# -------------------------------
# Run the client
# -------------------------------
with client:
    client.loop.run_until_complete(client.get_entity(chat_id))
    logger.info("🚀 Bot running...")
    client.run_until_disconnected()
