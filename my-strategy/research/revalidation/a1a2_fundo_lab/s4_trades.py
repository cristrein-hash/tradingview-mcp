#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 5 — TRADES do fundo-detector com entry A1/A2, Set/2025 -> fim do RAW.
Detector = a assinatura como construída (bucket macro-BULL ∧ zzregion∈BOTTOM/MIDDLE ∧ reclaim≥medGT ∧
depth≥medGT). Para cada fundo detetado aplica o ENTRY APROVADO A1/A2 (a1_causal_entry.causal_entry MB3:
swing-low fractal confirmado -> 1ª MB3, SL=low-real do pullback−0.1ATR, alvo +3R, outcome SL-first 480b).
Thresholds medGT = in-sample (dos 32 GT) — demonstração, não validação. Também mostra variante SEM região
(refutada) = reclaim+depth. Painel completo (N·WR·sumR·avgR·DD·streak). RAW-first. Causal. py3.9 stdlib.
"""
import sys, csv, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC, causal_entry
sys.path.insert(0, str(HERE))
from s2b_seq_features import feats, blocks, BUCKET
from s3b_zigzag_region import zzleg_region
RES = HERE / "results"
WIN_START = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def panel(trades):
    """N·WR·sumR·avgR·maxDD·streak (usa R do entry; OPEN conta 0)."""
    rs = [t["R_out"] for t in trades if t["outcome"] in ("WIN", "LOSS")]
    if not rs:
        return "sem trades resolvidos"
    wr = 100 * sum(1 for t in trades if t["outcome"] == "WIN") / len(rs)
    sm = sum(rs); avg = sm / len(rs)
    cum = 0; peak = 0; dd = 0; cs = 0; mst = 0
    for r in rs:
        cum += r; peak = max(peak, cum); dd = min(dd, cum - peak)
        cs = cs + 1 if r < 0 else 0; mst = max(mst, cs)
    return f"N {len(rs)} · WR {wr:.0f}% · sumR {sm:+.1f} · avgR {avg:+.2f} · maxDD {dd:.1f} · streak-perde {mst}"


def main():
    S = load_series(blocks()); T, L, N = S["T"], S["L"], S["N"]
    tab = {}
    with open(RES / "a1a2_bucket_table.csv") as fh:
        for r in csv.DictReader(fh):
            tab[int(r["t"])] = (r["kind"], r["family_label"])
    # thresholds medGT (in-sample) — mesmos do s3b
    gt_rc = []; gt_dp = []
    for p in range(M_FRAC, N - M_FRAC):
        if not _is_swinglow(L, p, M_FRAC):
            continue
        info = tab.get(T[p])
        if not info or info[1] not in BUCKET or info[0] not in ("GT_A1", "GT_A2"):
            continue
        fv = feats(S, {}, p, "fix48")
        if fv:
            gt_rc.append(fv["reclaim"]); gt_dp.append(fv["depth"])
    med_rc = st.median(gt_rc); med_dp = st.median(gt_dp)
    print(f"thresholds medGT (in-sample): reclaim≥{med_rc:.2f} · depth≥{med_dp:.2f}")
    print(f"janela: {ds(WIN_START)} -> {ds(T[-1])} (fim do RAW; live pós-{ds(T[-1])} não coberto)\n")

    def collect(use_region):
        trades = []
        for p in range(M_FRAC, N - M_FRAC):
            if T[p] < WIN_START:
                continue
            if not _is_swinglow(L, p, M_FRAC):
                continue
            info = tab.get(T[p])
            if not info or info[1] not in BUCKET:
                continue
            fv = feats(S, {}, p, "fix48")
            if not fv:
                continue
            reg, pos = zzleg_region(int(T[p]), L[p])
            ok = fv["reclaim"] >= med_rc and fv["depth"] >= med_dp
            if use_region:
                ok = ok and reg in ("BOTTOM", "MIDDLE")
            if not ok:
                continue
            # DA-fix (2026-07-17): o fundo só é CONHECÍVEL em p+M_FRAC (fractal confirma + reclaim usa C[p+3]).
            # A janela de entrada tem de abrir em p+M_FRAC, não em p (senão entra antes de confirmar = leak).
            e = causal_entry(S, p + M_FRAC, "MB3")
            if not e:
                continue
            trades.append({"t": T[p], "date": ds(T[p]), "kind": info[0], "region": reg,
                           "depth": fv["depth"], "reclaim": fv["reclaim"], "entry": e["ent"],
                           "sl": e["sl"], "tgt": e["tgt"], "RATR": e["RATR"],
                           "outcome": e["o"], "R_out": (3.0 if e["o"] == "WIN" else (-1.0 if e["o"] == "LOSS" else 0.0)),
                           "bars": e["bars"]})
        return trades

    for label, ureg in [("DETECTOR desse jeito (região∈BOTTOM/MIDDLE + reclaim + depth)", True),
                        ("SEM região (reclaim + depth — região foi refutada)", False)]:
        tr = collect(ureg)
        print(f"\n{'='*78}\n{label}\n{'='*78}")
        print(f"{'#':>2} {'data':16} {'reg':7} {'kind':7} {'entry':>8} {'SL':>8} {'tgt':>8} {'RxATR':>5} {'out':4} {'bars':>4}")
        for i, t in enumerate(tr, 1):
            star = "★" if t["kind"] in ("GT_A1", "GT_A2") else " "
            print(f"{i:2d}{star}{t['date']:16} {t['region']:7} {t['kind']:7} {t['entry']:8.2f} {t['sl']:8.2f} "
                  f"{t['tgt']:8.2f} {t['RATR']:5.2f} {t['outcome']:4} {str(t['bars']):>4}")
        gt_hit = sum(1 for t in tr if t["kind"] in ("GT_A1", "GT_A2"))
        print(f"  PAINEL: {panel(tr)}")
        print(f"  (★ = coincide com fundo GT teu: {gt_hit}/{len(tr)})")
        # persistir
        fn = RES / ("a4_trades_" + ("region" if ureg else "noregion") + ".csv")
        with open(fn, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["date", "region", "kind", "entry", "sl", "tgt", "RATR", "outcome", "R_out", "bars"])
            for t in tr:
                w.writerow([t["date"], t["region"], t["kind"], t["entry"], t["sl"], t["tgt"], t["RATR"], t["outcome"], t["R_out"], t["bars"]])


if __name__ == "__main__":
    main()
