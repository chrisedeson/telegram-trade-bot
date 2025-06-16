import MetaTrader5 as mt5
import time

# Step 1: Define alias variants for better symbol recognition
RAW_ALIASES = {
    "XAUUSD": ["GOLD", "XAU", "XAUUSD", "GOLDD"],
    "XAGUSD": ["SILVER", "XAG", "XAGUSD"],
    "BTCUSD": ["BTC", "BTCUSD", "BITCOIN"],
    "ETHUSD": ["ETH", "ETHUSD", "ETHER", "ETHEREUM"],
    "US30": ["US30", "DOW", "DOWJONES"],
    "NAS100": ["NAS100", "US100", "NASDAQ"],
    "SPX500": ["SPX500", "SP500", "S&P", "S&P500"],
    "EURUSD": ["EURUSD", "EUROUSD"],
    "GBPUSD": ["GBPUSD", "POUNDUSD"],
    "USDJPY": ["USDJPY", "JAPYEN", "USJPY"],
    "AUDUSD": ["AUDUSD", "AUSUSD"],
    "USDCHF": ["USDCHF", "CHFUSD"],
    "USDCAD": ["USDCAD", "CADUSD"],
    "NZDUSD": ["NZDUSD", "NZUSD"],
}

# Step 2: Symbol resolver using alias list
def resolve_symbol_name(name):
    name = name.upper().strip()
    for actual_symbol, aliases in RAW_ALIASES.items():
        if name in aliases:
            return actual_symbol
    return name  # fallback to raw name if no match

# Step 3: Determine pip size
def get_pip_size(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Could not get info for symbol {symbol}")
        return None

    if symbol_info.digits == 2:
        return 0.01
    elif symbol_info.digits == 3:
        return 0.001
    elif symbol_info.digits == 4:
        return 0.0001
    elif symbol_info.digits == 5:
        return 0.00001
    else:
        print(f"Unsupported number of digits: {symbol_info.digits}")
        return None

# Step 4: Main function to send signal
def send_to_broker(signal):
    if not mt5.initialize():
        print("Failed to initialize MetaTrader5:", mt5.last_error())
        return

    # Resolve the symbol from the signal
    resolved_name = resolve_symbol_name(signal["symbol"])
    symbol = resolved_name

    # Ensure the symbol is in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol {symbol} in Market Watch")
        mt5.shutdown()
        return

    volume = 0.01
    order_type = mt5.ORDER_TYPE_BUY if signal["type"].upper() == "BUY" else mt5.ORDER_TYPE_SELL

    pip_size = get_pip_size(symbol)
    if pip_size is None:
        mt5.shutdown()
        return

    # Use average entry or current price
    price = (
        sum(signal["entry"]) / 2
        if signal["entry"]
        else (
            mt5.symbol_info_tick(symbol).ask
            if order_type == mt5.ORDER_TYPE_BUY
            else mt5.symbol_info_tick(symbol).bid
        )
    )

    # Place the trade
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
        print(f"Order failed: {result.retcode}, {result.comment}")
        mt5.shutdown()
        return
    else:
        print(f"Order placed successfully: {result}")

    order_ticket = result.order

    # Monitor the trade for SL/TP logic
    while True:
        time.sleep(1)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"Failed to get tick data for {symbol}")
            break

        current_price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        order = mt5.order_get(ticket=order_ticket)

        if not order:
            print("Order not found or closed.")
            break

        entry_price = price
        pip_difference = (
            (current_price - entry_price) / pip_size
            if order_type == mt5.ORDER_TYPE_BUY
            else (entry_price - current_price) / pip_size
        )

        # Break-even logic: move SL to entry after 10 pips
        if pip_difference >= 10 and order.sl != entry_price:
            print(f"Moving SL to break-even: {entry_price}")
            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "order": order_ticket,
                "sl": entry_price,
                "tp": signal["tp"][0] if signal["tp"] else None,
                "deviation": 20,
                "magic": 123456,
                "comment": "Break-even adjustment",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            modify_result = mt5.order_send(modify_request)
            if modify_result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Break-even SL failed: {modify_result.retcode}")
            else:
                print(f"Break-even SL set to: {entry_price}")

        # Trailing SL logic: 3 pips before TP1
        if signal["tp"] and pip_difference >= (signal["tp"][0] - 3) * (1 / pip_size):
            trailing_stop = current_price - (3 * pip_size)
            if order.sl != trailing_stop:
                print(f"Setting trailing stop: {trailing_stop}")
                modify_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "order": order_ticket,
                    "sl": trailing_stop,
                    "tp": signal["tp"][0] if signal["tp"] else None,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": "Trailing Stop",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                modify_result = mt5.order_send(modify_request)
                if modify_result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Trailing Stop failed: {modify_result.retcode}")
                else:
                    print(f"Trailing Stop set: {trailing_stop}")

        if order.volume == 0:
            print("Order closed.")
            break

    mt5.shutdown()
