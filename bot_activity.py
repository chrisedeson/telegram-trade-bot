import logging
from logging.handlers import RotatingFileHandler

# Set up logging to a file with rotation (logs up to 5MB, keeps 5 backups)
log_file = 'logs/trade_bot.log'  # You can change this to any name you prefer
log_format = '%(asctime)s - %(levelname)s - %(message)s'

# Create the log directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

# Create a rotating file handler
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(log_format))

# Set up logging
logging.basicConfig(
    handlers=[file_handler],
    level=logging.INFO,
    format=log_format
)

# Example log messages
logging.info('Bot started successfully.')
logging.error('Failed to place order: Insufficient funds.')
logging.warning('Price slippage detected: 5 pips.')

# In your main code, log signals or trade actions
signal = {'symbol': 'EURUSD', 'type': 'BUY', 'entry': [1.2345, 1.2360], 'sl': 1.2300, 'tp': [1.2400]}
logging.info(f"Trade signal received: {signal}")
