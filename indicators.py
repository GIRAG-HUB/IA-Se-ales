"""Indicadores técnicos: EMA, RSI, ATR, ADX (mismos de tu versión original)."""
import numpy as np
import pandas as pd

N = 14


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["close"]

    for span in (20, 50, 200):
        df[f"EMA{span}"] = c.ewm(span=span, adjust=False).mean()

    # RSI
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / N, adjust=False, min_periods=N).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / N, adjust=False, min_periods=N).mean()
    rs = gain / loss
    df["RSI"] = 100 - 100 / (1 + rs)
    df.loc[(loss == 0) & (gain > 0), "RSI"] = 100
    df.loc[(loss == 0) & (gain == 0), "RSI"] = 50

    # ATR
    prev = c.shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / N, adjust=False, min_periods=N).mean()
    df["ATR"] = atr

    # ADX
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    pdi = 100 * plus_dm.ewm(alpha=1 / N, adjust=False, min_periods=N).mean() / atr
    mdi = 100 * minus_dm.ewm(alpha=1 / N, adjust=False, min_periods=N).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    df["ADX"] = dx.ewm(alpha=1 / N, adjust=False, min_periods=N).mean()

    df["ATR_PCT"] = atr / c
    return df.dropna().reset_index(drop=True)
