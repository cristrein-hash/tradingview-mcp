#!/usr/bin/env python3
"""DISTRIB SIGNATURE — execução do prereg selado 54cca07 + adenda (gates=referência, veredito=Cris).
Censo A1/A2 do detetor REAL (a1a2_runtime.detect barra-a-barra, RAW 15M canónico) → split pela
assinatura DISTRIB (V15/V1H) ativa no momento da entrada → painéis completos + null flag-aleatória.
Swing = fractal m=2 (declarado; único knob não selado no manifest — fixado ANTES de correr, sem sweep).
Progresso = maxH(2ª metade da janela) − maxH(1ª metade). py3.9 stdlib. SANITY_PROBE: read-only."""
import bisect
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402  (leitor canónico — hook raw_read_guard satisfeito)

OUT = Path(__file__).resolve().parent
SEED = 20260828
EP_GAP = 8            # unidade = episódio (gap 8 barras entre sinais)
HORIZON = 480
# params selados no manifest
FAIL_BARS = 8         # fecho de volta abaixo do high varrido em <=8 barras
ACCEPT_ATR = 0.5      # aceitação = fecho >= high_varrido + 0.5*ATR
MIN_CAPT = 2          # capturas falhadas mínimas
PROG_ATR = 1.0        # progresso líquido dos highs < 1.0*ATR
K15, K1H = 96, 24     # janelas 24h
M_SW = 2              # fractal do swing (declarado acima)
NULL_REPS = 300


def build(rows):
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    N = len(rows); EMA = [None] * N; ATR = [None] * N; ema = None; kE = 2 / 22; trs = []
    for i in range(N):
        ema = C[i] if ema is None else C[i] * kE + ema * (1 - kE); EMA[i] = ema
        if i > 0: trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    return dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)


def swing_highs(H, i0, i1):
    """Índices p em [i0,i1] com fractal high m=M_SW confirmado DENTRO do intervalo (p+M_SW<=i1)."""
    out = []
    for p in range(max(M_SW, i0), i1 - M_SW + 1):
        if H[p] == max(H[p - M_SW:p + M_SW + 1]):
            out.append(p)
    return out


def distrib_flag(H, C, atr, i, K):
    """Assinatura DISTRIB causal na barra i sobre a janela [i-K, i] (arrays H/C do TF em causa).
    d1: >=MIN_CAPT capturas de swing-high FALHADAS (rompe, fecha de volta <=FAIL_BARS, sem aceitação
        ACCEPT_ATR depois da captura ate i). d2: progresso maxH(2a metade)-maxH(1a metade) < PROG_ATR."""
    a = max(0, i - K)
    if i - a < K // 2 + M_SW * 2 + 2 or not atr:
        return False
    sws = swing_highs(H, a, i)
    fails = 0
    for p in sws:
        sh = H[p]
        b = next((x for x in range(p + M_SW, i + 1) if H[x] > sh), None)   # captura
        if b is None:
            continue
        back = next((x for x in range(b, min(i, b + FAIL_BARS) + 1) if C[x] < sh), None)
        if back is None:
            continue                                                       # não voltou = não falhou
        if any(C[x] >= sh + ACCEPT_ATR * atr for x in range(b, i + 1)):
            continue                                                       # houve aceitação
        fails += 1
    if fails < MIN_CAPT:
        return False
    mid = a + (i - a) // 2
    prog = max(H[mid:i + 1]) - max(H[a:mid + 1])
    return prog < PROG_ATR * atr


def outcome(S, k, ent, sl):
    """SL-first 3R, fill-bar conta (DA-fix herdado)."""
    tgt = ent + 3 * (ent - sl)
    for m in range(k + 1, min(S["N"], k + HORIZON)):
        if S["L"][m] <= sl: return -1.0
        if S["H"][m] >= tgt: return 3.0
    return 0.0


def panel(rlist, cost):
    n = len(rlist); w = sum(1 for r in rlist if r > 0)
    s = sum(r - cost for r in rlist)
    cum = peak = dd = 0.0; stk = mx = 0
    for r in rlist:
        cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
        stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
    return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build(rows)
    T, H, C, ATR = S["T"], S["H"], S["C"], S["ATR"]
    h1 = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl") if l.strip()]
    h1.sort(key=lambda x: x["t"])
    T1, H1, C1 = [b["t"] for b in h1], [b["h"] for b in h1], [b["c"] for b in h1]
    print(f"RAW 15M {S['N']} barras · RAW 1H {len(h1)} barras")

    # ===== censo do detetor REAL (episódios) =====
    import a1a2_runtime as RT
    sigs = []; last_i = -10**9
    for i in range(200, S["N"]):
        Sw = {k: (v[:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
        Sw["N"] = i + 1
        r, why = RT.detect(Sw)
        if not r or i - last_i < EP_GAP:
            continue
        last_i = i
        R = outcome(S, i, r["ent"], r["sl"])
        # assinaturas causais no momento do sinal
        v15 = distrib_flag(H, C, ATR[i], i, K15)
        j = bisect.bisect_right(T1, T[i]) - 1
        while j >= 0 and T1[j] + 3600 > T[i]:
            j -= 1                                        # só 1H FECHADAS
        v1h = distrib_flag(H1, C1, (ATR[i] or 5.0) * 2.0, j, K1H) if j > 0 else False
        half = dt.datetime.fromtimestamp(T[i], dt.timezone.utc)
        sigs.append(dict(i=i, layer=r["layer"], R=R, v15=v15, v1h=v1h,
                         half=f"{half.year}-H{1 if half.month <= 6 else 2}"))
    print(f"censo: {len(sigs)} episódios ({sum(1 for s in sigs if s['layer']=='A1')} A1 · "
          f"{sum(1 for s in sigs if s['layer']=='A2')} A2)")

    out = dict(n_sigs=len(sigs), variants={})
    for vn in ("v15", "v1h"):
        on = [s["R"] for s in sigs if s[vn]]
        off = [s["R"] for s in sigs if not s[vn]]
        freq = len(on) / len(sigs) if sigs else 0
        print(f"\n=== {vn.upper()} · ON {len(on)} ({freq:.0%}) vs OFF {len(off)} ===")
        blk = dict(freq=round(freq, 3), panels={})
        for c in (0.0, 0.2, 0.35):
            pon, poff = panel(on, c), panel(off, c)
            print(f"  custo {c}: ON {pon}")
            print(f"           OFF {poff}")
            blk["panels"][str(c)] = dict(on=pon, off=poff)
        hv = {}
        for s in sigs:
            hv.setdefault(s["half"], [0.0, 0.0])
            hv[s["half"]][0 if s[vn] else 1] += s["R"] - 0.2
        blk["halves_c02_on_off"] = {k: [round(a, 1), round(b, 1)] for k, (a, b) in sorted(hv.items())}
        print(f"  por-semestre c0.2 [ON, OFF]: {blk['halves_c02_on_off']}")
        # null: flag aleatória mesma frequência, 300 reps → distribuição do gap de WR (OFF-ON)
        real_gap = (panel(off, 0)["WR"] or 0) - (panel(on, 0)["WR"] or 0)
        ge = 0; gaps = []
        for _ in range(NULL_REPS):
            fl = [rnd.random() < freq for _ in sigs]
            ron = [s["R"] for s, f in zip(sigs, fl) if f]
            roff = [s["R"] for s, f in zip(sigs, fl) if not f]
            g = (panel(roff, 0)["WR"] or 0) - (panel(ron, 0)["WR"] or 0)
            gaps.append(g)
            if g >= real_gap: ge += 1
        gaps.sort()
        blk["null"] = dict(real_gap_wr=real_gap, p_ge=round(ge / NULL_REPS, 3),
                           null_gap_p95=gaps[int(0.95 * len(gaps))])
        print(f"  null: gap WR real {real_gap}pp · p(null>=real) {blk['null']['p_ge']} · p95 null {blk['null']['null_gap_p95']}pp")
        out["variants"][vn] = blk

    # jackknife por semestre (c0.2, sumR OFF-retido) para cada variante
    for vn in ("v15", "v1h"):
        halves = sorted({s["half"] for s in sigs})
        jk = {}
        for hx in halves:
            sub = [s for s in sigs if s["half"] != hx]
            jk[hx] = dict(on=round(sum(s["R"] - 0.2 for s in sub if s[vn]), 1),
                          off=round(sum(s["R"] - 0.2 for s in sub if not s[vn]), 1))
        out["variants"][vn]["jackknife_c02"] = jk
        print(f"\njackknife {vn} (c0.2 sem o semestre): {jk}")

    # descritivo (NÃO pontua): assinatura nos 8 sinais da semana 24-28/08
    wk = [json.loads(l) for l in open(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl") if l.strip()]
    wk0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()
    desc = []
    for r in wk:
        t = r.get("entry_t")
        if not t or t < wk0: continue
        i = next((x for x, tt in enumerate(T) if tt == t), None)
        if i is None: continue
        v15 = distrib_flag(H, C, ATR[i], i, K15)
        j = bisect.bisect_right(T1, t) - 1
        while j >= 0 and T1[j] + 3600 > t: j -= 1
        v1h = distrib_flag(H1, C1, (ATR[i] or 5.0) * 2.0, j, K1H) if j > 0 else False
        desc.append(dict(when=dt.datetime.fromtimestamp(t, dt.timezone(dt.timedelta(hours=1))).strftime("%a %d/%m %H:%M"),
                         v15=v15, v1h=v1h))
    out["week_descriptive"] = desc
    print(f"\nDESCRITIVO semana 24-28/08 (não pontua): {desc}")

    (OUT / "results_summary.json").write_text(json.dumps(out, indent=1))
    print("gravado results_summary.json")


if __name__ == "__main__":
    main()
