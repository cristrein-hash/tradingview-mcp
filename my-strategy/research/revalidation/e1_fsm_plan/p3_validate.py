#!/usr/bin/env python3
"""P3 GATE — o gatilho LB (5 regras) reproduz as entradas do Cris? Caso-a-caso + NULL por instantes
aleatórios (árbitro prometido no veredito P2). Hit = na barra da entrada dele existe candidato com
|limit − entry| <= 0.5 ATR. py3.9 stdlib."""
import json
import sys
import random
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import raw_reader as RR  # noqa: E402
import lm_trigger as LT  # noqa: E402
import liquidity_map as LM  # noqa: E402
LX = dt.timezone(dt.timedelta(hours=1))


def jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except Exception:
        return []


def main():
    rnd = random.Random(20260829)
    raw = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    raw_rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(raw.items())]
    raw_end = raw_rows[-1]["t"]
    store_rows = sorted(jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl"), key=lambda x: x["t"])
    cases = jl(HERE / "ground_truth_cases.jsonl")
    dated = [c for c in cases if c.get("t") and c.get("entry")]
    seen = {}
    for c in sorted(dated, key=lambda x: x["t"]):
        k = (round(c["entry"], 1), dt.datetime.fromtimestamp(c["t"], dt.timezone.utc).date())
        if k not in seen:
            seen[k] = c
    longs = [c for c in seen.values() if c["dir"] == "LONG"]

    def probe(t, entry=None):
        src = raw_rows if t <= raw_end else store_rows
        upto = [b for b in src if b["t"] <= t][-450:]
        if len(upto) < 120:
            return None, None, None
        atr = LM._atr(upto[-400:])
        cs = LT.candidates_at(upto)
        if entry is None:
            return cs, atr, None
        best = min(cs, key=lambda c: abs(c["limit"] - entry)) if cs else None
        return cs, atr, best

    print(f"casos LONG distintos: {len(longs)}")
    print(f"{'caso':<20}{'quando':<15}{'entry':>9}  candidato do gatilho")
    hit = tot = 0
    for c in longs:
        cs, atr, best = probe(c["t"], c["entry"])
        if cs is None:
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20} SEM-BARRAS"); continue
        tot += 1
        when = dt.datetime.fromtimestamp(c["t"], LX).strftime("%d/%m/%y %H:%M")
        if best and abs(best["limit"] - c["entry"]) <= 0.5 * atr:
            hit += 1
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20}{when:<15}{c['entry']:>9}  HIT limit {best['limit']} sl {best['sl']} tgt {best['target']} r{best['r']} sweep={best['sweeping']} resp={best['respected']}")
        else:
            d = round(abs(best['limit'] - c['entry']) / atr, 2) if best else None
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20}{when:<15}{c['entry']:>9}  miss ({len(cs)} cands; mais perto a {d} ATR)" if best else
                  f"{(c['src']+':'+str(c['name']))[:19]:<20}{when:<15}{c['entry']:>9}  miss (0 candidatos)")
    print(f"\nCASOS: {hit}/{tot} ({100*hit//max(tot,1)}%)")

    # NULL: 150 instantes aleatórios — com que frequência existe candidato "hitável" por acaso?
    span = [b["t"] for b in raw_rows[500:]]
    n_hit = n_tot = 0
    for _ in range(150):
        t = rnd.choice(span)
        src = raw_rows
        upto = [b for b in src if b["t"] <= t][-450:]
        if len(upto) < 120:
            continue
        atr = LM._atr(upto[-400:])
        entry = upto[-1]["c"]
        cs = LT.candidates_at(upto)
        best = min(cs, key=lambda c: abs(c["limit"] - entry)) if cs else None
        n_tot += 1
        if best and abs(best["limit"] - entry) <= 0.5 * atr:
            n_hit += 1
    print(f"NULL (150 instantes aleatórios, entry=close): {n_hit}/{n_tot} ({100*n_hit//max(n_tot,1)}%)")
    print(f"CONTRASTE: casos {100*hit//max(tot,1)}% vs null {100*n_hit//max(n_tot,1)}%")
    json.dump(dict(cases=f"{hit}/{tot}", null=f"{n_hit}/{n_tot}"),
              open(HERE / "p3_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
