#!/usr/bin/env python3
"""ALVO = classe MON+FORTE (fundos genuínos, label forward, 100% hit-3R) — achar a ASSINATURA CAUSAL.
Reframe pós-crítica Cris: parar de medir hit-3R genérico; predizer a classe boa a partir de features
causais. N pequeno (label forward) = CALIBRAÇÃO estrita (canon 45-grupos); cross-val leave-year-out
obrigatório; is_monforte NUNCA entra como feature (é o alvo). Universo selado."""
import json, hashlib, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = [r for r in U if fv(r, "is_monforte") == 1]
print(f"universo {len(U)} · MON+FORTE (alvo) {len(MF)} · base-rate {100*len(MF)/len(U):.2f}%")
print(f"MON+FORTE por regime: {dict(collections.Counter(r['g_v5h'] for r in MF))} · por ano {dict(collections.Counter(r['yr'] for r in MF))}")
print(f"MON+FORTE hit-3R: {sum(1 for r in MF if R3[r['cj_t']]['R3']>=3)}/{len(MF)} · sob let-run g_R>=3: {sum(1 for r in MF if fv(r,'g_R')>=3)}/{len(MF)}")

# lentes causais candidatas → LIFT sobre o alvo (P(MF|lente)/base) e recall
CAND = {
 "swept_prior_low": lambda r: fv(r, "swept_prior_low") == 1,
 "HTF4H&1D up": lambda r: fv(r, "h4n_trend") == 1 and fv(r, "h1n_trend") == 1,
 "h1_pos>=0.44": lambda r: fv(r, "h1_pos", 0) >= 0.44,
 "reclaim_atr>=2": lambda r: fv(r, "reclaim_atr", 0) >= 2.0,
 "up_closes>=3": lambda r: fv(r, "up_closes_pc", 0) >= 3,
 "confirm_body>=0.6": lambda r: fv(r, "confirm_body_atr", 0) >= 0.6,
 "clean_sky<=0.5": lambda r: fv(r, "clean_sky_atr", 9) <= 0.5,
 "n_supply<=30": lambda r: fv(r, "n_supply_overhead", 99) <= 30,
 "in_demand": lambda r: fv(r, "in_demand") == 1,
 "htf_demand_confl": lambda r: fv(r, "htf_demand_confluence") == 1,
 "rsi_low>=30": lambda r: fv(r, "rsi_low", 50) >= 30,
 "sem_faca": lambda r: r["g_knife"] == 0,
 "micro_hl": lambda r: fv(r, "micro_hl") == 1,
 "reclaim_ema<=3": lambda r: fv(r, "reclaim_ema_bars", 99) <= 3,
 "downleg_eff>=0.45": lambda r: fv(r, "downleg_eff", 0) >= 0.45,
 "atr_regime>1.2": lambda r: fv(r, "atr_regime", 1) > 1.2,
 "legpos60>=0.3": lambda r: fv(r, "legpos60", 0) >= 0.3,
 "pos_recent20>=0.35": lambda r: fv(r, "pos_recent20", 0) >= 0.35 if False else True,
}
del CAND["pos_recent20>=0.35"]
base = len(MF) / len(U)
rows = []
for nm, fn in CAND.items():
    sub = [r for r in U if fn(r)]
    mf_in = sum(1 for r in sub if fv(r, "is_monforte") == 1)
    prec = mf_in / len(sub) if sub else 0
    rows.append((nm, prec, prec / base if base else 0, mf_in, len(MF), len(sub)))
rows.sort(key=lambda x: -x[2])
print("\nLENTES por LIFT sobre MON+FORTE (precisão P(MF|lente) · lift · recall):")
for nm, prec, lift, mfin, mftot, nn in rows:
    print(f"  lift {lift:>4.1f}x  prec {100*prec:>4.1f}%  recall {mfin}/{mftot}  N{nn:>4}  {nm}")

# convergência: quantas lentes de alto-lift cada MON+FORTE satisfaz vs não-MF
HL = [nm for nm, prec, lift, mfin, mftot, nn in rows if lift >= 1.3][:8]
print(f"\nCONVERGÊNCIA das {len(HL)} de maior lift {HL}:")
def votes(r): return sum(1 for nm in HL if CAND[nm](r))
for k in range(3, len(HL) + 1):
    keep = [r for r in U if votes(r) >= k]
    mfin = sum(1 for r in keep if fv(r, "is_monforte") == 1)
    prec = mfin / len(keep) if keep else 0
    h3 = sum(1 for r in keep if R3[r["cj_t"]]["R3"] >= 3) / len(keep) if keep else 0
    print(f"  >={k}/{len(HL)}: N{len(keep):>4} ({len(keep)/WEEKS:.2f}/sem) · MF-recall {mfin}/{len(MF)} "
          f"· precisão-MF {100*prec:.1f}% (lift {prec/base:.1f}x) · hit3R {100*h3:.1f}%")
print("\nNOTA: alvo is_monforte = FORWARD label; precisão alta = candidato, NÃO validação. Cross-val e N pequeno decidem.")
