#!/usr/bin/env python3
"""JANELA VIRGEM 2024-25 — BEAR-ONLY SKIP ONE-SHOT (prereg ..._VIRGIN_WINDOW_2024_25_PREREG.md).
Leitura multi-fatorial congelada (S2a profundidade 1D + S3 estrutura acima), trajetória (zz online,
bounce-peaks), dois objetivos (cortar losers preservar winners), null cluster-aware — teste VIRGEM
ao nível de outcome/seleção (declarado no prereg §1). RODA UMA VEZ. Zero tuning.

Etapas na ordem dura do prereg §2:
 (0) CONSISTÊNCIA: gerador RAW-only reproduz a base conhecida na janela 2025-08+? (match por t)
 (1) Gerar candidatos virgem (2024-07-01→2025-04-08) + macro + flags S2a/S3 → CONGELAR (sem outcomes)
 (2) Outcomes 3R first-touch SL-first h1440 → composites A/B/C/D → métricas → null por bloco semanal.
Gerador = Opção B FROZEN re-implementada RAW-only (F0): zz(6·ATR) online sem confirmação futura,
WIN=24, higher-low, reclaim EMA21(15M), SL V1, risk>0,05·ATR. ATR=SMA14-TR/EMA21 do F0 (variante
declarada). S3 = código pinado (import de skip_family_discovery, sha b749b7a62386fd7c)."""
import json, sys, csv, bisect, random, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]/"xau_15m_structural_leg_engine"))
sys.path.insert(0, str(HERE))
from f1_structural_leg_machine import Data
from skip_family_discovery import bounce_peaks   # código PINADO
random.seed(20260709)
R6, WIN, HOR = 6, 24, 1440
V0 = int(dt.datetime(2024, 7, 1, tzinfo=dt.timezone.utc).timestamp())
V1 = int(dt.datetime(2025, 4, 8, tzinfo=dt.timezone.utc).timestamp())
B0 = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())
B1 = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
BASE_CSV = HERE.parents[0]/"xau_15m_bb_nas_leonardo/reports/xau_15m_live_fireable_candidates.csv"

def gen_candidates(D, EMA21, w0, w1):
    """walk online Opção B FROZEN (sem outcomes). Devolve rows(i,j,t,ent,sl)."""
    HI, LO, CL, ATR, TS = D.H, D.L, D.C, D.ATR, D.TS
    n = len(TS)
    d = 0; ehi = elo = 0; prevL = None; lastH = None
    entered = set(); rows = []; open_window = None
    for k in range(1, n):
        a = ATR[k]
        if HI[k] > HI[ehi]: ehi = k
        if LO[k] < LO[elo]: elo = k
        if d <= 0 and HI[k]-LO[elo] >= R6*a and elo < k:
            open_window = (elo, min(n-1, elo+WIN))
            prevL = LO[elo]; d = 1; ehi = max(range(elo, k+1), key=lambda q: HI[q])
        elif d >= 0 and HI[ehi]-LO[k] >= R6*a and ehi < k:
            lastH = HI[ehi]; d = -1; elo = min(range(ehi, k+1), key=lambda q: LO[q]); open_window = None
        cand = None
        if d == -1 and lastH is not None and elo < k and (k-elo) <= WIN: cand = elo
        elif open_window and open_window[0] < k <= open_window[1]: cand = open_window[0]
        if cand is None or cand in entered: continue
        lo = LO[cand]
        kind_markup = (prevL is None or lo > prevL)
        if not (w0 <= TS[cand] <= w1): continue
        if EMA21[k] is not None and CL[k] > EMA21[k] and CL[k] > CL[k-1]:
            entered.add(cand)
            if not kind_markup: continue
            aa = ATR[cand] or 5
            ent = CL[k]; sl = lo-0.1*aa; risk = ent-sl
            if risk <= 0.05*aa: continue
            rows.append({"i": cand, "j": k, "t": TS[k], "ent": round(ent, 2), "sl": round(sl, 2),
                         "risk": round(risk, 2)})
    return rows

def simulate(D, j, ent, sl, tgt):
    for k in range(j+1, min(j+1+HOR, len(D.TS))):
        if D.L[k] <= sl: return "SL"
        if D.H[k] >= tgt: return "TGT"
    return "TIME"

def main():
    D = Data()
    n = len(D.TS)
    # EMA21 15M (recursiva completa, causal)
    EMA21 = [None]*n
    kk = 2/22; e = D.C[0]
    for i in range(n):
        e = D.C[i]*kk + e*(1-kk); EMA21[i] = e
    # EMA21 1D price-agg (S2a)
    emad = []; e = D.DC[0]
    for v in D.DC: e = v*kk + e*(1-kk); emad.append(e)
    def px1d(t, px, a):
        di = bisect.bisect_left(D.DK, t//86400)-1
        return (px-emad[di])/(a or 5) if di >= 0 else None
    # ---- (0) CONSISTÊNCIA na janela conhecida ----
    known = {int(r["t"]) for r in csv.DictReader(open(BASE_CSV))}
    rep = gen_candidates(D, EMA21, B0, B1)
    rep_t = {r["t"] for r in rep}
    match = len(known & rep_t)
    consist = {"known_166": len(known), "reimpl_n": len(rep), "match_exact_t": match,
               "match_rate_vs_known": round(match/len(known), 3)}
    if consist["match_rate_vs_known"] < 0.80:
        out = {"STOP": "consistência <80% — investigar antes do virgem", "consistency": consist}
        (HERE/"results/virgin_window_skip_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2)); return 1
    # ---- (1) universo virgem + flags (SEM outcomes) → CONGELAR ----
    virg = gen_candidates(D, EMA21, V0, V1)
    for r in virg:
        t = r["t"]; i = bisect.bisect_right(D.TS, t)-1
        a = D.ATR[i] or 5.0
        r["macro"] = D.macro_at(t)
        v = px1d(t, r["ent"], a)
        r["S2a_px1d"] = round(v, 2) if v is not None else None
        r["F_S2a"] = int(r["macro"] == "BEAR" and v is not None and v >= 0)
        w0i = max(0, i-384)
        j_hi = w0i + max(range(i+1-w0i), key=lambda q: D.H[w0i+q])
        pks = bounce_peaks(D, j_hi, i)
        nd = 0
        for q in range(len(pks)-1, 0, -1):
            if pks[q] < pks[q-1]: nd += 1
            else: break
        r["S3_ndesc"] = nd
        r["F_S3"] = int(r["macro"] == "BEAR" and nd >= 2)
    bear = [r for r in virg if r["macro"] == "BEAR"]
    frozen = {"window": ["2024-07-01", "2025-04-08"], "n_candidates": len(virg),
              "by_macro": {g: sum(1 for r in virg if r["macro"] == g) for g in ("BULL", "BEAR", "RANGE")},
              "n_bear": len(bear), "ids_t_bear": sorted(r["t"] for r in bear),
              "flags_frozen_before_outcomes": True,
              "underpowered": len(bear) < 15}
    (HERE/"results/virgin_bear_universe_frozen.json").write_text(json.dumps(frozen, indent=2))
    # ---- (2) outcomes (só agora) + composites ----
    for r in virg:
        tgt = r["ent"]+3*r["risk"]
        r["oc"] = simulate(D, r["j"], r["ent"], r["sl"], tgt)
        r["out"] = 1 if r["oc"] == "TGT" else 0
    bear_res = [r for r in bear if r["oc"] != "TIME"]
    L0 = sum(1 for r in bear_res if r["out"] == 0); W0_ = len(bear_res)-L0
    def comp(fl):
        m = [r for r in bear_res if fl(r)]
        Lm = sum(1 for r in m if r["out"] == 0)
        return {"skipped": len(m), "losers_skipped": Lm, "winners_skipped": len(m)-Lm,
                "losers_remaining": L0-Lm, "winners_preserved": W0_-(len(m)-Lm),
                "skip_precision": round(Lm/len(m), 2) if m else None,
                "false_skip_rate": round((len(m)-Lm)/W0_, 2) if W0_ else None}
    comps = {"A_S2a": comp(lambda r: r["F_S2a"]),
             "B_S3": comp(lambda r: r["F_S3"]),
             "C_OR": comp(lambda r: r["F_S2a"] or r["F_S3"]),
             "D_AND": comp(lambda r: r["F_S2a"] and r["F_S3"])}
    ov = {"both": sum(1 for r in bear_res if r["F_S2a"] and r["F_S3"]),
          "S2a_only": sum(1 for r in bear_res if r["F_S2a"] and not r["F_S3"]),
          "S3_only": sum(1 for r in bear_res if r["F_S3"] and not r["F_S2a"]),
          "S3_only_losers": sum(1 for r in bear_res if r["F_S3"] and not r["F_S2a"] and r["out"] == 0)}
    # null cluster-aware (blocos semana ISO; permuta outcomes por bloco; 2000; seed fixa)
    weeks = {}
    for r in bear_res:
        wk = dt.datetime.utcfromtimestamp(r["t"]).strftime("%G-W%V")
        weeks.setdefault(wk, []).append(r)
    def null_p(fl, obs):
        cnt = 0; TRI = 2000
        blocks = list(weeks.values())
        outs_by_block = [[r["out"] for r in b] for b in blocks]
        all_blocks = list(range(len(blocks)))
        for _ in range(TRI):
            perm = outs_by_block[:]
            random.shuffle(perm)          # permuta vetores de outcome ENTRE blocos de tamanho compatível?
            # blocos têm tamanhos distintos: permutar atribuição bloco->vetor exige tamanhos iguais;
            # fallback declarado: shuffle DENTRO do pool com unidade = bloco (troca outcomes de blocos inteiros
            # de igual tamanho; blocos sem par de tamanho = shuffle interno)
            by_size = {}
            for bi in all_blocks: by_size.setdefault(len(blocks[bi]), []).append(bi)
            assign = {}
            for sz, bis in by_size.items():
                src = bis[:]; random.shuffle(src)
                for bi, sj in zip(bis, src): assign[bi] = sj
            tot = 0
            for bi in all_blocks:
                outs = [r["out"] for r in blocks[assign[bi]]]
                tot += sum(1 for r, o in zip(blocks[bi], outs) if fl(r) and o == 0)
            if tot >= obs: cnt += 1
        return round(cnt/TRI, 4)
    nulls = {"B_S3": null_p(lambda r: r["F_S3"], comps["B_S3"]["losers_skipped"]),
             "C_OR": null_p(lambda r: r["F_S2a"] or r["F_S3"], comps["C_OR"]["losers_skipped"])}
    per_week = {wk: {"n": len(b), "L": sum(1 for r in b if r["out"] == 0),
                     "skipped_C": sum(1 for r in b if r["F_S2a"] or r["F_S3"])}
                for wk, b in sorted(weeks.items())}
    out = {"prereg": "XAU_15M_BEAR_ONLY_SKIP_VIRGIN_WINDOW_2024_25_PREREG.md",
           "consistency_check": consist, "frozen": {k: v for k, v in frozen.items() if k != "ids_t_bear"},
           "bear_resolved": {"n": len(bear_res), "L": L0, "W": W0_,
                             "TIME_excluded": len(bear)-len(bear_res)},
           "composites": comps, "overlap": ov, "nulls_cluster_aware": nulls,
           "per_week": per_week,
           "note": "ONE-SHOT; zero tuning; leitura = READER; verdict só após DA"}
    (HERE/"results/virgin_window_skip_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with open(HERE/"results/virgin_window_candidates.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(virg[0].keys()))
        w.writeheader()
        for r in virg: w.writerow(r)
    print(json.dumps({k: v for k, v in out.items() if k != "per_week"}, indent=2, ensure_ascii=False))
    print("MEASURED_OK")

if __name__ == "__main__":
    sys.exit(main() or 0)
