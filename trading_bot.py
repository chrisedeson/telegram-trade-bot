import MetaTrader5 as mt5
import time

# Function to determine the pip size for the broker's quote
def get_pip_size(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Could not get info for symbol {symbol}")
        return None
    # For currency pairs, pip size is typically 0.0001 for 4-digit brokers
    # For XAU/USD (gold), it's typically 0.01
    # Check the number of digits to determine pip size
    if symbol_info.digits == 3:  # 3-digit broker
        return 0.001  # 1 pip = 0.001
    elif symbol_info.digits == 4:  # 4-digit broker
        return 0.0001  # 1 pip = 0.0001
    elif symbol_info.digits == 5:  # 5-digit broker
        return 0.00001  # 1 pip = 0.00001
    else:
        print(f"Unsupported number of digits: {symbol_info.digits}")
        return None

def send_to_broker(signal):
    # Make sure MT5 is initialized first (only once for the whole session)
    if not mt5.initialize():
        print("Failed to initialize MetaTrader5:", mt5.last_error())
        return

    symbol = signal["symbol"]
    volume = 0.01
    order_type = mt5.ORDER_TYPE_BUY if signal["type"] == "BUY" else mt5.ORDER_TYPE_SELL

    # Get the correct pip size for the broker
    pip_size = get_pip_size(symbol)
    if not pip_size:
        mt5.shutdown()
        return

    # Use midpoint of entry zone if it exists, or current market price
    if signal["entry"]:
        price = sum(signal["entry"]) / 2
    else:
        price = (
            mt5.symbol_info_tick(symbol).ask
            if order_type == mt5.ORDER_TYPE_BUY
            else mt5.symbol_info_tick(symbol).bid
        )

    # Prepare the initial request dictionary
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": signal["sl"],  # Initial Stop Loss
        "tp": signal["tp"][0] if signal["tp"] else None,  # Take Profit 1
        "deviation": 20,  # Slippage tolerance
        "magic": 123456,  # Unique identifier for the order
        "comment": "Telegram Signal",  # Order comment
        "type_time": mt5.ORDER_TIME_GTC,  # Good Till Canceled
        "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
    }

    # Send the order request
    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.retcode}, {result.comment}")
        mt5.shutdown()
        return
    else:
        print(f"Order placed successfully: {result}")

    # Get the order ticket number for tracking
    order_ticket = result.order

    # Implement Break-even and Trailing Stop Loss strategies
    while True:
        time.sleep(1)  # Wait for 1 second before checking the price again

        # Get the current price and the order's stop loss and take profit
        current_price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
        order = mt5.order_get(ticket=order_ticket)

        # Calculate the entry price and current distance from entry in pips
        entry_price = price
        pip_difference = (current_price - entry_price) / pip_size if order_type == mt5.ORDER_TYPE_BUY else (entry_price - current_price) / pip_size

        # Break-even logic: If price has moved 10 pips in favor, adjust SL to entry price
        if pip_difference >= 10 and order.sl != entry_price:
            print(f"Moving Stop Loss to Break-even: {entry_price}")
            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "order": order_ticket,
                "sl": entry_price,  # Set stop-loss to entry price (break-even)
                "tp": signal["tp"][0] if signal["tp"] else None,
                "deviation": 20,
                "magic": 123456,
                "comment": "Break-even adjustment",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            modify_result = mt5.order_send(modify_request)
            if modify_result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to move Stop Loss to break-even: {modify_result.retcode}")
            else:
                print(f"Stop Loss successfully moved to break-even: {entry_price}")

        # Trailing Stop Loss logic: If price is 3 pips near TP1, activate trailing stop
        if signal["tp"] and pip_difference >= (signal["tp"][0] - 3) * (1 / pip_size):
            trailing_stop = current_price - (3 * pip_size)  # 3 pip trailing stop
            if order.sl != trailing_stop:
                print(f"Setting Trailing Stop at: {trailing_stop}")
                modify_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "order": order_ticket,
                    "sl": trailing_stop,  # Set trailing stop
                    "tp": signal["tp"][0] if signal["tp"] else None,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": "Trailing Stop adjustment",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                modify_result = mt5.order_send(modify_request)
                if modify_result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Failed to set Trailing Stop: {modify_result.retcode}")
                else:
                    print(f"Trailing Stop successfully set at: {trailing_stop}")

        # Stop the loop if the order is closed or cancelled
        if order and order.volume == 0:
            print("Order has been closed or canceled.")
            break

    # Shutdown MT5 after all operations are done
    mt5.shutdown()
