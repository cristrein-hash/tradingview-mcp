#!/usr/bin/env python3
"""P1 GATE — os pools causais (lm_pools) cobrem os níveis dos casos P0? Medição caso-a-caso
(ordem Cris: nunca julgar sem detalhamento). Para cada caso datado: pools_asof no instante do trade
(RAW canónico p/ históricos; store p/ semana 24-28/08) e distância do entry ao pool mais próximo.
Cobertura = entry a <=0.5 ATR de um pool (CLUSTER_ATR herdado). py3.9 stdlib."""
import json
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import raw_reader as RR  # noqa: E402
import lm_pools as LP  # noqa: E402
import liquidity_map as LM  # noqa: E402
LX = dt.timezone(dt.timedelta(hours=1))


def jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except Exception:
        return []


def main():
    raw = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    raw_rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(raw.items())]
    raw_end = raw_rows[-1]["t"]
    store_rows = sorted(jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl"), key=lambda x: x["t"])
    cases = jl(HERE / "ground_truth_cases.jsonl")
    dated = [c for c in cases if c.get("t") and c.get("entry")]
    # DA-fix P1(a): dedup por TRADE distinto (entry, dia) — chart_aug repete o mesmo trade em 4 tabs;
    # canoniza 1 t por trade (o mais cedo = barra 15M de origem)
    seen = {}
    for c in sorted(dated, key=lambda x: x["t"]):
        k = (round(c["entry"], 1), dt.datetime.fromtimestamp(c["t"], dt.timezone.utc).date())
        if k not in seen:
            seen[k] = c
    dated = list(seen.values())
    print(f"casos datados com entry: {len(dated)} de {len(cases)}")
    print(f"{'caso':<22}{'quando':<15}{'dir':<6}{'entry':>9}{'pool_perto':>16}{'dist':>7}{'dATR':>6}  veredito")
    cov = tot = 0
    details = []
    for c in dated:
        t, e = c["t"], c["entry"]
        src_rows = raw_rows if t <= raw_end else store_rows
        upto = [b for b in src_rows if b["t"] <= t]
        lowconf = " LOW-CONF(janela<400)" if len(upto) < 400 else ""
        if len(upto) < 100:
            print(f"{(c['src']+' '+str(c['name']))[:21]:<22}{'—':<15}{c['dir']:<6}{e:>9}  SEM-BARRAS")
            continue
        atr = LM._atr(upto[-400:])
        side = "SSL" if c["dir"] == "LONG" else "BSL"
        pools = LP.pools_asof(upto, side=side)
        if not pools:
            print(f"{(c['src']+' '+str(c['name']))[:21]:<22}{dt.datetime.fromtimestamp(t,LX).strftime('%d/%m/%y %H:%M'):<15}{c['dir']:<6}{e:>9}  SEM-POOLS")
            tot += 1
            continue
        # pool mais próximo do entry (borda relevante: hi p/ SSL, lo p/ BSL)
        def dist(p):
            edge = p["hi"] if side == "SSL" else p["lo"]
            return abs(e - edge)
        best = min(pools, key=dist)
        dd = dist(best); datr = dd / atr if atr else 99
        ok = datr <= 0.5
        cov += ok; tot += 1
        details.append(dict(case=f"{c['src']}:{c['name']}", t=t, entry=e,
                            pool=[best["lo"], best["hi"]], dist=round(dd, 1),
                            datr=round(datr, 2), covered=ok, respected=best["respected_left"],
                            status=best["status"]))
        print(f"{(c['src']+' '+str(c['name']))[:21]:<22}{dt.datetime.fromtimestamp(t,LX).strftime('%d/%m/%y %H:%M'):<15}{c['dir']:<6}{e:>9}{str([best['lo'],best['hi']]):>16}{dd:>7.1f}{datr:>6.2f}  {'COBERTO' if ok else 'fora'}{lowconf}"
              + (f" ({best['status']},resp={best['respected_left']})" if ok else ""))
    print(f"\nCOBERTURA: {cov}/{tot} ({100*cov//max(tot,1)}%) a <=0.5 ATR do pool")
    (HERE / "p1_results.json").write_text(json.dumps(dict(coverage=f"{cov}/{tot}", details=details), indent=1))
    print("gravado p1_results.json")


if __name__ == "__main__":
    main()
