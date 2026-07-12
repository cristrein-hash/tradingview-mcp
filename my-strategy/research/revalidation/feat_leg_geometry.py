#!/usr/bin/env python3
"""FAMÍLIA leg_geometry — geometria PROPORCIONAL das pernas do zigzag causal (R2.zigzag).
Ortogonal a deslocamento e a contagem HH/HL (já refutada). Mede, no instante t (close-only,
pivots com confirmed_at <= t, nunca revistos):
  - retr = |perna menor| / |perna maior| entre as DUAS últimas pernas confirmadas (tamanhos em ATR)
  - direção = direção da última perna impulsiva (= a perna maior das duas)
  - variante _dur: exige que a perna impulsiva tenha VELOCIDADE (ATR/barra) > perna corretiva
Regra: retr <= RETR_TREND -> trend na direção da perna maior; retr >= RETR_RANGE -> RANGE;
zona intermédia -> carry (mantém rótulo anterior; init RANGE). Zero repaint.
IN-SAMPLE ONLY (t < 2023-01-01). Grelha FECHADA de 8 configs declarada abaixo. SEM P&L."""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
import gt_pivot_structural_harness as R1
import gt_pivot_structural_harness_r2 as R2

# ===================== GRELHA FECHADA (declarada ANTES de qualquer resultado) =====================
SPLIT = 1672531200  # 2023-01-01 UTC — PROIBIDO olhar métricas com t >= SPLIT
ZZ_R = [4, 6]                                   # escala do zigzag (R·ATR14_4H)
RETR_PAIRS = [(0.50, 0.80), (0.62, 1.00)]       # (RETR_TREND, RETR_RANGE)
USE_DUR = [False, True]                         # exigir velocidade impulsiva > corretiva
GAP_MODE = "carry"                              # zona intermédia mantém rótulo anterior (fixo)
CONFIGS = [{"R": R, "retr_trend": rt, "retr_range": rr, "use_dur": ud}
           for R in ZZ_R for (rt, rr) in RETR_PAIRS for ud in USE_DUR]  # 2*2*2 = 8
# ==================================================================================================

TS4 = R1.TS4
BAR_S = R1.BAR_S


def legs_from_pivots(hi, lo):
    """Sequência cronológica (por confirmed_at) de pivots intercalados -> pernas confirmadas.
    Cada perna: (t_conf_fim, size_atr_signed, dur_bars). size em ATR do pivô final."""
    piv = sorted([(t, p, a, +1) for (t, p, a) in hi] + [(t, p, a, -1) for (t, p, a) in lo])
    legs = []
    for (t0, p0, a0, s0), (t1, p1, a1, s1) in zip(piv, piv[1:]):
        atr = a1 or a0 or 5.0
        size = (p1 - p0) / atr
        dur = max((t1 - t0) / BAR_S, 1.0)
        legs.append((t1, size, dur))
    return legs


def label_series(legs, retr_trend, retr_range, use_dur):
    """Rótulo por índice de TS4. No t usa só pernas com t_conf_fim <= t (barras fechadas)."""
    labs = []
    cur = "RANGE"
    j = 0  # nº de pernas com t_conf <= t
    n_legs = len(legs)
    for t in TS4:
        while j < n_legs and legs[j][0] <= t:
            j += 1
        if j >= 2:
            _, szA, durA = legs[j - 2]
            _, szB, durB = legs[j - 1]
            aA, aB = abs(szA), abs(szB)
            if aB >= aA:
                big_sz, big_dur, small_sz, small_dur = szB, durB, aA, durA
            else:
                big_sz, big_dur, small_sz, small_dur = szA, durA, aB, durB
            big = abs(big_sz)
            retr = small_sz / big if big > 0 else 1.0
            if retr <= retr_trend:
                ok = True
                if use_dur:
                    vel_big = big / max(big_dur, 1.0)
                    vel_small = small_sz / max(small_dur, 1.0)
                    ok = vel_big > vel_small
                if ok:
                    cur = "BULL" if big_sz > 0 else "BEAR"
                # se velocidade falha: carry (zona ambígua)
            elif retr >= retr_range:
                cur = "RANGE"
            # zona intermédia: carry
        labs.append(cur)
    return labs


def main():
    sc_in = [(t, g) for t, g in R1.SCOPE if t < SPLIT]
    zz_cache = {R: legs_from_pivots(*R2.zigzag(R)) for R in ZZ_R}
    out = {"family": "leg_geometry", "configs": []}
    report = []
    for ci, cfg in enumerate(CONFIGS, 1):
        legs = zz_cache[cfg["R"]]
        labs = label_series(legs, cfg["retr_trend"], cfg["retr_range"], cfg["use_dur"])
        fn = lambda t, _l=labs: _l[R1.T2I[t]]
        s_in = R1.score_fn(fn, sc_in)
        cid = f"c{ci}"
        out["configs"].append({"id": cid, "params": cfg, "labels": labs})
        report.append((cid, cfg, s_in))
        print(f"{cid} R={cfg['R']} retr<={cfg['retr_trend']} range>={cfg['retr_range']} "
              f"dur={cfg['use_dur']} | IN bal={s_in['bal']:5.1f} acc={s_in['acc']:5.1f} "
              f"recall B/Be/R={s_in['recall']['BULL']}/{s_in['recall']['BEAR']}/{s_in['recall']['RANGE']}")
    path = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/results/feat_leg_geometry_labels.json"
    json.dump(out, open(path, "w"))
    best = max(report, key=lambda r: r[2]["bal"])
    print(f"\nBEST IN-SAMPLE: {best[0]} bal={best[2]['bal']} | labels -> {path}")
    return report


if __name__ == "__main__":
    main()
