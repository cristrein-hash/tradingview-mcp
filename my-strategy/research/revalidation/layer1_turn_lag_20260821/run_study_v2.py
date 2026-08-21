#!/usr/bin/env python3
"""LAYER1 TURN-LAG v2 — RE-RUN exigido pelo DA (harness fiel; prereg 80d10d3 mantém-se).
Correções: (a) variante = MOTOR REAL COMPLETO via patch de source só da linha rev_ref (RANGE +
min_bear_age + enter_range intactos), P1 byte-a-byte de verdade; (b) GT = viragens persistentes do
próprio motor real + comparação PAREADA por evento; (c) gate falsos-flips contra baseline REAL (=0);
(d) null redesenhado = jitter do floor de T1 (floors aleatórios de igual alcance médio) medindo
EXCESSO de falsos-flips e ganho de lag. py3.9 stdlib. Zero escrita fora deste diretório."""
import inspect
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
REV_LINE = "        rev_ref = sw_high if (bull_rev_swing and sw_high is not None) else prot_high\n"


def setup():
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]


def make_variant(repl_line):
    """build_layer1 REAL com APENAS a linha rev_ref substituída (source-patch; resto byte-idêntico)."""
    src = inspect.getsource(M.build_layer1)
    assert REV_LINE in src, "linha rev_ref não encontrada — motor mudou, HARD_STOP"
    src2 = src.replace(REV_LINE, repl_line)
    assert (src2 != src) or (repl_line == REV_LINE)   # identidade permitida (P1)
    ns = dict(M.__dict__)
    exec(src2, ns)                       # define build_layer1 patchado no namespace do módulo
    return ns["build_layer1"]


T1_LINE = ("        _fl = (min(L[i-252:i+1]) * (1 + ru_bull/100))\n"
           "        rev_ref = (min(sw_high, max(prot_high, _fl)) if (bull_rev_swing and sw_high is not None) else prot_high)\n")


def null_line(mult):
    return ("        _fl = (min(L[i-252:i+1]) * (1 + %.6f))\n"
            "        rev_ref = (min(sw_high, max(prot_high, _fl)) if (bull_rev_swing and sw_high is not None) else prot_high)\n" % mult)


def transitions(lab):
    """Viragens PERSISTENTES do label (BEAR->BULL e BULL->BEAR, atravessando RANGE): estado efetivo =
    último não-RANGE. Devolve [(i, from, to)]."""
    eff = None; out = []
    for i, s in enumerate(lab):
        if s == "RANGE":
            continue
        if eff is not None and s != eff:
            out.append((i, eff, s))
        eff = s
    return out


def false_flips(tr, days=5):
    n = 0
    for j in range(len(tr) - 1):
        if tr[j + 1][0] - tr[j][0] <= days and tr[j + 1][2] == tr[j][1]:
            n += 1
    return n


def main():
    setup()
    T, C = M.T, M.C
    yr = lambda i: dt.datetime.fromtimestamp(T[i], dt.timezone.utc).year
    dstr = lambda i: dt.datetime.fromtimestamp(T[i], dt.timezone.utc).strftime("%Y-%m-%d")

    # ===== P1: paridade — variante com a MESMA linha reproduz o real byte-a-byte =====
    base_fn = make_variant(REV_LINE)
    real = M.build_layer1()
    same = base_fn()
    assert same == real, "P1 FAIL: source-patch identidade não reproduz — HARD_STOP"
    print(f"P1 PASS: harness reproduz o motor real byte-a-byte ({len(real)} labels)")
    tr_base = transitions(real)
    ff_base = false_flips(tr_base)
    ups_base = [t for t in tr_base if t[2] == "BULL"]
    print(f"base REAL: {len(tr_base)} viragens persistentes · {len(ups_base)} p/ BULL · falsos-flips {ff_base}")

    # ===== P2: GT = viragens do próprio motor (persistentes) — pareado por evento =====
    # Para cada viragem->BULL do base, o EVENTO é o fundo real: mínimo de C nos 90d antes do flip.
    events = []
    for i, a, b in ups_base:
        j0 = max(0, i - 90)
        bot = min(range(j0, i + 1), key=lambda k: C[k])
        events.append(dict(flip_i=i, bottom_i=bot, lag_base=i - bot, year=yr(i), date=dstr(i)))
    print(f"P2: {len(events)} eventos BULL (fundo real = min 90d pré-flip) · lag base mediano "
          f"{sorted(e['lag_base'] for e in events)[len(events)//2]}d")

    # ===== P3: T1 no motor real =====
    t1_fn = make_variant(T1_LINE)
    lab_t1 = t1_fn()
    tr_t1 = transitions(lab_t1)
    ff_t1 = false_flips(tr_t1)
    ups_t1 = [t for t in tr_t1 if t[2] == "BULL"]
    # onsets BEAR preservados? (todas as viragens ->BEAR do base no mesmo dia na T1)
    dns_base = {i for i, a, b in tr_base if b == "BEAR"}
    dns_t1 = {i for i, a, b in tr_t1 if b == "BEAR"}
    onsets_kept = dns_base <= dns_t1 or dns_base == dns_t1
    # pareado: para cada evento do base, 1º flip->BULL da T1 em [bottom_i, flip_i+10]
    paired = []
    for e in events:
        cand = [i for i, a, b in ups_t1 if e["bottom_i"] <= i <= e["flip_i"] + 10]
        lag_t1 = (cand[0] - e["bottom_i"]) if cand else None
        paired.append({**e, "lag_t1": lag_t1})
    ok = [p for p in paired if p["lag_t1"] is not None]
    gains = [p["lag_base"] - p["lag_t1"] for p in ok]
    better = sum(1 for g in gains if g > 0); worse = sum(1 for g in gains if g < 0)
    med_gain = sorted(gains)[len(gains) // 2] if gains else None
    print(f"P3 T1: viragens {len(tr_t1)} · falsos {ff_t1} (base {ff_base}) · onsetsBEAR kept {onsets_kept}")
    print(f"   pareado n={len(ok)}: melhor {better} · pior {worse} · ganho mediano {med_gain}d")
    ex26 = [p["lag_base"] - p["lag_t1"] for p in ok if p["year"] < 2026]
    print(f"   ex-2026 (n={len(ex26)}): ganho mediano {sorted(ex26)[len(ex26)//2] if ex26 else None}d "
          f"· melhor {sum(1 for g in ex26 if g>0)} · pior {sum(1 for g in ex26 if g<0)}")
    for p in paired:
        print(f"   {p['date']} lag base {p['lag_base']}d -> T1 {p['lag_t1']}d")
    print(f"   label hoje: base {real[-1]} · T1 {lab_t1[-1]} (descritivo, não pontua)")

    # ===== P4: null = floors aleatórios de igual alcance (jitter do multiplicador) =====
    rnd = random.Random(SEED)
    null_stats = []
    for _ in range(60):                                  # 60 réplicas (cada uma corre o motor completo)
        mult = rnd.uniform(0.02, 0.30)                   # floor entre +2% e +30% do low252 (T1 = 12%)
        fn = make_variant(null_line(mult))
        labn = fn()
        trn = transitions(labn)
        ffn = false_flips(trn)
        upsn = [t for t in trn if t[2] == "BULL"]
        gs = []
        for e in events:
            cand = [i for i, a, b in upsn if e["bottom_i"] <= i <= e["flip_i"] + 10]
            if cand: gs.append(e["lag_base"] - (cand[0] - e["bottom_i"]))
        null_stats.append(dict(mult=round(mult, 3), ff=ffn,
                               med_gain=sorted(gs)[len(gs) // 2] if gs else None, n=len(gs)))
    ff_excess_null = sorted(x["ff"] - ff_base for x in null_stats)
    t1_ff_excess = ff_t1 - ff_base
    pct_null_ff_le = sum(1 for x in null_stats if (x["ff"] - ff_base) <= t1_ff_excess) / len(null_stats)
    gains_null = [x["med_gain"] for x in null_stats if x["med_gain"] is not None]
    pct_null_gain_ge = sum(1 for g in gains_null if g >= (med_gain or 0)) / max(1, len(gains_null))
    print(f"P4 null (60 floors aleatórios 2-30%): excesso-ff T1 {t1_ff_excess} · "
          f"null excesso-ff mediano {ff_excess_null[len(ff_excess_null)//2]} · "
          f"%null com ff<=T1 {pct_null_ff_le:.2f} · %null com ganho>=T1 {pct_null_gain_ge:.2f}")

    (OUT / "results_v2_summary.json").write_text(json.dumps(dict(
        p1="byte-exact PASS",
        base=dict(transicoes=len(tr_base), ups=len(ups_base), ff=ff_base),
        t1=dict(transicoes=len(tr_t1), ff=ff_t1, onsets_kept=onsets_kept,
                paired_n=len(ok), better=better, worse=worse, med_gain_d=med_gain,
                ex2026_med_gain=sorted(ex26)[len(ex26)//2] if ex26 else None,
                label_hoje=lab_t1[-1]),
        paired=[{k: p[k] for k in ("date", "lag_base", "lag_t1", "year")} for p in paired],
        null=dict(reps=len(null_stats), t1_ff_excess=t1_ff_excess,
                  pct_null_ff_le=round(pct_null_ff_le, 2), pct_null_gain_ge=round(pct_null_gain_ge, 2))),
        indent=1))
    print("gravado results_v2_summary.json")


if __name__ == "__main__":
    main()
