#!/usr/bin/env python3
"""AUTO-AUDITORIA do Engine 2 (Cris 2026-06-28): por que a seleção pegou tanta FACA CAINDO apesar do Eng1 saber o
fingerprint (forte=raso/controlado/não-exausto; fraco=capitulação sobrevendida)? Diagnóstico determinístico."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
SEL={int(r["cj_t"]) for r in __import__("csv").DictReader(open(HERE/"entry2_selected_trades.csv"))}
sel=[r for r in ROWS if r["cj_t"] in SEL]
# definição FACA CAINDO (do fingerprint Eng1): sobrevendido + vol alta + perna não-desacelerando + abaixo da EMA1H
def knife(r):
    return (r.get("rsi_min8",50)<32) and (r.get("atr_regime",1)>1.05) and (r.get("downleg_decel",0)==0)
def corr(a,b):
    xs=[(r.get(a),r.get(b)) for r in ROWS if r.get(a) is not None and r.get(b) is not None]
    n=len(xs); ma=sum(x for x,_ in xs)/n; mb=sum(y for _,y in xs)/n
    cov=sum((x-ma)*(y-mb) for x,y in xs); va=sum((x-ma)**2 for x,_ in xs); vb=sum((y-mb)**2 for _,y in xs)
    return cov/((va*vb)**.5) if va>0 and vb>0 else 0
MF=sum(r["is_monforte"] for r in ROWS)
print("=== AUTO-AUDIT ENGINE 2 ===")
print(f"OVER-FIRE: {len(sel)} trades p/ {MF} fundos MON+FORTE = {len(sel)/MF:.1f}x excesso (quantidade, não qualidade)")
print(f"  da seleção: MON+FORTE={sum(r['is_monforte'] for r in sel)} | MED+FRACO={sum(r['is_medfraco'] for r in sel)} | NONE={sum(1 for r in sel if r['label']=='NONE')}")
print(f"selecionados: {len(sel)} | FACA-CAINDO na seleção: {sum(1 for r in sel if knife(r))} ({100*sum(1 for r in sel if knife(r))/len(sel):.0f}%)")
allknife=[r for r in ROWS if knife(r)]
print(f"facas no universo: {len(allknife)} | delas MON+FORTE: {sum(r['is_monforte'] for r in allknife)} | MED+FRACO: {sum(r['is_medfraco'] for r in allknife)}")
print(f"\nPOR QUE: reclaim_atr (feature estrela do Eng2) correlaciona com FACA?")
print(f"  corr(reclaim_atr, rsi_min8)   = {corr('reclaim_atr','rsi_min8'):+.2f}  (negativo => reclaim alto vem de mínima sobrevendida=faca que quica)")
print(f"  corr(reclaim_atr, atr_regime) = {corr('reclaim_atr','atr_regime'):+.2f}  (positivo => reclaim alto em vol alta=flush)")
print(f"  corr(reclaim_atr, downleg_decel)= {corr('reclaim_atr','downleg_decel'):+.2f}")
# o Eng2 NÃO usou as features anti-faca do Eng1 como qualificação
print("\nFALHA: Eng2 buscou MAXIMIZAR precisão-de-LABEL com 3 features (greedy), e a feature que 'venceu' (reclaim_atr)")
print("é justamente um detector de QUICADA-DE-FACA, não de fundo limpo. Não impôs qualificação macro/multi-TF anti-faca.")
print("Eng1 SABIA separar (atr_regime baixo, rsi_min8 alto, pullback raso) mas Eng2 ignorou esse conhecimento.")
# o que o fingerprint Eng1 faria como GATE anti-faca
nonknife_mf=[r for r in ROWS if not knife(r) and r["is_monforte"]]
print(f"\nse GATE anti-faca (not knife): remove {sum(1 for r in ROWS if knife(r))} candidatos, preserva {len(nonknife_mf)}/{sum(r['is_monforte'] for r in ROWS)} MON+FORTE")
