#!/usr/bin/env python3
"""Teste-ponte: as features de TRAJETÓRIA/CONTEXTO (as que o olho do Cris usa — posição na estrutura,
maturidade, retração, esticamento) separam a classe MON+FORTE melhor que as features de momentum do
builder? Se SIM = achamos o vetor do 'positivo descartado'. Se NÃO = o discriminador está fora da nossa
data (discricionário/HTF-leg). Alvo forward, N=58 = CALIBRAÇÃO estrita. Universo selado."""
import json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)
base = len(MF) / len(U)
print(f"alvo MON+FORTE {len(MF)}/{len(U)} base {100*base:.2f}%")
# distribuição das features de trajetória: MON+FORTE vs resto
def med(rows, k):
    v = sorted(fv(r, k) for r in rows); return v[len(v) // 2] if v else None
mf = [r for r in U if r["cj_t"] in MF]; rest = [r for r in U if r["cj_t"] not in MF]
print("\nMEDIANAS trajetória (MON+FORTE vs resto):")
for k in ("g_box96", "g_box480", "g_ema21_dist", "g_ema50_dist", "g_rec_speed", "g_atr_spike",
          "g_downrun", "g_sweep_depth", "g_cj_body", "legpos60", "legpos90", "pullback_depth", "reclaim_atr"):
    print(f"  {k:<16} MF={med(mf,k)}  resto={med(rest,k)}")
# lentes de trajetória por lift sobre MON+FORTE
CAND = {
 "box96<=0.4 (fundo)": lambda r: fv(r, "g_box96", .5) <= 0.4,
 "box96>=0.7 (topo)": lambda r: fv(r, "g_box96", .5) >= 0.7,
 "ema21_dist<=0 (abaixo EMA)": lambda r: fv(r, "g_ema21_dist", 9) <= 0,
 "ema21_dist>=1 (esticado)": lambda r: fv(r, "g_ema21_dist", 0) >= 1,
 "rec_speed>=0.7 (resposta rapida)": lambda r: fv(r, "g_rec_speed", 0) >= 0.7,
 "atr_spike>=1.3 (violencia)": lambda r: fv(r, "g_atr_spike", 0) >= 1.3,
 "sweep_depth>=0.8 (varredura funda)": lambda r: fv(r, "g_sweep_depth", 0) >= 0.8,
 "cj_body>=0.5 (corpo confirmacao)": lambda r: fv(r, "g_cj_body", 0) >= 0.5,
 "box480>=0.7 (alto na estrutura maior)": lambda r: fv(r, "g_box480", .5) >= 0.7,
 "downrun>=4 (perda longa)": lambda r: fv(r, "g_downrun", 0) >= 4,
}
rows = []
for nm, fn in CAND.items():
    sub = [r for r in U if fn(r)]
    mfin = sum(1 for r in sub if r["cj_t"] in MF)
    prec = mfin / len(sub) if sub else 0
    rows.append((nm, prec / base if base else 0, prec, mfin, len(sub)))
rows.sort(key=lambda x: -x[1])
print("\nLENTES TRAJETÓRIA por LIFT sobre MON+FORTE:")
for nm, lift, prec, mfin, nn in rows:
    print(f"  lift {lift:>4.1f}x  prec {100*prec:>4.1f}%  recall {mfin}/{len(MF)}  N{nn:>4}  {nm}")
best = max(r[1] for r in rows)
print(f"\nMELHOR LIFT trajetória = {best:.1f}x (vs melhor momentum builder 2,4x). "
      f"{'traço fraco — discriminador provavelmente HTF-leg/discricionário' if best < 3 else 'candidato'}")
