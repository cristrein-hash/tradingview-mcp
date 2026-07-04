#!/usr/bin/env python3
"""DA ATAQUE 2b — causalidade das zonas vs RAW gz (1H sandbox + bloco 15M oficial).
born_t<=t0<=last_t é causal SSE (a) presença do id é contígua entre born e last (visível em t0 =
conhecível em t0) e (b) high/low não derivam durante a vida (builder guarda bounds FINAIS —
'extensão dinâmica' = lookahead de geometria se os bounds mudam). Verifica ambos no RAW:
por id: first/last cur_t, contiguidade de presença, bounds iniciais vs finais, drift máximo.
Compara 5 zonas vs prim60. Leitura apenas — nada é escrito no RAW."""
import gzip, json, sys
from pathlib import Path

RAW1H = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1H")
RAW15 = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
HERE = Path(__file__).resolve().parent

def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)

def scan(path):
    snaps = []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    Z = {}  # id -> stats
    for si, r in enumerate(snaps):
        oh = r.get("ohlcv") or []
        cur_t = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is None: continue
            hi, lo = bx.get("high"), bx.get("low")
            if zid not in Z:
                Z[zid] = {"first_t": cur_t, "last_t": cur_t, "first_si": si, "last_si": si, "n_seen": 1,
                          "hi0": hi, "lo0": lo, "hiF": hi, "loF": lo, "max_dhi": 0.0, "max_dlo": 0.0,
                          "text": str(bx.get("text", "")).upper()}
            else:
                z = Z[zid]
                z["max_dhi"] = max(z["max_dhi"], abs((hi or 0) - (z["hi0"] or 0)))
                z["max_dlo"] = max(z["max_dlo"], abs((lo or 0) - (z["lo0"] or 0)))
                z["hiF"], z["loF"] = hi, lo
                z["last_t"], z["last_si"], z["n_seen"] = cur_t, si, z["n_seen"] + 1
    return Z, len(snaps)

def report(tag, Z, nsnap):
    zs = list(Z.values())
    gaps = [z for z in zs if z["n_seen"] < (z["last_si"] - z["first_si"] + 1)]
    drift = [z for z in zs if z["max_dhi"] > 1e-9 or z["max_dlo"] > 1e-9]
    print(f"\n[{tag}] snapshots={nsnap} zonas={len(zs)}")
    print(f"  presença NÃO-contígua (gaps): {len(gaps)}/{len(zs)} ({100*len(gaps)/max(1,len(zs)):.1f}%)")
    if gaps:
        wg = sorted(gaps, key=lambda z: (z['last_si']-z['first_si']+1)-z['n_seen'], reverse=True)[:3]
        for z in wg: print(f"    ex.: seen {z['n_seen']}/{z['last_si']-z['first_si']+1} snapshots ({z['text'][:20]})")
    print(f"  bounds mudam durante a vida: {len(drift)}/{len(zs)} ({100*len(drift)/max(1,len(zs)):.1f}%)")
    if drift:
        d = sorted(drift, key=lambda z: max(z["max_dhi"], z["max_dlo"]), reverse=True)
        vals = sorted(max(z["max_dhi"], z["max_dlo"]) for z in drift)
        print(f"    drift $ mediano={vals[len(vals)//2]:.2f} max={vals[-1]:.2f}")
        for z in d[:3]: print(f"    ex.: {z['text'][:24]} hi {z['hi0']}→{z['hiF']} lo {z['lo0']}→{z['loF']} (max Δ {max(z['max_dhi'],z['max_dlo']):.2f})")
    return zs

if __name__ == "__main__":
    # ---- 1H (par campeão usa 1H demand) ----
    allZ = {}
    for blk in ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25"):
        Z, n = scan(RAW1H / f"XAUUSD_60m_replay_{blk}.jsonl.gz")
        report(f"1H {blk}", Z, n)
        allZ[blk] = Z
    # comparação com prim60: 5 zonas (3 DEMAND + 2 SUPPLY, determinístico)
    print("\nSPOT 5 zonas prim60 vs RAW (born_t/last_t/high/low):")
    for blk in ("2025-05-25_to_2025-11-25",):
        prim = json.load(open(SBX / "prim60" / f"XAUUSD_60m_replay_{blk}.primitives.json"))
        zsP = prim["zones"] if isinstance(prim["zones"], list) else list(prim["zones"].values())
        dem = [z for z in zsP if "DEMAND" in z["text"] and not z.get("pre_existing")][:3]
        sup = [z for z in zsP if "SUPPLY" in z["text"] and not z.get("pre_existing")][:2]
        for z in dem + sup:
            r = allZ[blk].get(z["id"])
            if r is None: print(f"  id={z['id']} NÃO ENCONTRADO no RAW ⚠️"); continue
            ok = (z["born_t"] == r["first_t"] and z["last_t"] == r["last_t"]
                  and z["high"] == r["hiF"] and z["low"] == r["loF"])
            print(f"  id={z['id']} {z['text'][:16]:<16} born {z['born_t']}=={r['first_t']} last {z['last_t']}=={r['last_t']}"
                  f" hi {z['high']}=={r['hiF']} lo {z['low']}=={r['loF']} → {'OK' if ok else 'MISMATCH ⚠️'}"
                  f" | contíguo={r['n_seen']==(r['last_si']-r['first_si']+1)} drift_max={max(r['max_dhi'],r['max_dlo']):.2f}")
    # ---- 15M oficial: 1 bloco (par campeão usa 15M supply) ----
    Z, n = scan(RAW15 / "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz")
    report("15M 2025-05-25_to_2025-08-25 (oficial)", Z, n)
