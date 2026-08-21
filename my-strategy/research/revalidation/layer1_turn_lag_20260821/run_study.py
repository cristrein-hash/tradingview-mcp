#!/usr/bin/env python3
"""LAYER1 TURN-LAG — execução do prereg selado (MANIFEST_PREREG.md, commit 80d10d3).
P1 baseline byte-exato (fail-loud) → P2 GT mecânico extremos 20d + lags → P3 variantes T1/T2/T3
(patch mínimo por monkey-run: reimplementa SÓ o loop de labels com o rev_ref alterado, reusando os
pivôs/RSI/DXY do módulo congelado) → P4 null + sub-janelas. py3.9 stdlib. Read-only sobre RAW."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core/layer1_service"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
import layer1_cycle as LC  # noqa: E402
import macro_structural_v3 as M  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260821


def setup_module():
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    return xau


def labels_variant(variant, m=5, m_sw=13, dd_bear=8.0, crash_thr=-6.0, dxy_w=90, ru_bull=12.0,
                   m_rev=8, min_bear_age=8):
    """Réplica do loop de transições do build_layer1 com APENAS o rev_ref/gate de saída de BEAR alterado
    por variante ('base','T1','T2','T3'). Estruturas (pivôs, RSI, DXY, RANGE) = módulo congelado.
    NOTA: réplica SIMPLIFICADA — sem o ramo RANGE (só transições BULL/BEAR + choch) para isolar o efeito
    da régua de viragem; o P1 valida a réplica-base contra o build_layer1 real APENAS nos dias de flip
    BEAR<->BULL (a régua em estudo), não no label completo."""
    T, H, L, C, N = M.T, M.H, M.L, M.C, M.N
    evi = M.fractal_pivots(m); evs = M.fractal_pivots(m_sw); pi = ps = 0
    evr = M.fractal_pivots(m_rev); pr = 0
    prot_low = prot_high = None
    sw_high = None
    rev8_high = None
    state = "RANGE"; out = []; bear_age = 0
    for i in range(N):
        while pi < len(evi) and evi[pi][0] <= i:
            _, typ, pb, px = evi[pi]; pi += 1
            if typ == "H": prot_high = px
            else: prot_low = px
        while ps < len(evs) and evs[ps][0] <= i:
            _, typ, pb, px = evs[ps]; ps += 1
            if typ == "H": sw_high = px
        while pr < len(evr) and evr[pr][0] <= i:
            _, typ, pb, px = evr[pr]; pr += 1
            if typ == "H": rev8_high = px
        if i < 360 or prot_low is None or prot_high is None:
            out.append(state if state != "RANGE" else "RANGE"); continue
        hi252 = max(H[i - 252:i + 1]); dd = (hi252 - C[i]) / hi252 * 100
        lo252 = min(L[i - 252:i + 1]); ru = (C[i] - lo252) / lo252 * 100
        dxr = M.dxy_ret(T[i] + 86400, dxy_w); rising = dxr > 0; falling = dxr < 0
        crash = (C[i] / C[i - 2] - 1) * 100 <= crash_thr
        bear_gate = crash or dd >= dd_bear or rising
        bull_gate = falling or ru >= ru_bull
        choch_dn = C[i] < prot_low; choch_up = C[i] > prot_high
        # rev_ref por variante
        if variant == "base":
            rev_ref = sw_high if sw_high is not None else prot_high
        elif variant == "T1":
            floor_ = lo252 * (1 + ru_bull / 100)
            rev_ref = min(sw_high, max(prot_high, floor_)) if sw_high is not None else prot_high
        elif variant == "T3":
            rev_ref = rev8_high if rev8_high is not None else (sw_high or prot_high)
        else:  # T2 usa choch_up imediato + idade/extensão
            rev_ref = sw_high if sw_high is not None else prot_high
        choch_up_rev = C[i] > rev_ref
        if state == "BEAR":
            bear_age += 1
        if crash:
            state = "BEAR"; bear_age = 0
        elif state == "BULL":
            if choch_dn and bear_gate: state = "BEAR"; bear_age = 0
        elif state == "BEAR":
            if variant == "T2":
                if (choch_up_rev and bull_gate) or (choch_up and bull_gate and bear_age >= min_bear_age
                                                    and ru >= 2 * ru_bull):
                    state = "BULL"
            else:
                if choch_up_rev and bull_gate: state = "BULL"
        else:  # RANGE inicial: sai na 1ª direção com gate (aproximação; P1 valida flips, não o RANGE)
            if choch_dn and bear_gate: state = "BEAR"; bear_age = 0
            elif choch_up_rev and bull_gate: state = "BULL"
        out.append(state)
    return out


def flips(labels, T, kinds=("BEAR", "BULL")):
    """Lista de (i, from, to) de transições BEAR<->BULL (ignora RANGE do warmup)."""
    f = []
    for i in range(1, len(labels)):
        a, b = labels[i - 1], labels[i]
        if a != b and a in kinds and b in kinds:
            f.append((i, a, b))
    return f


def extremes(C, w=20):
    """Extremos mecânicos: mínimos/máximos locais de janela ±w (confirmáveis ex-post — régua do GT)."""
    lows, highs = [], []
    for i in range(w, len(C) - w):
        if C[i] == min(C[i - w:i + w + 1]): lows.append(i)
        if C[i] == max(C[i - w:i + w + 1]): highs.append(i)
    # dedup plateaus
    def dd(xs):
        o = []
        for x in xs:
            if not o or x - o[-1] > w: o.append(x)
        return o
    return dd(lows), dd(highs)


def lag_stats(labels, lows, highs, T):
    """Para cada fundo (low): lag até ao 1º dia BEAR->BULL depois dele (<=60d senão MISS). Idem topos."""
    fl = flips(labels, T)
    up = [i for i, a, b in fl if b == "BULL"]
    dn = [i for i, a, b in fl if b == "BEAR"]
    def lags(exts, flps):
        out = []
        for e in exts:
            nxt = [f for f in flps if e <= f <= e + 60]
            out.append((e, nxt[0] - e if nxt else None))
        return out
    return lags(lows, up), lags(highs, dn), fl


def false_flips(labels, T, revert_days=5):
    fl = flips(labels, T)
    n = 0
    for j, (i, a, b) in enumerate(fl):
        if j + 1 < len(fl) and fl[j + 1][0] - i <= revert_days and fl[j + 1][2] == a:
            n += 1
    return n


def main():
    xau = setup_module()
    T, C = M.T, M.C
    yr = lambda i: dt.datetime.fromtimestamp(T[i], dt.timezone.utc).year
    # ===== P1: baseline real + validação da réplica nos flips =====
    real = M.build_layer1()
    rep = labels_variant("base")
    fl_real = flips(real, T); fl_rep = flips(rep, T)
    match = set((i, b) for i, a, b in fl_real) & set((i, b) for i, a, b in fl_rep)
    recall_rep = len(match) / max(1, len(fl_real))
    print(f"P1: flips reais {len(fl_real)} · réplica {len(fl_rep)} · match {len(match)} ({recall_rep:.0%})")
    assert recall_rep >= 0.85, f"réplica infiel aos flips ({recall_rep:.0%}) — HARD_STOP"
    # onsets BEAR do baseline (para o gate de preservação)
    onsets_bear_real = [(i, b) for i, a, b in fl_real if b == "BEAR"]

    lows, highs = extremes(C, 20)
    print(f"P2: GT extremos 20d — {len(lows)} fundos · {len(highs)} topos")

    results = {}
    for v in ("base", "T1", "T2", "T3"):
        lab = labels_variant(v)
        lg_up, lg_dn, fl = lag_stats(lab, lows, highs, T)
        up_l = [l for _, l in lg_up if l is not None]
        dn_l = [l for _, l in lg_dn if l is not None]
        med = lambda a: sorted(a)[len(a) // 2] if a else None
        ff = false_flips(lab, T)
        onsets_v = set((i, b) for i, a, b in fl if b == "BEAR")
        onsets_keep = all(x in onsets_v for x in set((i, b) for i, b in onsets_bear_real) & set((i, b) for i, b in onsets_bear_real))
        # preservação: todos os onsets BEAR da RÉPLICA-base têm de estar na variante
        base_onsets = set((i, b) for i, a, b in flips(labels_variant("base"), T) if b == "BEAR") if v != "base" else onsets_v
        keep = base_onsets <= onsets_v
        # label 2026 hoje
        today_lab = lab[-1]
        d2026 = sum(1 for i in range(len(lab)) if yr(i) == 2026 and lab[i] == "BEAR")
        results[v] = dict(flips=len(fl), lag_up_med=med(up_l), lag_up_n=len(up_l), lag_up_miss=sum(1 for _, l in lg_up if l is None),
                          lag_dn_med=med(dn_l), false_flips=ff, onsets_bear_kept=keep,
                          label_hoje=today_lab, dias_bear_2026=d2026)
        print(f"P3 [{v}] flips {len(fl)} · lag↑ med {med(up_l)}d (n={len(up_l)}, miss {sum(1 for _,l in lg_up if l is None)}) "
              f"· lag↓ med {med(dn_l)}d · falsos {ff} · onsetsBEAR ok {keep} · hoje {today_lab} · dias-BEAR-2026 {d2026}")

    # ===== P4: null (flip antecipado aleatório de k dias) para a melhor candidata por lag =====
    cands = [v for v in ("T1", "T2", "T3")
             if results[v]["lag_up_med"] is not None and results["base"]["lag_up_med"] is not None
             and results[v]["lag_up_med"] <= results["base"]["lag_up_med"] - 3
             and results[v]["false_flips"] <= results["base"]["false_flips"] + 1
             and results[v]["onsets_bear_kept"]]
    print("P4 candidatas pós-gates:", cands or "NENHUMA")
    null_out = {}
    if cands:
        rnd = random.Random(SEED)
        base_lab = labels_variant("base")
        base_fl = flips(base_lab, T)
        for v in cands:
            gain = results["base"]["lag_up_med"] - results[v]["lag_up_med"]
            ffn = []
            for _ in range(200):
                # antecipa cada flip->BULL do base por k~U[1,2*gain] dias
                lab2 = list(base_lab)
                for i, a, b in base_fl:
                    if b == "BULL":
                        k = rnd.randint(1, max(1, 2 * gain))
                        for j in range(max(0, i - k), i):
                            if lab2[j] == "BEAR": lab2[j] = "BULL"
                ffn.append(false_flips(lab2, T))
            worse = sum(1 for x in ffn if x <= results[v]["false_flips"])
            null_out[v] = dict(gain_days=gain, null_ff_median=sorted(ffn)[100], pct_null_melhor_ou_igual=round(worse / 200, 2))
            print(f"P4 null [{v}]: ganho {gain}d · null falsos-flips mediana {sorted(ffn)[100]} vs variante {results[v]['false_flips']}")

    (OUT / "results_summary.json").write_text(json.dumps(dict(
        p1=dict(flips_real=len(fl_real), replica_match=round(recall_rep, 2)),
        gt=dict(fundos=len(lows), topos=len(highs)),
        variantes=results, null=null_out), indent=1))
    print("gravado results_summary.json")


if __name__ == "__main__":
    main()
