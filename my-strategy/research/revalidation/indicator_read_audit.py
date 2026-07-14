#!/usr/bin/env python3
"""AUDITORIA da leitura dos INDICADORES (ordem Cris 2026-07-14): comparar a MINHA extração (fresca,
direto do RAW HD, em a1_context_build.py) com a extração CANÓNICA (primitives/*.primitives.json, que
os engines de sucesso extraíram direto do RAW HD via build_causal_primitives). Bloco de teste:
2025-08-25_to_2025-11-25. Verifica: série/RSI, NAS (LONG/SHORT), SMC (BOS/CHoCH), zonas OB
(SUPPLY/DEMAND) — contagens + spot-check de valores. Se bate = leitura fiel. Só medição."""
import gzip, json
from collections import Counter
from pathlib import Path
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
PRIM = Path("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/primitives")
BLK = "XAUUSD_15m_replay_2025-08-25_to_2025-11-25"
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None

# ---- MINHA extração (replica a1_context_build, PER-BLOCO) ----
bars = {}; rsi_t = {}; nas = []; smc = []; zones = {}
mnas = msmc = -1; nasi = smci = False
snaps = []
with gzip.open(RAW / f"{BLK}.jsonl.gz", "rt") as fh:
    for line in fh:
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
for r in snaps:
    oh = r.get("ohlcv") or []
    cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
    for b in oh:
        if isinstance(b, dict) and b.get("time") is not None:
            bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
    rv = grp(r, "study_values", "Relative Strength")
    if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
    ng = grp(r, "pine_labels", "NAS"); ngi = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
    if not nasi:
        if ngi: mnas = max(ngi); nasi = True
    else:
        for l in (ng.get("labels") or []) if ng else []:
            lid = l.get("id")
            if lid is None or lid <= mnas: continue
            txt = str(l.get("text", "")).upper()
            if "LONG" in txt or "SHORT" in txt: nas.append({"t": cur, "dir": "LONG" if "LONG" in txt else "SHORT"})
        if ngi: mnas = max(mnas, max(ngi))
    sg = grp(r, "pine_labels", "Smart Money"); sgi = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
    if not smci:
        if sgi: msmc = max(sgi); smci = True
    else:
        for l in (sg.get("labels") or []) if sg else []:
            lid = l.get("id")
            if lid is None or lid <= msmc: continue
            smc.append({"t": cur, "text": l.get("text")})
        if sgi: msmc = max(msmc, max(sgi))
    ob = grp(r, "pine_boxes", "Custom OB")
    for bx in (ob.get("all_boxes") if ob else []) or []:
        zid = bx.get("id")
        if zid is None: continue
        if zid not in zones:
            zones[zid] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur}

mine = {"bars": len(bars), "rsi": sum(1 for v in rsi_t.values() if v is not None),
        "nas_L": sum(1 for e in nas if e["dir"] == "LONG"), "nas_S": sum(1 for e in nas if e["dir"] == "SHORT"),
        "bos": sum(1 for e in smc if "BOS" in str(e["text"])), "choch": sum(1 for e in smc if "CHoCH" in str(e["text"])),
        "sup": sum(1 for z in zones.values() if "SUPPLY" in z["text"]), "dem": sum(1 for z in zones.values() if "DEMAND" in z["text"])}

# ---- CANÓNICA (primitives) ----
p = json.loads((PRIM / f"{BLK}.primitives.json").read_text())
canon = {"bars": p["n_bars"], "rsi": sum(1 for s in p["series"] if s.get("rsi") is not None),
         "nas_L": sum(1 for e in p["nas_events"] if e["dir"] == "LONG"), "nas_S": sum(1 for e in p["nas_events"] if e["dir"] == "SHORT"),
         "bos": sum(1 for e in p["smc_events"] if "BOS" in str(e["text"])), "choch": sum(1 for e in p["smc_events"] if "CHoCH" in str(e["text"])),
         "sup": sum(1 for z in p["zones"] if "SUPPLY" in z["text"]), "dem": sum(1 for z in p["zones"] if "DEMAND" in z["text"])}

print(f"BLOCO {BLK}\n{'campo':<8} {'MINHA':>8} {'CANÓNICA':>9} {'match'}")
for k in ("bars", "rsi", "nas_L", "nas_S", "bos", "choch", "sup", "dem"):
    print(f"{k:<8} {mine[k]:>8} {canon[k]:>9} {'✅' if mine[k] == canon[k] else '❌ DIVERGE'}")
# spot-check RSI: 3 timestamps comuns
common = [t for t in sorted(rsi_t) if rsi_t[t] is not None][:0]
pr = {s["t"]: s.get("rsi") for s in p["series"]}
sample = [t for t in sorted(rsi_t) if rsi_t[t] is not None and t in pr][100:103]
print("\nspot-check RSI (3 barras):")
for t in sample:
    a, b = rsi_t[t], pr[t]
    print(f"  t={t}  minha={a}  canónica={b}  {'✅' if a is not None and b is not None and abs(a-b) < 0.05 else '❌'}")
