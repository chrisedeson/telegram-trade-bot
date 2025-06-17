import os
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
log_file = "logs/trade_bot.log"
os.makedirs("logs", exist_ok=True)

file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

logging.basicConfig(
    handlers=[file_handler],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Bot initialized and logging started.")
