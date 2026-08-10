#!/usr/bin/env python3
"""A1A2_FVG_LAB v2 — AMOSTRA CERTA: TODOS os disparos MB3 A1/A2 numa janela (não só fundos curados).
Replica FIELMENTE o detect() do runtime (a1a2_runtime.py) varrendo cada barra como barra-corrente do live:
perna HH[i-96,i-8] → fundo pós-topo (min low) → guarda escala 2.5×ATR → MB3 do módulo-mãe (causal). Cada
disparo é catalogado UMA vez (na sua barra de disparo ei==i). Outcome resolvido na série COMPLETA (SL-first
480b). Assim a distribuição de bounce cobre early→mid→late e INCLUI os mid-leg chases — o modo de falha que
a amostra GT curada não tinha. Depois: baseline + A(gate) + B(limite FVG) + C(etiqueta) + null + veredito §4.
Motor a1_causal_entry read-only. NÃO toca nada live. py3.9 stdlib."""
import sys, bisect, json, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, causal_entry, HORIZON
from fvg_localization_study import fvg_below_filled, resolve_limit, panel, r_of, BLK

# constantes idênticas ao runtime detect()
HH_WIN, HH_GAP, PB_WIN, PB_MIN_ATR, A2_MAX_ATR, SCALE_ATR = 96, 8, 24, 1.0, 2.0, 2.5
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def detect_at(S, i):
    """Réplica fiel de a1a2_runtime.detect() com a barra-corrente = i (só barras <= i). Devolve dict do
    disparo (ei absoluto, outcome resolvido na série completa) ou None. Cataloga só se ei==i (dedup natural)."""
    H, L, ATR, N = S["H"], S["L"], S["ATR"], S["N"]
    atr = ATR[i] or 5.0
    if i - HH_GAP <= 0:
        return None
    hh_i = max(range(max(0, i - HH_WIN), i - HH_GAP), key=lambda z: H[z])
    hh = H[hh_i]
    j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
    if i - j > PB_WIN:
        return None
    depth = (hh - L[j]) / atr
    if depth < PB_MIN_ATR:
        return None
    start = max(0, j - 3)
    # slice truncada em i (causal, como o live) para achar o 1º MB3 <= i
    Sx = {k: (v[start:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = causal_entry(Sx, j - start, kind="MB3")
    if not r:
        return None
    ei = r["ei"] + start
    if ei != i:                         # cataloga o disparo só na sua barra de disparo
        return None
    if r["R"] > SCALE_ATR * atr:        # guarda de escala 15M (idêntica ao runtime)
        return None
    # outcome REAL na série completa (SL-first) — usa o SL/entry já ancorados
    ent, sl = r["ent"], r["sl"]; rr = ent - sl; tgt = ent + 3 * rr; o = "OPEN"
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if L[m] <= sl: o = "LOSS"; break
        if H[m] >= tgt: o = "WIN"; break
    pb_low = L[j]
    bounce = 100 * (ent - pb_low) / (hh - pb_low) if hh > pb_low else 0.0
    has_fvg, gap = fvg_below_filled(S, j, ent, pb_low)
    layer = "A2" if depth <= A2_MAX_ATR else "A1"
    return dict(ei=ei, t=S["T"][ei], ent=ent, sl=sl, R=round(rr, 2), o=o, depth=round(depth, 2),
                layer=layer, bounce=bounce, fvg=has_fvg, gap=gap, pb_low=pb_low, hh=hh)


def main():
    S = load_series(BLK); N = S["N"]
    print(f"série RAW: {N} barras {ds(S['T'][0])} → {ds(S['T'][-1])}")
    fires = []
    for i in range(HH_WIN + 4, N):
        r = detect_at(S, i)
        if r:
            fires.append(r)
    got = [r for r in fires if r["o"] in ("WIN", "LOSS")]   # resolvidos
    print(f"{'='*80}\nA1A2 TODOS OS DISPAROS MB3 (janela completa) — {len(fires)} disparos, "
          f"{len(got)} resolvidos\n{'='*80}")

    # distribuição de bounce (a verificação-chave: tem mid-leg agora?)
    bs = sorted(r["bounce"] for r in got)
    print(f"\nbounce% distribuição: min {bs[0]:.0f} · p25 {bs[len(bs)//4]:.0f} · mediana "
          f"{st.median(bs):.0f} · p75 {bs[3*len(bs)//4]:.0f} · max {bs[-1]:.0f}")
    for lab, lo, hi in [("early ≤40", -999, 40), ("mid 40-60", 40, 60), ("late >60", 60, 999)]:
        sub = [r for r in got if lo < r["bounce"] <= hi] if lo != -999 else [r for r in got if r["bounce"] <= hi]
        if lab == "mid 40-60": sub = [r for r in got if 40 < r["bounce"] <= 60]
        if lab == "late >60": sub = [r for r in got if r["bounce"] > 60]
        if lab.startswith("early"): sub = [r for r in got if r["bounce"] <= 40]
        w = sum(1 for r in sub if r["o"] == "WIN"); l = sum(1 for r in sub if r["o"] == "LOSS")
        fv = sum(1 for r in sub if r["fvg"])
        wr = 100 * w / len(sub) if sub else 0
        print(f"  {lab:10}: n={len(sub):3d}  WIN {w:3d} / LOSS {l:3d}  (WR {wr:.0f}%)  · com-FVG {fv}")

    base_res = [r_of(r["o"]) for r in got]
    bp = panel(base_res)
    print(f"\n[BASELINE MB3 · todos]  {bp['s']}")
    print(f"  mediana bounce% {st.median(bs):.0f} · entries bounce>60 = {sum(1 for r in got if r['bounce']>60)} · "
          f"com FVG-fill {sum(1 for r in got if r['fvg'])}/{len(got)}")

    # C — FVG-fill como discriminador
    fs = [r for r in got if r["fvg"]]; nf = [r for r in got if not r["fvg"]]
    print(f"\n[C · FVG-fill discrimina?]")
    print(f"  FVG=SIM: {panel([r_of(r['o']) for r in fs])['s']}")
    print(f"  FVG=NÃO: {panel([r_of(r['o']) for r in nf])['s']}")
    # cruzamento localização×FVG nos mid/late (onde interessa)
    ml = [r for r in got if r["bounce"] > 40]
    if ml:
        mlf = [r for r in ml if r["fvg"]]; mln = [r for r in ml if not r["fvg"]]
        print(f"  [mid+late só] FVG=SIM: {panel([r_of(r['o']) for r in mlf])['s']}")
        print(f"  [mid+late só] FVG=NÃO: {panel([r_of(r['o']) for r in mln])['s']}")

    # A — GATE
    passA = [r for r in got if r["bounce"] <= 50 or r["fvg"]]
    killedA = [r for r in got if r["o"] == "WIN" and not (r["bounce"] <= 50 or r["fvg"])]
    a_res = [r_of(r["o"]) for r in passA]
    ap = panel(a_res)
    print(f"\n[A · GATE bounce≤50 OU FVG]  passa {len(passA)}/{len(got)}  {ap['s']}")
    print(f"  winners mortos {len(killedA)} · mediana bounce {st.median([r['bounce'] for r in passA]):.0f} · "
          f"bounce>60 restantes {sum(1 for r in passA if r['bounce']>60)}")

    # B — LIMITE no FVG
    b_res = []; fills = expires = killedB = 0
    for r in got:
        if r["fvg"]:
            o, rr = resolve_limit(S, r["ei"], r["gap"][1], r["sl"])
            if o in ("WIN", "LOSS"): fills += 1; b_res.append(rr)
            else:
                expires += 1
                if r["o"] == "WIN": killedB += 1
        else:
            b_res.append(r_of(r["o"]))
    bpB = panel(b_res)
    print(f"\n[B · LIMITE no FVG]  {bpB['s']}")
    print(f"  FVG-signals {len(fs)} · fills {fills} · expires {expires} · winners perdidos por não-fill {killedB}")

    # NULL
    import random; random.seed(42); null = []
    # null: entrada aleatória +1..+48 após ei de cada disparo (mesmo SL/âncora)
    for r in got:
        base_i = r["ei"]
        k = min(N - 1, base_i)  # usa ei como âncora coerente
        kk = min(N - 1, k + random.randint(1, 48))
        ent = S["C"][kk]; sl = r["sl"]; rr = ent - sl
        if rr <= 0: continue
        tgt = ent + 3 * rr; o = "OPEN"
        for m in range(kk + 1, min(N, kk + HORIZON + 1)):
            if S["L"][m] <= sl: o = "LOSS"; break
            if S["H"][m] >= tgt: o = "WIN"; break
        if o in ("WIN", "LOSS"): null.append(r_of(o))
    print(f"\n[NULL entrada aleatória +1..48]  {panel(null)['s']}")

    # VEREDITO §4
    print(f"\n{'='*80}\nVEREDITO §4 (limiares congelados)\n{'='*80}")
    med_all = st.median([r["bounce"] for r in got])
    c1A = len(killedA) <= 1
    c2A = (med_all - st.median([r["bounce"] for r in passA])) >= 15 and sum(1 for r in passA if r["bounce"]>60) <= 1
    c3A = ap["sumR"] >= bp["sumR"] - 1e-9 and (ap["rdd"] >= bp["rdd"] - 1e-9 or ap["rdd"] == float("inf"))
    print(f"  Opção A: {'PASS' if (c1A and c2A and c3A) else 'FAIL'} | mata≤1={c1A}({len(killedA)}) · "
          f"loc(cai≥15 & >60≤1)={c2A} · agregado≥base={c3A} (sumR {ap['sumR']:+.1f} vs {bp['sumR']:+.1f})")
    c1B = killedB <= 1
    c3B = bpB["sumR"] >= bp["sumR"] - 1e-9 and (bpB["rdd"] >= bp["rdd"] - 1e-9 or bpB["rdd"] == float("inf"))
    print(f"  Opção B: {'PASS' if (c1B and c3B) else 'FAIL'} | mata≤1={c1B}({killedB}) · "
          f"agregado≥base={c3B} (sumR {bpB['sumR']:+.1f} vs {bp['sumR']:+.1f})")
    print("\n  Chave: se agora HÁ mid/late no painel, o teste é INFORMATIVO. Comparar WR early vs mid/late e")
    print("  se FVG discrimina DENTRO dos mid/late. PASS → prereg forward, nunca edição live directa.")


if __name__ == "__main__":
    main()
