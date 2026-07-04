#!/usr/bin/env python3
"""DA ATAQUE 2 (CENTRAL) — lookahead de vida da zona OB.
O mapa exige atividade born_t<=t0<=last_t; last_t (fim de vida da zona) só é conhecido DEPOIS de t0
→ lookahead estrutural. Recompute com zonas ativas por born_t<=t0 APENAS (100% causal) e reporte:
lentes de zona nos 3 TFs, par campeão (15M supply_far3atr & 1H demand_near1atr) e pipeline completo."""
import json, statistics as st
import _DA_mtf_common as C

print("recomputando ctx borncausal (trades + 1107 controles)…")
trc_bc = C.trades_ctx("borncausal")
ct_bc = [{k: v for k, v in o.items() if k != "_cj_t"} for o in C.controls_ctx("borncausal", 0, "g_entry")]
cache = json.load(open(C.SCRATCH / "ctx_orig_shift0.json"))
trc_o, ct_o = cache["trc"], [{k: v for k, v in o.items() if k != "_cj_t"} for o in cache["ct"]]
print(f"controles: orig={len(ct_o)} borncausal={len(ct_bc)}\n")

ZLENS = ["inside_demand", "demand_near1atr", "supply_far3atr"]
print(f"{'LENTE':<18}{'TF':<5}{'ORIG cris/ctrl lift':>24}{'BORNCAUSAL cris/ctrl lift':>30}")
for name in ZLENS:
    for tfk in ("15M", "30M", "1H"):
        ao, bo = C.cov(trc_o, tfk, name), C.cov(ct_o, tfk, name)
        ab, bb = C.cov(trc_bc, tfk, name), C.cov(ct_bc, tfk, name)
        lo = ao / bo if bo else float("inf"); lb = ab / bb if bb else float("inf")
        print(f"{name:<18}{tfk:<5}{f'{100*ao:.0f}%/{100*bo:.1f}% {lo:.2f}x':>24}{f'{100*ab:.0f}%/{100*bb:.1f}% {lb:.2f}x':>30}")

print("\nzonas ativas (mediana) cris vs ctrl:")
for tfk in ("15M", "30M", "1H"):
    for k in ("n_demand_active", "n_supply_active"):
        print(f"  {tfk} {k}: orig cris={st.median([o[tfk][k] for o in trc_o])} ctrl={st.median([o[tfk][k] for o in ct_o])}"
              f" | borncausal cris={st.median([o[tfk][k] for o in trc_bc])} ctrl={st.median([o[tfk][k] for o in ct_bc])}")

ao, bo, lo = C.pair_lift(trc_o, ct_o)
ab, bb, lb = C.pair_lift(trc_bc, ct_bc)
print(f"\nPAR CAMPEÃO 15M:supply_far3atr & 1H:demand_near1atr")
print(f"  ORIG       : cris {100*ao:.1f}% ctrl {100*bo:.2f}% lift {lo:.2f}x")
print(f"  BORNCAUSAL : cris {100*ab:.1f}% ctrl {100*bb:.2f}% lift {lb:.2f}x")

lifts, cands, best = C.pipeline(trc_bc, ct_bc)
print("\npipeline completo BORNCAUSAL — top singles (cov>=60%, lift>=1.3):")
for n, tfk, a, b, l in cands[:8]: print(f"  {tfk:<4}{n:<20} {100*a:.0f}%/{100*b:.1f}% {l:.2f}x")
print("pares top-6 (cov>=50%):")
for nm, a, b, l in best[:6]: print(f"  {nm:<58} {100*a:.0f}%/{100*b:.1f}% {l:.2f}x")

json.dump({"trc": trc_bc, "ct": ct_bc}, open(C.SCRATCH / "ctx_borncausal_shift0.json", "w"))
print(f"\ncache salvo: {C.SCRATCH}/ctx_borncausal_shift0.json")
