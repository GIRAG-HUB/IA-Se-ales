"""Generación de señales. 1 = compra, -1 = venta, 0 = esperar."""
import pandas as pd


def add_signals(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    df = df.copy()

    vol_ok = (df["ATR_PCT"] > p["atr_pct_min"]) & (df["ATR_PCT"] < p["atr_pct_max"])
    up = (df["EMA20"] > df["EMA50"]) & (df["EMA50"] > df["EMA200"]) & (df["close"] > df["EMA20"])
    down = (df["EMA20"] < df["EMA50"]) & (df["EMA50"] < df["EMA200"]) & (df["close"] < df["EMA20"])
    strong = df["ADX"] >= p["adx_min"]

    buy = up & df["RSI"].between(*p["rsi_buy"]) & strong & vol_ok
    sell = down & df["RSI"].between(*p["rsi_sell"]) & strong & vol_ok

    df["signal"] = 0
    df.loc[buy, "signal"] = 1
    df.loc[sell, "signal"] = -1
    return df


def build_trade_levels(direction: int, entry: float, atr: float, p: dict):
    """Devuelve (sl, tp) a partir del ATR de la vela cerrada."""
    dist = p["atr_sl_mult"] * atr
    if direction == 1:
        return entry - dist, entry + dist * p["risk_reward"]
    return entry + dist, entry - dist * p["risk_reward"]
