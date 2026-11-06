"""Avisador de señales GRATIS: corre una vez, revisa los activos y manda Telegram.

Lo ejecuta GitHub Actions cada 15 minutos (ver .github/workflows/signals.yml).
No opera por ti: tú abres la operación a mano en la app de MT5.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

from indicators import add_indicators
from strategy import add_signals

BASE = Path(__file__).resolve().parent
STATE_FILE = BASE / "state.json"

TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
RANGE = {"5m": "30d", "15m": "60d", "30m": "60d", "1h": "180d"}


def fmt(x: float) -> str:
    return f"{x:.5g}"


def download(ticker: str, interval: str, tfm: int) -> pd.DataFrame:
    r = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        params={"range": RANGE[interval], "interval": interval},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=25,
    )
    r.raise_for_status()
    result = r.json()["chart"]["result"]
    if not result:
        raise ValueError("Sin datos")
    d = result[0]
    q = d["indicators"]["quote"][0]
    df = pd.DataFrame({
        "time": pd.to_datetime(d["timestamp"], unit="s", utc=True),
        "open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"],
    })
    df = df.dropna().sort_values("time").reset_index(drop=True)
    now = datetime.now(timezone.utc)
    df = df[df["time"] + pd.Timedelta(minutes=tfm) <= now].reset_index(drop=True)  # solo velas cerradas
    if len(df) < 300:
        raise ValueError("Menos de 300 velas completas")
    return df


def send(text: str) -> None:
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[sin Telegram configurado]\n" + text)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text}, timeout=15,
    )
    r.raise_for_status()  # si Telegram rechaza el mensaje, que se note


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def main() -> int:
    if os.getenv("SEND_TEST") == "1":
        if not os.getenv("TELEGRAM_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
            print("Faltan los Secrets TELEGRAM_TOKEN y/o TELEGRAM_CHAT_ID", file=sys.stderr)
            return 1
        send("Prueba OK: tu avisador de señales está conectado a Telegram.")
        return 0

    cfg =yaml.safe_load((BASE / "config.yaml").read_text(encoding="utf-8"))
    tf = cfg["timeframe"]
    tfm = TF_MIN[tf]
    p = cfg["strategy"]
    state = load_state()
    errors = 0

    for item in cfg["symbols"]:
        name = item["name"]
        try:
            df = download(item["ticker"], tf, tfm)
            df = add_signals(add_indicators(df), p)
            last, prev = df.iloc[-1], df.iloc[-2]
            sig = int(last["signal"])

            if sig == 0 or sig == int(prev["signal"]):
                continue  # solo avisa cuando la señal es NUEVA
            candle_end = last["time"] + pd.Timedelta(minutes=tfm)
            if datetime.now(timezone.utc) - candle_end > timedelta(minutes=3 * tfm):
                continue  # señal vieja
            key = last["time"].isoformat()
            if state.get(name) == key:
                continue  # ya avisada

            dist = p["atr_sl_mult"] * float(last["ATR"])
            tp_dist = dist * p["risk_reward"]
            lado = "COMPRA" if sig == 1 else "VENTA"
            sl_dir, tp_dir = ("debajo", "arriba") if sig == 1 else ("arriba", "debajo")
            send(
                f"SEÑAL {lado}: {name} ({tf})\n"
                f"Precio de referencia (Yahoo): {fmt(float(last['close']))}\n"
                f"Stop Loss: {fmt(dist)} {sl_dir} de tu precio de entrada\n"
                f"Take Profit: {fmt(tp_dist)} {tp_dir} de tu precio de entrada\n"
                f"RSI {last['RSI']:.1f} | ADX {last['ADX']:.1f}\n"
                f"Abre la operación en MT5 con TU precio y aplica esas distancias. "
                f"Riesgo máximo sugerido: 0.5 % de tu cuenta."
            )
            state[name] = key
        except Exception as e:
            errors += 1
            print(f"ERROR {name}: {e}", file=sys.stderr)

    # Si TODO falla, avisa como máximo una vez cada 6 horas (para no creer que "no hay señales").
    if errors == len(cfg["symbols"]):
        now = datetime.now(timezone.utc)
        last_err = state.get("_ultimo_error")
        if not last_err or now - datetime.fromisoformat(last_err) > timedelta(hours=6):
            send("Aviso: no pude descargar datos de Yahoo Finance. "
                 "Puede ser un bloqueo temporal; revisa el log en GitHub > Actions.")
            state["_ultimo_error"] = now.isoformat()

    STATE_FILE.write_text(json.dumps(state, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
