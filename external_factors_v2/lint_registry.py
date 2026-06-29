#!/usr/bin/env python3
"""FASE 0 GATE — lint do registry/whitelist External Factors v2. Checa as invariantes ANTES de qualquer coleta:
- toda fonte tem tier + headless_safe (bool)
- todo tier1_series tem fred-code/endpoint + cadence + asof_lag + transform
- NENHUM tier2 declara output numérico (output_numeric deve ser false)
- nenhuma fonte tier2 usada como tier1
Sem rede. Sai !=0 se violar."""
import json,sys
from pathlib import Path
H=Path(__file__).parent
W=json.loads((H/"config/sources_whitelist.json").read_text())
R=json.loads((H/"config/factor_registry.json").read_text())
err=[]
for s in W["sources"]:
    if s.get("tier") not in ("tier1","tier2"): err.append(f"fonte {s.get('id')}: tier inválido")
    if not isinstance(s.get("headless_safe"),bool): err.append(f"fonte {s.get('id')}: headless_safe ausente/não-bool")
    if not s.get("auth"): err.append(f"fonte {s.get('id')}: auth não declarado")
for t in R["tier1_series"]:
    for k in ("id","fred","cadence","asof_lag_days","transform","driver"):
        if k not in t: err.append(f"tier1 {t.get('id')}: falta '{k}'")
for c in R["tier2_classifiers"]:
    if c.get("output_numeric") is not False: err.append(f"tier2 {c.get('id')}: output_numeric DEVE ser false (fronteira de determinismo)")
    if not c.get("labels"): err.append(f"tier2 {c.get('id')}: sem labels")
n1=len(R["tier1_series"]); n2=len(R["tier2_classifiers"])
hs=sum(1 for s in W["sources"] if s["headless_safe"])
print(f"sources={len(W['sources'])} (headless_safe={hs}) | tier1_series={n1} | tier2_classifiers={n2}")
print(f"tier1 séries: {', '.join(t['fred'] for t in R['tier1_series'])}")
if err:
    print("\nLINT FALHOU:"); [print("  -",e) for e in err]; sys.exit(1)
print("\n✅ LINT OK — registry/whitelist consistente. Fase 0 gate PASS.")
