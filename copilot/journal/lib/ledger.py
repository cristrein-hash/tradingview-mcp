#!/usr/bin/env python3
"""COPILOT/JOURNAL — ledger das trades (P0): trades.jsonl (linha enxuta, grep-able) + sidecar do snapshot
pesado em snapshots/<N>_<epoch>.json. Dedup por (trade_id, entry). Horas humanas = Lisboa."""
import json, os, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
J = Path(__file__).resolve().parents[1]                 # copilot/journal
TRADES = J / "trades.jsonl"
SNAPDIR = J / "snapshots"; SNAPDIR.mkdir(parents=True, exist_ok=True)
LX = ZoneInfo("Europe/Lisbon")


def load():
    try:
        return [json.loads(x) for x in TRADES.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def _key(t):
    return f"{t.get('trade_id')}|{t.get('entry')}"


def keys():
    return {_key(t) for t in load()}


def save(rows):
    tmp = TRADES.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""))
    os.replace(tmp, TRADES)


def upsert(rec):
    """Substitui a linha com o mesmo dedup_key (ou acrescenta), mantém ordenado por deteção."""
    rows = [r for r in load() if r.get("dedup_key") != rec.get("dedup_key")]
    rows.append(rec)
    rows.sort(key=lambda r: r.get("detected_epoch") or 0)
    save(rows)
    return rec


def append(trade, snapshot):
    now = int(time.time())
    ref = f"snapshots/{str(trade['trade_id']).lstrip('#')}_{now}.json"
    (J / ref).write_text(json.dumps(snapshot, ensure_ascii=False))
    rec = {**trade, "detected_epoch": now,
           "detected_ts": dt.datetime.fromtimestamp(now, LX).strftime("%Y-%m-%d %H:%M Lisboa"),
           "status": "PENDING", "filled_ts": None, "resolved_ts": None,
           "bars_to_resolve": None, "mfe_R": None, "mae_R": None,
           "snapshot_ref": ref, "dedup_key": _key(trade), "revisions": [], "schema_version": 1}
    with open(TRADES, "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec
