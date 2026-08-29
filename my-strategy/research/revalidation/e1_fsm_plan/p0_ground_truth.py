#!/usr/bin/env python3
"""P0 — GROUND TRUTH DOSSIER (gate: Cris confirma a lista). Consolida TODOS os trades reais conhecidos:
(1) 35 long_position de julho (cris_manual_trades_20260704.json, com timestamps);
(2) 26 posições das 4 tabs desta semana (all_positions_20260828.json);
(3) 16 trades do copilot/journal (sem timestamp legível — incluídos com t=None, marcados);
(4) trades declarados no declared_trades_log.md (parse manual mínimo);
(5) trades dos vídeos do Inter Equity (níveis citados nos breakdowns — para validação do método).
Output: ground_truth_cases.jsonl + lista legível para confirmação. py3 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
LX = dt.timezone(dt.timedelta(hours=1))
cases = []


def add(src, name, dirn, t, entry, sl=None, tgt=None, note=""):
    cases.append(dict(src=src, name=name, dir=dirn, t=t, entry=entry, sl=sl, tgt=tgt, note=note))


# (1) julho — 35 long_position com pontos (price, time); SL/TP dos props se existirem
d = json.load(open(REPO / "research/xau_15m_bb_nas_leonardo/results/cris_manual_trades_20260704.json"))
for s in d.get("shapes", []):
    pr = s.get("props") or {}
    pts = pr.get("points") or []
    if not pts:
        continue
    entry = pts[0].get("price"); t = pts[0].get("time")
    props = pr.get("properties") or {}
    sd = (props.get("stopLevel") or 0) / 100.0
    td = (props.get("profitLevel") or 0) / 100.0
    sl = round(entry - sd, 2) if sd else None
    tgt = round(entry + td, 2) if td else None
    add("chart_jul", s.get("id"), "LONG", t, entry, sl, tgt)

# (2) esta semana — 26 posições das 4 tabs
for p in json.load(open(REPO / "research/all_positions_20260828.json")):
    if not p.get("price") or not p.get("t"):
        continue
    add("chart_aug", f"{p['res']}m", "LONG" if p["name"] == "long_position" else "SHORT",
        p["t"], p["price"], note=f"tab {p['res']}")

# (3) journal — 16 sem timestamp
for r in [json.loads(l) for l in open(REPO / "copilot/journal/trades.jsonl") if l.strip()]:
    add("journal", r.get("trade_id"), (r.get("direction") or "").upper(), None,
        r.get("entry"), r.get("sl"), r.get("tp"),
        note=f"outcome={r.get('outcome')} {str(r.get('reason') or '')[:40]}")

# (4) declarados (log narrado — o caso documentado 07/08)
add("declared", "FN 07/08", "LONG", int(dt.datetime(2026, 8, 7, 17, 0, tzinfo=dt.timezone.utc).timestamp()),
    4338.0, 4300.0, None, "swing fim-de-semana FN; SL alargado+size 1%")
add("declared", "FTMO 07/08", "LONG", int(dt.datetime(2026, 8, 7, 17, 0, tzinfo=dt.timezone.utc).timestamp()),
    4341.0, 4300.0, None, "swing FTMO")

# (5) vídeos Inter Equity (níveis citados; datas nem sempre conhecidas — servem à validação do MÉTODO)
add("video", "IE gold $13k short", "SHORT", None, 4081.87, None, 4041.28, "entry acima do high varrido; alvos 4041/3941")
add("video", "IE gold $3500 long", "LONG", None, 3977.81, None, 4021.69, "low varrido 3977.81; alvo SL-dos-sellers 4021.69")
add("video", "IE gold $30k long", "LONG", None, None, None, 2524.0, "low pos-CPI varrido; alvos 2524/2529/2531 (data CPI)")
add("video", "IE gold live $9k", "LONG", None, 3633.675, None, 3651.0, "blue line 3633.675; alvos 3651/3673.20")

out = HERE / "ground_truth_cases.jsonl"
out.write_text("\n".join(json.dumps(c) for c in cases) + "\n")


def hm(t):
    return dt.datetime.fromtimestamp(t, LX).strftime("%d/%m/%y %H:%M") if t else "s/data"


print(f"=== P0 GROUND TRUTH — {len(cases)} casos (para confirmação do Cris) ===")
from collections import Counter
print("por fonte:", dict(Counter(c["src"] for c in cases)))
print()
for c in cases:
    print(f"{c['src']:<10} {hm(c['t']):<15} {c['dir']:<6} entry {c['entry']} sl {c['sl']} tgt {c['tgt']}  {c['note'][:45]}")
