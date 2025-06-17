import re

def parse_signal(msg):
    msg = msg.upper()

    # ✅ Match trading pair
    pair = re.search(r'\b(GOLD|XAUUSD|EURUSD|GBPUSD|BTCUSD|USDJPY|NAS100|US30)\b', msg)

    # ✅ Match BUY/SELL
    side = re.search(r'\b(BUY|SELL)\b', msg)

    # ✅ Match flexible Entry Zone (handles "@", "between", etc.)
    # Looks for something like: "BUY @3439.5 - 3436.5" or "SELL 3439.5–3436.5"
    entry_match = re.search(r'(BUY|SELL)[^0-9]{0,10}[@:]?\s*([\d.]+)\s*[-–—]\s*([\d.]+)', msg)

    entry = None
    if entry_match:
        entry = [float(entry_match.group(2)), float(entry_match.group(3))]

    # ✅ Match Stop Loss (SL, Stoploss, Stop Loss)
    sl = (
        re.search(r'\bSL\s*[:;]?\s*([\d.]+)', msg) or
        re.search(r'STOP[\s-]?LOSS\s*[:;]?\s*([\d.]+)', msg)
    )

    # ✅ Match Take Profits (TP1, TP2, TP: ...)
    tps = re.findall(r'TP\s*\d*\s*[:;]?\s*([\d.]+)', msg)

    # ✅ Final result
    if pair and side:
        return {
            "symbol": pair.group(1),
            "type": side.group(1),
            "entry": entry,
            "sl": float(sl.group(1)) if sl else None,
            "tp": [float(tp) for tp in tps] if tps else []
        }

    return None
