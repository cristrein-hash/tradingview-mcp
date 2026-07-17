#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 4a — MAPA DE BUBBLES (union causal do RAW).
O indicador Market Order Bubbles mantém janela rolante (~19) por snapshot → a última linha perde ~99%.
Reconstrói o mapa COMPLETO por união das activations de TODAS as linhas de todos os blocos 15M.
Mapa de plots (validado Cp): BUY plot_0/2/4 = size1/2/3 · SELL plot_6/8/10 = size1/2/3.
Output: results/bubble_map.json = {time: {"b":[n1,n2,n3], "s":[n1,n2,n3]}} (por chart-bar-time).
A causalidade (buffer 3b) NÃO é aplicada aqui — é aplicada no s2b ao ler o mapa. py3.9 stdlib.
"""
import gzip, json, glob, time, sys
from pathlib import Path
from collections import defaultdict

RAW15 = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_*.jsonl.gz"
OUT = Path(__file__).resolve().parent / "results"; OUT.mkdir(exist_ok=True)
BUY = {"plot_0": 0, "plot_2": 1, "plot_4": 2}     # size 1/2/3
SELL = {"plot_6": 0, "plot_8": 1, "plot_10": 2}


def main():
    blocks = [f for f in sorted(glob.glob(RAW15)) if "superseded" not in f]
    if not blocks:
        sys.exit("FALHA: 0 blocos RAW 15M")
    print(f"blocos: {len(blocks)}", flush=True)
    # time -> [b1,b2,b3, s1,s2,s3] ; guardamos o MÁXIMO visto (a mesma bubble repete-se entre snapshots)
    mp = defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    for bi, f in enumerate(blocks):
        t0 = time.time(); nl = 0
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if '"pine_shapes_bubbles"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                nl += 1
                for st in (o.get("pine_shapes_bubbles") or []):
                    for a in (st.get("activations") or []):
                        t = a.get("time")
                        if t is None:
                            continue
                        row = mp[t]
                        for p, v in (a.get("shapes") or {}).items():
                            if p in BUY:
                                row[BUY[p]] = max(row[BUY[p]], int(v))
                            elif p in SELL:
                                row[3 + SELL[p]] = max(row[3 + SELL[p]], int(v))
        print(f"  [{bi+1}/{len(blocks)}] {Path(f).name[:38]} · {nl} linhas c/ bubbles · {time.time()-t0:.1f}s · mapa={len(mp)}", flush=True)
    # serializar
    out = {str(t): {"b": mp[t][:3], "s": mp[t][3:]} for t in sorted(mp)}
    fp = OUT / "bubble_map.json"
    json.dump(out, open(fp, "w"))
    # sumário
    import datetime as dt
    ts = sorted(int(t) for t in out)
    tb = sum(sum(v["b"]) for v in out.values()); tsl = sum(sum(v["s"]) for v in out.values())
    print(f"\nMAPA: {len(out)} chart-bars com bubbles · {dt.datetime.utcfromtimestamp(ts[0])} -> {dt.datetime.utcfromtimestamp(ts[-1])}")
    print(f"  total BUY weight (n*1): {tb} · total SELL weight: {tsl} · ratio buy/(buy+sell)={tb/(tb+tsl):.2f}")
    print(f"  -> {fp}")


if __name__ == "__main__":
    main()
