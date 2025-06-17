# trading_bot.py

import MetaTrader5 as mt5
import time
import os
from dotenv import load_dotenv

RAW_ALIASES = {
    "XAUUSD": ["GOLD", "XAU", "XAUUSD"],
    "BTCUSD": ["BTC", "BTCUSD", "BITCOIN"],
    "US30": ["US30", "DOW", "DOWJONES"],
    "NAS100": ["NAS100", "US100", "NASDAQ"],
    "EURUSD": ["EURUSD", "EUROUSD"],
    "GBPUSD": ["GBPUSD", "POUNDUSD"],
    "USDJPY": ["USDJPY", "JAPYEN", "USJPY"],
}

signal_cache = {}

# Load the .env file (choose which .env manually or via command line)
ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(dotenv_path=ENV_FILE)

MT5_PATH = os.getenv("MT5_PATH")

def resolve_symbol_name(name):
    name = name.upper().strip()
    for actual, aliases in RAW_ALIASES.items():
        if name in aliases:
            return actual
    return name

def get_pip_size(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"Symbol info not found: {symbol}")
        return None
    return {2: 0.01, 3: 0.001, 4: 0.0001, 5: 0.00001}.get(info.digits, None)

def initialize_mt5():
    if not mt5.initialize(path=MT5_PATH):
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True

def send_to_broker(signal, message_id=None):
    if message_id and message_id in signal_cache:
        print(f"Signal already processed for message {message_id}.")
        return

    if not initialize_mt5():
        return

    symbol = resolve_symbol_name(signal["symbol"])
    if not mt5.symbol_select(symbol, True):
        print("Symbol not in Market Watch")
        mt5.shutdown()
        return

    volume = 0.01
    order_type = mt5.ORDER_TYPE_BUY if signal["type"] == "BUY" else mt5.ORDER_TYPE_SELL

    pip = get_pip_size(symbol)
    if pip is None:
        mt5.shutdown()
        return

    price = (
        sum(signal["entry"]) / 2 if signal["entry"]
        else mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY
        else mt5.symbol_info_tick(symbol).bid
    )

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": signal["sl"],
        "tp": signal["tp"][0] if signal["tp"] else None,
        "deviation": 20,
        "magic": 123456,
        "comment": "Telegram Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Trade failed: {result.retcode}")
    else:
        print(f"Trade placed: {result.order}")
        if message_id:
            signal_cache[message_id] = signal

    mt5.shutdown()

def update_trade(message_id, new_signal):
    if not initialize_mt5():
        return

    if message_id not in signal_cache:
        print("No cached signal for message edit.")
        mt5.shutdown()
        return

    symbol = resolve_symbol_name(new_signal["symbol"])
    orders = mt5.positions_get(symbol=symbol)

    if not orders:
        print("No open position found to update.")
        mt5.shutdown()
        return

    order = orders[0]
    new_sl = new_signal["sl"]
    new_tp = new_signal["tp"][0] if new_signal["tp"] else None

    modify = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": order.ticket,
        "sl": new_sl,
        "tp": new_tp,
        "deviation": 20,
        "magic": 123456,
        "comment": "Signal Edited",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(modify)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("Trade updated.")
        signal_cache[message_id] = new_signal
    else:
        print(f"Failed to update trade: {result.retcode}")

    mt5.shutdown()
