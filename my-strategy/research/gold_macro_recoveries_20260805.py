#!/usr/bin/env python3
"""APANHADO DAS RECUPERAÇÕES MACRO DO OURO (ordem Cris 2026-08-05 ~08:2x): grandes fundos de capitulação
1D (RAW HD 2012-2026) e o PADRÃO do recuo pós-recuperação — quanto devolve a 1ª perna antes de continuar.

Método (TRAJETÓRIA, multi-fator, descritivo — não é gate/separação):
  - Fundo maior = low mínimo de ±45 sessões, precedido de queda >=8% do pico das 90 sessões anteriores.
  - Perna 1 = rally do fundo até ao 1º topo local (max high antes do 1º pullback >=3% do running-max).
  - Recuo = profundidade do 1º pullback: % do preço, % da perna 1 (fib), duração em sessões,
    e se segurou acima do fundo. Continuação = fez novo high acima do topo da perna 1 depois?
RAW-first: /Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D. py3.9."""
import gzip, json, datetime as dt
from pathlib import Path

RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz")
STORE = Path(__file__).resolve().parents[1] / "core/bar_store/store/bars_1d.jsonl"


def load():
    bars = {}
    with gzip.open(RAW, "rt") as fh:
        for l in fh:
            i = l.find('"ohlcv":')
            if i < 0: continue
            s = l.find('[', i); e = l.find(']', s)
            try: arr = json.loads(l[s:e+1])
            except Exception: continue
            for b in arr:
                t = b.get("time")
                if t is None: continue
                if t not in bars:
                    bars[t] = [b["open"], b["high"], b["low"], b["close"]]
                else:
                    bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
    # extensão live (store 1d cobre 2026-05→08, o RAW pára 2026-05-25)
    try:
        for l in open(STORE):
            if not l.strip() or l[0] != "{": continue
            b = json.loads(l)
            if all(k in b for k in ("t", "o", "h", "l", "c")) and b["t"] not in bars:
                bars[b["t"]] = [b["o"], b["h"], b["l"], b["c"]]
    except Exception:
        pass
    T = sorted(bars)
    return T, [bars[t][1] for t in T], [bars[t][2] for t in T], [bars[t][3] for t in T]


def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")


def main():
    T, H, L, C = load()
    N = len(T)
    print(f"série 1D: {N} sessões, {ds(T[0])} → {ds(T[-1])}\n")
    # fundos maiores
    bottoms = []
    for i in range(45, N - 45):
        if L[i] != min(L[i-45:i+46]): continue
        peak = max(H[max(0, i-90):i])
        drop = (peak - L[i]) / peak * 100
        if drop < 8: continue
        bottoms.append((i, drop, peak))
    # dedup fundos a <30 sessões (fica o mais fundo)
    dedup = []
    for i, drop, peak in bottoms:
        if dedup and i - dedup[-1][0] < 30:
            if L[i] < L[dedup[-1][0]]: dedup[-1] = (i, drop, peak)
        else:
            dedup.append((i, drop, peak))
    print(f"{'fundo':<12}{'low':>8}{'queda%':>8} | {'perna1 topo':>12}{'+%':>7}{'sess':>5} | {'recuo%px':>9}{'%perna':>8}{'sess':>5} {'fundo2>fundo?':>14} {'continuou?':>11}")
    rows = []
    for i, drop, peak in dedup:
        lo = L[i]
        # perna 1: running-max dos highs até 1º pullback >=3%
        top_i = None; runmax = H[i]; runmax_i = i
        for k in range(i + 1, min(N, i + 250)):
            if H[k] > runmax: runmax, runmax_i = H[k], k
            if (runmax - L[k]) / runmax >= 0.03 and runmax_i > i:
                top_i = runmax_i; break
        if top_i is None: continue
        leg = runmax - lo
        # recuo: min low após o topo até novo high (ou 120 sessões)
        ret_lo = None; ret_i = None; cont = False
        for k in range(top_i + 1, min(N, top_i + 120)):
            if H[k] > runmax: cont = True; break
            if ret_lo is None or L[k] < ret_lo: ret_lo, ret_i = L[k], k
        if ret_lo is None: continue
        ret_px = (runmax - ret_lo) / runmax * 100
        ret_leg = (runmax - ret_lo) / leg * 100 if leg > 0 else 0
        held = ret_lo > lo
        rows.append((ret_leg, ret_px))
        print(f"{ds(T[i]):<12}{lo:>8.0f}{drop:>7.1f}% | {runmax:>8.0f} ({top_i-i:>3}s){(runmax-lo)/lo*100:>6.1f}%{'':>0} | "
              f"{ret_px:>8.1f}%{ret_leg:>7.0f}%{(ret_i-top_i) if ret_i else 0:>5} {'SIM' if held else 'NÃO':>14} {'SIM' if cont else '—':>11}")
    if rows:
        import statistics as st
        legs = [r[0] for r in rows]; pxs = [r[1] for r in rows]
        print(f"\nPADRÃO: recuo mediano = {st.median(legs):.0f}% da perna 1 (média {st.mean(legs):.0f}%, "
              f"min {min(legs):.0f}%, max {max(legs):.0f}%) · em preço: mediana {st.median(pxs):.1f}%")
        print(f"fundo do recuo segurou acima do fundo de capitulação em {sum(1 for r in dedup)} casos analisáveis (ver coluna)")


if __name__ == "__main__":
    main()
