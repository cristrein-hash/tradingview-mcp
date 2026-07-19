#!/usr/bin/env python3
"""COPILOT/JOURNAL — ciclo de captura+resolução (P1). Read-only no chart, NUNCA negoceia/alerta/pausa.
Por ciclo (daemon ~90-120s + WatchPaths bars_15m):
  1. lê as trades do chart (tag verde #N + Long/Short Position) com debounce;
  2. CAPTURA novas (congela snapshot completo -> trades.jsonl + sidecar) e regista REVISÕES de SL/TP
     (mantém entry/SL/TP ORIGINAIS = o GT no commit; revisão só logada);
  3. CANCELLED se a trade PENDING sumir do chart em 2 leituras estáveis não-vazias (anti vazio-transitório);
  4. RESOLVE PENDING/FILLED do RAW (fill quando preço toca o entry -> SL-first).
Só DADOS (0 Telegram, 0 ordens). py3.9.
Uso: (default) 1 ciclo · --dry (só lê+imprime, não escreve) · --status (imprime o ledger)."""
import os, sys, json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import chart_read
import snapshot as snaplib
import ledger
import resolve
STATE = HERE / ".state"; STATE.mkdir(exist_ok=True)
LOG = STATE / "capture.log"
LX = ZoneInfo("Europe/Lisbon")
_now = lambda: dt.datetime.now(LX).strftime("%Y-%m-%d %H:%M Lisboa")


def _log(o):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def run_cycle(dry=False):
    import store_reader as SR
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
           "captured": [], "revised": [], "cancelled": [], "resolved": []}
    r = chart_read.read_trades()
    if not r.get("ok"):
        out["status"] = f"SKIP: {r.get('reason')}"; _log(out); return out
    reads = [t for t in r.get("trades", []) if t.get("status") == "READ"]
    on_chart = {ledger._key(t) for t in reads}
    led = {x["dedup_key"]: x for x in ledger.load()}
    # 1) captura novas + revisões
    for t in reads:
        k = ledger._key(t)
        if k not in led:
            if not dry:
                snap = snaplib.build_snapshot(); rec = ledger.append(t, snap); led[k] = rec
            out["captured"].append(t["trade_id"])
        else:
            ex = led[k]
            if ex.get("status") == "PENDING" and (ex.get("sl") != t.get("sl") or ex.get("tp") != t.get("tp")):
                ex.setdefault("revisions", []).append(
                    {"ts": _now(), "entry": t.get("entry"), "sl": t.get("sl"), "tp": t.get("tp"), "rr": t.get("rr")})
                if not dry: ledger.upsert(ex)               # entry/SL/TP ORIGINAIS ficam; só regista revisão
                out["revised"].append(t["trade_id"])
    # 2) CANCELLED — a trade PENDING sumiu do chart. O read já é fiável (r.ok True + debounce); o vazio
    # GENUÍNO (Cris removeu tudo) também conta. A robustez vem das 2 AUSÊNCIAS CONSECUTIVAS (um edit não
    # mantém o desenho fora 2 ciclos ~4min). O antigo guard raw_n>0 nunca cancelava com o chart vazio (bug).
    if not dry:
        for k, ex in list(led.items()):
            if ex.get("status") != "PENDING":
                continue
            if k in on_chart:
                if ex.get("_absent"):
                    ex["_absent"] = 0; ledger.upsert(ex)
            else:
                ex["_absent"] = ex.get("_absent", 0) + 1
                if ex["_absent"] >= 2:
                    ex["status"] = "CANCELLED"; ex["cancelled_ts"] = _now(); out["cancelled"].append(ex["trade_id"])
                ledger.upsert(ex)
    # 3) resolve PENDING/FILLED do RAW
    bars = SR.bars("15") or []
    for ex in ledger.load():
        if ex.get("status") in ("PENDING", "FILLED"):
            before = ex.get("status")
            resolve.resolve_trade(ex, bars)
            if ex.get("status") != before:
                if not dry: ledger.upsert(ex)
                out["resolved"].append(f"{ex['trade_id']}:{before}->{ex['status']}")
    out["status"] = "OK" + (" (dry)" if dry else "")
    _log(out)
    return out


def show_status():
    rows = ledger.load()
    print(f"JOURNAL — {len(rows)} trade(s) no ledger")
    for t in rows:
        rev = f" ·{len(t.get('revisions',[]))}rev" if t.get("revisions") else ""
        print(f"  {t['trade_id']:>4} {t.get('direction','?'):>5} entry {t.get('entry')} SL {t.get('sl')} TP {t.get('tp')} "
              f"| {t.get('status'):8} b2r={t.get('bars_to_resolve')}{rev} | {t.get('detected_ts')}")


def main():
    if "--status" in sys.argv:
        show_status(); return
    dry = "--dry" in sys.argv
    out = run_cycle(dry=dry)
    print(json.dumps({k: out[k] for k in ("status", "captured", "revised", "cancelled", "resolved")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
