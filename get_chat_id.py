from dotenv import load_dotenv
import os
from telethon import TelegramClient

# Load your credentials
load_dotenv()
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('session_name', api_id, api_hash)

async def main():
    dialogs = await client.get_dialogs()

    for dialog in dialogs:
        print(f"Name: {dialog.name}")
        print(f"    ID: {dialog.id}")
        print(f"    Username: {dialog.entity.username}")
        print(f"    Access Hash: {dialog.entity.access_hash}")
        print("")

with client:
    client.loop.run_until_complete(main())
