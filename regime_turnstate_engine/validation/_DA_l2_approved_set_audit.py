#!/usr/bin/env python3
"""AUDITORIA (a pedido do Cris): o set que coletei p/ a avaliação de regime na L2/BPT É a estratégia APROVADA?
Confronto FACTUAL: (a) o que coletei (qualification_decisions_merged.csv, decision==TAKE, realR CAPADO);
(b) os sets de trades existentes no corpus L2 (tamanho + se R é capado); (c) a definição CANÓNICA da aprovação (memória).
Sem conclusões/caminhos — só expor a correspondência ou a divergência."""
import json,csv,glob,os
from pathlib import Path
L2=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
def rfield(d):
    for k in ("realR","net","R","r","lr"):
        if k in d: return k
    return None
print("="*80);print("(a) O QUE COLETEI para a avaliação de regime");print("="*80)
Q=L2/"results/l2_bpt_trade_qualification_decisions_merged.csv"
rows=list(csv.DictReader(open(Q)))
from collections import Counter
dec=Counter(r["decision"] for r in rows)
take=[r for r in rows if r["decision"]=="TAKE"]
realRs=[float(r["realR"]) for r in rows if r["realR"] not in("","None")]
print(f"  fonte: {Q.name}")
print(f"  decisões: {dict(dec)} | usei decision==TAKE = {len(take)} trades")
print(f"  campo de R: realR | range realR (todos 276): [{min(realRs):+.2f} , {max(realRs):+.2f}]  -> CAP no topo? max={max(realRs):+.2f}")
print(f"  sumR(realR) dos 32 TAKE = {sum(float(r['realR']) for r in take):+.1f}")
print("\n"+"="*80);print("(b) SETS DE TRADES existentes no corpus L2 (tamanho + cap de R)");print("="*80)
for f in sorted(glob.glob(str(L2/"results/*.json"))):
    try:
        d=json.load(open(f))
        rs=d if isinstance(d,list) else (d.get("trades") if isinstance(d,dict) else None)
        if isinstance(rs,list) and rs and isinstance(rs[0],dict):
            rf=rfield(rs[0])
            if rf:
                vals=[x[rf] for x in rs if isinstance(x.get(rf),(int,float))]
                if vals:
                    print(f"  {os.path.basename(f):52} n={len(rs):4} Rfield={rf:6} max={max(vals):+6.2f} sum={sum(vals):+7.1f} {'(UNCAPPED?)' if max(vals)>5 else '(capado<=~4)'}")
    except: pass
print("\n"+"="*80);print("(c) DEFINIÇÃO CANÓNICA da L2/BPT APROVADA (memória, factual)");print("="*80)
print("""  project_xau_4h_long_FINAL_l1_l2_approved.md + project_l2_bpt_*_approved:
  - Estratégia = trada o UNIVERSO 276 (bases: BULL+absorb n44 WR50% +37.5R / not_clean-supply-acima n97 WR42% +62.1R).
  - RÉGUA DE EXIT OFICIAL = VSTAIR (trailing escalonado), let-run p/ monumentais. Full-276 vstair: N276 WR23.9% +207.7R.
    R é UNCAPPED (a estratégia 'vive da cauda'; o cap distorce — é uma das '3 peças sólidas' do Cris).
  - LOSER-CUT aprovado = bear-leg refined (DENTRO de MACRO_BEAR_LEG n29), não global.
  - Regime: ≠BEAR NÃO se aplica à L2 (testado: ATRAPALHA −62R let-run; L2 lucra no bear=reversão-de-fundo). Regime=só contexto.""")
print("\n"+"="*80);print("(d) CORRESPONDÊNCIA");print("="*80)
print(f"  coletado: decision==TAKE (n={len(take)}), realR CAPADO (+3.9R), exit implícito do realR.")
print(f"  aprovado: universo 276 / bases 44+97, exit VSTAIR let-run UNCAPPED, bear-leg cut contextual.")
print(f"  => set coletado ({len(take)} TAKE capado) NÃO é o set aprovado (276/44/97 vstair uncapped). Divergente em: tamanho, régua de exit, e cap de R.")
