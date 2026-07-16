#!/usr/bin/env python3
"""Helper DETERMINÍSTICO para armar/desarmar níveis do realtime_monitor (logs/levels.json).
Chamado pela ponte Telegram (claude -p) ou à mão. Escrita atómica + schema validado (evita que edição
livre corrompa o ficheiro). NÃO envia Telegram, NÃO toca produção. py3.9.
Uso:
  arm_level.py arm <price> <cross_below|cross_above> [--note "..."] [--symbol PEPPERSTONE:XAUUSD]
                                                     [--no-oneshot] [--cooldown 300] [--hyst 10]
  arm_level.py disarm <id>
  arm_level.py list
"""
import sys, json, os, time, argparse
from pathlib import Path

LOGS = Path(__file__).resolve().parent / "logs"; LOGS.mkdir(exist_ok=True)
F = LOGS / "levels.json"
DEFAULT_SYMBOL = "PEPPERSTONE:XAUUSD"


def load():
    try:
        return json.loads(F.read_text())
    except Exception:
        return {"version": 1, "levels": []}


def save(d):
    tmp = F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False)); os.replace(tmp, F)


def cmd_arm(a):
    if a.side not in ("cross_below", "cross_above"):
        print("side inválido (cross_below|cross_above)"); return 1
    price = float(a.price)
    d = load()
    lid = f"{a.symbol.split(':')[-1].lower()}-{price:g}-{a.side}-{int(time.time())}"
    level = {"id": lid, "symbol": a.symbol, "price": price, "side": a.side,
             "note": a.note or "", "armed_ts": int(time.time()),
             "one_shot": not a.no_oneshot, "cooldown_s": a.cooldown,
             "hysteresis_ticks": a.hyst, "state": "armed"}
    d.setdefault("levels", []).append(level)
    save(d)
    print(f"✅ armado {lid}: {a.symbol} {a.side} {price:g} one_shot={not a.no_oneshot}")
    return 0


def cmd_disarm(a):
    d = load(); found = False
    try:
        want_price = float(a.id)
    except ValueError:
        want_price = None
    for l in d.get("levels", []):
        if l.get("state") != "armed":
            continue
        if l.get("id") == a.id or (want_price is not None and float(l.get("price")) == want_price):
            l["state"] = "disarmed"; found = True
    save(d)
    print("✅ desarmado" if found else "⚠️ id não encontrado")
    return 0 if found else 1


def cmd_list(a):
    d = load()
    armed = [l for l in d.get("levels", []) if l.get("state") == "armed"]
    if not armed:
        print("(sem níveis armados)"); return 0
    for l in armed:
        print(f"  {l['id']} | {l['symbol']} {l['side']} {l['price']:g} | one_shot={l.get('one_shot')} | {l.get('note','')}")
    return 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("arm"); pa.add_argument("price"); pa.add_argument("side")
    pa.add_argument("--note", default=""); pa.add_argument("--symbol", default=DEFAULT_SYMBOL)
    pa.add_argument("--no-oneshot", action="store_true"); pa.add_argument("--cooldown", type=int, default=300)
    pa.add_argument("--hyst", type=int, default=10)
    pd = sub.add_parser("disarm"); pd.add_argument("id")
    sub.add_parser("list")
    a = p.parse_args()
    return {"arm": cmd_arm, "disarm": cmd_disarm, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
