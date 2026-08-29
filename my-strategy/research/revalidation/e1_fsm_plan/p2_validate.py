#!/usr/bin/env python3
"""P2 GATE — o detetor de inducement marca, em >=80% dos casos P0 LONG datados, um inducement de
BUYERS com status OPEN/RESOLVED-recente no instante da entrada, cuja ORIGEM (stops dos induzidos)
esteja na região do pool da entrada (é essa liquidez que o sweep caça). Caso-a-caso (regra Cris:
nunca julgar sem detalhamento). py3.9 stdlib."""
import json
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import raw_reader as RR  # noqa: E402
import lm_inducement as LI  # noqa: E402
import liquidity_map as LM  # noqa: E402
LX = dt.timezone(dt.timedelta(hours=1))
WIN = 400            # mesma janela do P1


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
    seen = {}
    for c in sorted(dated, key=lambda x: x["t"]):
        k = (round(c["entry"], 1), dt.datetime.fromtimestamp(c["t"], dt.timezone.utc).date())
        if k not in seen:
            seen[k] = c
    dated = list(seen.values())
    longs = [c for c in dated if c["dir"] == "LONG"]
    print(f"casos LONG distintos datados: {len(longs)}")
    print(f"{'caso':<20}{'quando':<15}{'entry':>9}  inducement@entrada")
    ok = tot = 0
    det = []
    for c in longs:
        t, e = c["t"], c["entry"]
        src = raw_rows if t <= raw_end else store_rows
        upto = [b for b in src if b["t"] <= t][-WIN:]
        if len(upto) < 100:
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20} SEM-BARRAS")
            continue
        H = [b["h"] for b in upto]; L = [b["l"] for b in upto]; C = [b["c"] for b in upto]
        atr = LM._atr(upto)
        evs = LI.inducements(H, L, C)
        # candidato de inducement válido p/ LONG: BUYERS induced, origem <= entry + 1 ATR (stops na
        # região abaixo/na entrada = a liquidez que o sweep da entrada caça); estado OPEN no fim da
        # janela OU resolvido nas últimas 12 barras (o trap a completar É o momento da entrada)
        good = [ev for ev in evs if ev["kind"] == "BUYERS" and ev.get("origin") is not None
                and ev["origin"] <= e + 1.0 * atr
                and (ev["status"] == "OPEN" or ev.get("resolved_idx", -99) >= len(upto) - 12)]
        hit = bool(good)
        ok += hit; tot += 1
        best = max(good, key=lambda ev: ev["t_idx"]) if good else None
        det.append(dict(case=f"{c['src']}:{c['name']}", t=t, entry=e, hit=hit,
                        ind=None if not best else dict(broken=best["broken_extreme"],
                                                       origin=best["origin"], status=best["status"])))
        when = dt.datetime.fromtimestamp(t, LX).strftime("%d/%m/%y %H:%M")
        if best:
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20}{when:<15}{e:>9}  SIM: rompeu {best['broken_extreme']:.1f} → buyers presos, stops sob {best['origin']:.1f} ({best['status']})")
        else:
            n_open = sum(1 for ev in evs if ev['status'] == 'OPEN' and ev['kind'] == 'BUYERS')
            print(f"{(c['src']+':'+str(c['name']))[:19]:<20}{when:<15}{e:>9}  NÃO (buyers-induced OPEN na janela: {n_open}, nenhum com origem na região)")
    print(f"\nGATE P2: {ok}/{tot} ({100*ok//max(tot,1)}%) — alvo >=80%")
    (HERE / "p2_results.json").write_text(json.dumps(dict(gate=f"{ok}/{tot}", details=det), indent=1))
    print("gravado p2_results.json")


if __name__ == "__main__":
    main()
