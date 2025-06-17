import re


def parse_signal(msg):
    msg = msg.upper()

    pair = re.search(r"\b(GOLD|XAUUSD|EURUSD|GBPUSD|BTCUSD|USDJPY|NAS100|US30)\b", msg)
    side = re.search(r"\b(BUY|SELL)\b", msg)

    entry = re.search(r"@\s*([\d.]+)\s*[-–—]\s*([\d.]+)", msg) or re.search(
        r"ENTRY\s*ZONE[L]?\s*[:;]?\s*([\d.]+)\s*[-–—]\s*([\d.]+)", msg
    )

    sl = re.search(r"\bSL\s*[:;]?\s*([\d.]+)", msg) or re.search(
        r"STOP[\s-]?LOSS\s*[:;]?\s*([\d.]+)", msg
    )

    tps = re.findall(r"TP\s*\d*\s*[:;]?\s*([\d.]+)", msg)

    if pair and side:
        return {
            "symbol": pair.group(1),
            "type": side.group(1),
            "entry": [float(entry.group(1)), float(entry.group(2))] if entry else None,
            "sl": float(sl.group(1)) if sl else None,
            "tp": [float(tp) for tp in tps] if tps else [],
        }

    return None
