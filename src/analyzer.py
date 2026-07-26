import json
import os

HISTORY_FILE = "data/history.json"

def analyze_volatile_timeframes():
    """30分ログから各銘柄のピークボラティリティ時間帯を計算"""
    if not os.path.exists(HISTORY_FILE):
        return None

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return None

    time_keys = sorted(history.keys())
    if len(time_keys) < 2:
        return None

    movements = {}
    for i in range(1, len(time_keys)):
        prev_t, curr_t = time_keys[i-1], time_keys[i]
        slot_label = f"{prev_t}~{curr_t}"
        movements[slot_label] = {}

        for pair, curr_p in history[curr_t].items():
            prev_p = history[prev_t].get(pair)
            if prev_p and prev_p > 0:
                movements[slot_label][pair] = ((curr_p - prev_p) / prev_p) * 100

    symbol_peaks = {}
    if not movements:
        return None

    sample_slot = list(movements.keys())[0]
    for pair in movements[sample_slot].keys():
        max_change = 0.0
        peak_slot = "データなし"
        symbol = pair.split('_')[0].upper()

        for slot, pair_pcts in movements.items():
            pct = pair_pcts.get(pair, 0.0)
            if abs(pct) > abs(max_change):
                max_change = pct
                peak_slot = slot

        symbol_peaks[symbol] = {"peak_slot": peak_slot, "change_pct": max_change}

    return symbol_peaks
