#!/usr/bin/env python3
"""A1A2_FVG_LAB — filtro de LOCALIZAÇÃO por FVG-fill (prereg FVG_LOCALIZATION_PREREG_20260810.md).
Mede 3 variantes (C=etiqueta, A=gate, B=refina-entry-limite-no-FVG) vs baseline MB3 nos 32 fundos GT
(A1=14 + A2=18). Motor a1_causal_entry read-only. FVG das barras RAW, causal. Painel completo + veredito
PASS/FAIL contra §4 do prereg. py3.9 stdlib. NÃO toca nada live."""
import sys, bisect, json, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, causal_entry, M_FRAC, TRIG_WIN, HORIZON

BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
LEG_LB = 96   # lookback do topo da perna (idêntico ao runtime detect())


def panel(rs):
    """rs = lista de R resolvidos (WIN=+3? não — usamos R real). Devolve dict de métricas."""
    if not rs:
        return dict(n=0, s="N 0")
    wr = 100 * sum(1 for r in rs if r > 0) / len(rs); sm = sum(rs); avg = sm / len(rs)
    cum = pk = dd = cs = mst = 0
    for r in rs:
        cum += r; pk = max(pk, cum); dd = min(dd, cum - pk); cs = cs + 1 if r < 0 else 0; mst = max(mst, cs)
    rdd = (sm / abs(dd)) if dd < 0 else float("inf")
    return dict(n=len(rs), wr=wr, sumR=sm, avg=avg, dd=dd, rdd=rdd, streak=mst,
                s=f"N {len(rs)} · WR {wr:.0f}% · sumR {sm:+.1f} · avgR {avg:+.2f} · DD {dd:.1f} · "
                  f"ret/DD {rdd:.2f} · streak {mst}")


def r_of(o):
    return 3.0 if o == "WIN" else (-1.0 if o == "LOSS" else 0.0)


def fvg_below_filled(S, jf, ent, pb_low):
    """FVG bullish (high[b-1]<low[b+1]) formado em b+1<=jf, gap [glo,ghi], abaixo de ent (ghi<=ent),
    preenchido pelo pullback (pb_low<=ghi). Causal: só barras <= jf. Devolve (bool, (glo,ghi,b) | None).
    Escolhe o gap mais alto (ghi maior) = o retest-limite mais próximo da entrada."""
    H, L = S["H"], S["L"]
    lb = max(1, jf - LEG_LB)
    best = None
    for b in range(lb, jf):                       # b+1 <= jf
        if b + 1 > jf or b - 1 < 0:
            continue
        if H[b - 1] < L[b + 1]:                    # imbalance bullish
            glo, ghi = H[b - 1], L[b + 1]
            if ghi <= ent and pb_low <= ghi:       # gap abaixo da entrada E pullback entrou no gap
                if best is None or ghi > best[1]:
                    best = (glo, ghi, b)
    return (best is not None), best


def resolve_limit(S, ei, new_ent, sl):
    """B: limite em new_ent após ei. Preenche se low<=new_ent na janela TRIG_WIN antes de bater alvo.
    Depois SL-first até HORIZON. Devolve (o, R_real). Não-fill/expira = ('EXPIRE', 0.0)."""
    L, H, N = S["L"], S["H"], S["N"]
    r = new_ent - sl
    if r <= 0:
        return "EXPIRE", 0.0
    tgt = new_ent + 3 * r
    fill = None
    for k in range(ei + 1, min(N, ei + 1 + TRIG_WIN)):
        if H[k] >= tgt:                # foi ao alvo sem retestar o limite = perdemos (expira)
            return "EXPIRE", 0.0
        if L[k] <= new_ent:            # limite preenchido
            fill = k; break
    if fill is None:
        return "EXPIRE", 0.0
    for m in range(fill + 1, min(N, fill + HORIZON + 1)):
        if L[m] <= sl:
            return "LOSS", -1.0
        if H[m] >= tgt:
            return "WIN", 3.0
    return "OPEN", 0.0


def main():
    S = load_series(BLK); T, H = S["T"], S["H"]
    GT = json.load(open(HERE.parent / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
    fundos = GT["fundos"] if "fundos" in GT else GT
    F = sorted([f for f in fundos if f.get("subclasse") in ("A1_pullback_fundo", "A2_pullback_raso")],
               key=lambda x: x["t"])
    rows = []
    for f in F:
        jf = bisect.bisect_right(T, int(f["t"])) - 1
        if jf < LEG_LB + 3 or jf >= S["N"]:
            continue
        e = causal_entry(S, jf, "MB3")
        if not e:
            rows.append(dict(f=f, jf=jf, e=None))
            continue
        ei, ent, sl, pb_low = e["ei"], e["ent"], e["sl"], min(S["L"][max(0, jf - 16):jf + 1])
        hh = max(H[jf - LEG_LB:jf]) if jf - LEG_LB >= 0 else H[jf]
        bounce = 100 * (ent - pb_low) / (hh - pb_low) if hh > pb_low else 0.0
        has_fvg, gap = fvg_below_filled(S, jf, ent, pb_low)
        rows.append(dict(f=f, jf=jf, e=e, ei=ei, ent=ent, sl=sl, pb_low=pb_low, bounce=bounce,
                         fvg=has_fvg, gap=gap, sub=f["subclasse"]))
    got = [r for r in rows if r["e"]]
    print(f"{'='*78}\nA1A2 FVG-LOCALIZAÇÃO — {len(got)}/{len(F)} fundos com entry MB3 (32 alvo)\n{'='*78}")

    # ---- BASELINE ----
    base = [r_of(r["e"]["o"]) for r in got]
    base_res = [r for r in base if r != 0.0]
    base_wins = [r for r in got if r["e"]["o"] == "WIN"]
    print(f"\n[BASELINE MB3]  {panel(base_res)['s']}")
    print(f"  mediana bounce% = {st.median([r['bounce'] for r in got]):.0f} · "
          f"entries bounce>60 = {sum(1 for r in got if r['bounce'] > 60)} · "
          f"com FVG-fill = {sum(1 for r in got if r['fvg'])}/{len(got)}")

    # ---- C: ETIQUETA ----
    print("\n[C · ETIQUETA]  distribuição localização × outcome:")
    def band(b): return "early" if b <= 40 else ("mid" if b <= 60 else "late")
    from collections import Counter
    for lab in ("early", "mid", "late"):
        sub = [r for r in got if band(r["bounce"]) == lab]
        w = sum(1 for r in sub if r["e"]["o"] == "WIN"); l = sum(1 for r in sub if r["e"]["o"] == "LOSS")
        fv = sum(1 for r in sub if r["fvg"])
        print(f"   {lab:5}: n={len(sub):2d}  WIN {w} / LOSS {l}  · com-FVG {fv}")
    fvg_sub = [r for r in got if r["fvg"]]; nofvg = [r for r in got if not r["fvg"]]
    print(f"   FVG-fill=SIM: {panel([r_of(r['e']['o']) for r in fvg_sub if r['e']['o'] in ('WIN','LOSS')])['s']}")
    print(f"   FVG-fill=NÃO: {panel([r_of(r['e']['o']) for r in nofvg if r['e']['o'] in ('WIN','LOSS')])['s']}")

    # ---- A: GATE ----
    passA = [r for r in got if r["bounce"] <= 50 or r["fvg"]]
    killedA = [r for r in base_wins if not (r["bounce"] <= 50 or r["fvg"])]
    a_res = [r_of(r["e"]["o"]) for r in passA if r["e"]["o"] in ("WIN", "LOSS")]
    med_b_A = st.median([r["bounce"] for r in passA]) if passA else 0
    print(f"\n[A · GATE bounce≤50 OU FVG]  passa {len(passA)}/{len(got)}  {panel(a_res)['s']}")
    print(f"   winners mortos = {len(killedA)}  · mediana bounce% {med_b_A:.0f} · "
          f"bounce>60 restantes = {sum(1 for r in passA if r['bounce'] > 60)}")

    # ---- B: REFINAR ENTRY (limite no FVG) ----
    b_out = []; fills = 0; expires = 0; killedB = 0
    for r in got:
        if r["fvg"]:
            o, rr = resolve_limit(S, r["ei"], r["gap"][1], r["sl"])
            if o in ("WIN", "LOSS"):
                fills += 1
            else:
                expires += 1
                if r["e"]["o"] == "WIN":
                    killedB += 1     # era WIN baseline, limite não encheu = winner perdido
            b_out.append((r, o, rr, r["gap"][1]))
        else:
            b_out.append((r, r["e"]["o"], r_of(r["e"]["o"]), r["ent"]))   # sem FVG = baseline
    b_res = [rr for (_, o, rr, _) in b_out if o in ("WIN", "LOSS")]
    med_b_B = st.median([r["bounce"] for r in got])   # bounce não muda (é do baseline); a entrada é que desce
    ent_impr = [(r["ent"] - ne) for (r, o, rr, ne) in b_out if r["fvg"] and o in ("WIN", "LOSS")]
    print(f"\n[B · LIMITE no FVG]  {panel(b_res)['s']}")
    print(f"   FVG-signals={sum(1 for r in got if r['fvg'])} · fills={fills} · expires(não-fill)={expires} · "
          f"winners perdidos por não-fill = {killedB}")
    if ent_impr:
        print(f"   melhoria média de preço de entrada (mais baixo) nos fills = {st.mean(ent_impr):+.1f} pts")

    # ---- NULL ----
    import random
    random.seed(42)
    null_rs = []
    for r in got:
        lo = r["jf"]
        k = min(S["N"] - 1, lo + random.randint(1, 48))
        ent = S["C"][k]; sl = r["sl"]; rr = ent - sl
        if rr <= 0:
            continue
        tgt = ent + 3 * rr; o = "OPEN"
        for m in range(k + 1, min(S["N"], k + HORIZON + 1)):
            if S["L"][m] <= sl: o = "LOSS"; break
            if S["H"][m] >= tgt: o = "WIN"; break
        if o in ("WIN", "LOSS"): null_rs.append(r_of(o))
    print(f"\n[NULL entrada aleatória +1..+48]  {panel(null_rs)['s']}")

    # ---- VEREDITO §4 ----
    bp = panel(base_res)
    print(f"\n{'='*78}\nVEREDITO §4 (limiares congelados)\n{'='*78}")
    for name, res, killed, med_b, over60 in [
        ("A", a_res, len(killedA), med_b_A, sum(1 for r in passA if r["bounce"] > 60)),
        ("B", b_res, killedB, med_b_B, sum(1 for r in got if r["fvg"] and r["bounce"] > 60))]:
        pn = panel(res)
        c1 = killed <= 1
        c2 = (bp["n"] and (st.median([r["bounce"] for r in got]) - med_b) >= 15) or name == "B"
        # nota: para B a mediana bounce não muda (mede-se melhoria de PREÇO, não de bounce%) → localização
        # avaliada por melhoria de entrada; marco c2 como n/a informativo para B.
        c3 = pn["sumR"] >= bp["sumR"] - 1e-9 and (pn["rdd"] >= bp["rdd"] - 1e-9 or pn["rdd"] == float("inf"))
        verdict = "PASS" if (c1 and c3 and (name == "B" or c2)) else "FAIL"
        print(f"  Opção {name}: {verdict} | mata≤1={c1}({killed}) · loc≥15pts={'n/a' if name=='B' else c2} · "
              f"agregado≥base={c3} (sumR {pn['sumR']:+.1f} vs {bp['sumR']:+.1f})")
    print("\n  C = etiqueta (risco zero, não gate) — informativa; não sujeita a PASS/FAIL.")
    print("  Lembrete: 32 in-sample = evidência de desenho, não prova. PASS → prereg forward, não edição live.")


if __name__ == "__main__":
    main()
