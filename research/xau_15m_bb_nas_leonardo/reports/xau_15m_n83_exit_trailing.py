#!/usr/bin/env python3
"""EXIT REVIEW N83 — TRAILING RATCHET REAL (ordem Cris: testar trailing antes de concluir).
Lição L1 4H aplicada: ratchet verdadeiro (stop só sobe), buffer ATR, saída intrabar SÓ no stop
ELEVADO, floor = SL estrutural V1. Causal: stop ativo no bar m usa highs/ATR CONFIRMADOS <= m-1.
Famílias pré-registradas (grelha fixa, sem otimização solta):
  CHAND_k  = max(prev, maxH[j..m-1] - k*ATR[m-1]), k in {2,3,4,5,6,8}
  ATRT_k   = max(prev, C[m-1] - k*ATR[m-1]),       k in {2,3}
  RLAD     = trail 1R atrás do pico-R inteiro confirmado
  SWBUF    = max(prev, min low 12 barras confirmadas - 0.5*ATR)
Baseline = 3R fixo (125R). Métricas + per-year + null de exposição (random close com mesma
distribuição de duração do candidato). População N83 congelada (caveat: base com event-selection
lookahead — achados condicionais, transferem p/ base reparada). Output: ..._trailing_result.json."""
import json, sys, random
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
random.seed(20260709)
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
HOR=L.HORIZON

def sim_trail(tr,kind,k=None):
    """Ratchet causal; retorna (R, bars). Floor=SL0 sempre; exit intrabar em LO<=eff (fill no eff)."""
    j=tr["j"]; ent=tr["ent"]; sl0=tr["sl"]; risk=ent-sl0
    eff=sl0; hh=L.HI[j]; maxR=0.0
    last=min(L.N-1,j+HOR)
    for m in range(j+1,last+1):
        a=L.ATR[m-1] or 5
        if kind=="CHAND": cand=hh-k*a
        elif kind=="ATRT": cand=L.CL[m-1]-k*a
        elif kind=="RLAD":
            step=int(maxR)-1; cand=ent+step*risk if step>=1 else sl0
        elif kind=="SWBUF": cand=min(L.LO[max(0,m-12):m])-0.5*a
        else: cand=sl0
        eff=max(eff,cand,sl0)
        if L.LO[m]<=eff:
            return (eff-ent)/risk, m-j
        hh=max(hh,L.HI[m]); maxR=max(maxR,(L.HI[m]-ent)/risk)
    return (L.CL[last]-ent)/risk, last-j

RULES=[("CHAND",2),("CHAND",3),("CHAND",4),("CHAND",5),("CHAND",6),("CHAND",8),
       ("ATRT",2),("ATRT",3),("RLAD",None),("SWBUF",None)]
res={"baseline_3R":{"sumR":125.0,"WR":62.7,"DD":-4.0,"streak":4},"alts":{}}
for kind,k in RULES:
    name=f"{kind}_{k}" if k is not None else kind
    out=[(tr,)+sim_trail(tr,kind,k) for tr in n83]
    Rs=[r for _,r,_ in out]; bars=[b for _,_,b in out]
    p=L.panel(Rs); p["avg_bars"]=round(sum(bars)/len(bars),1)
    yr={}
    for (tr,r,_) in out: yr.setdefault(L.dstr(tr["t"])[:4],[]).append(r)
    p["per_year"]={y:{"n":len(v),"sumR":round(sum(v),1)} for y,v in sorted(yr.items())}
    res["alts"][name]=p

# null de exposição p/ o melhor trailing por sumR: random close (duração U[1,dur_cand]) com SL0
best=max(res["alts"].items(),key=lambda kv:kv[1]["sumR"])
bname=best[0]; bkind,bk=(bname.split("_")[0], None if "_" not in bname else None)
# recomputar durações do melhor
kk=None
for kind,k in RULES:
    nm=f"{kind}_{k}" if k is not None else kind
    if nm==bname: bkind,kk=kind,k
durs=[sim_trail(tr,bkind,kk)[1] for tr in n83]
TRI=800; nulls=[]
for _ in range(TRI):
    tot=0.0
    for tr,dmax in zip(n83,durs):
        kx=random.randint(1,max(1,dmax))
        s=L.simulate(tr["j"],tr["ent"],tr["sl"],None,time_cap=kx)
        tot+=s["R"] if s["R"] is not None else 0
    nulls.append(tot)
nulls.sort(); obs=best[1]["sumR"]
res["null_exposure_best"]={"best":bname,"obs":obs,"null_mean":round(sum(nulls)/TRI,1),
    "null_p95":round(nulls[int(0.95*TRI)],1),"p_null_ge_obs":round(sum(1 for x in nulls if x>=obs)/TRI,3)}
res["caveat"]="população N83 congelada (base com event-selection lookahead) — achados condicionais"
(HERE/"xau_15m_n83_exit_trailing_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(f"{'rule':<10} {'sumR':>7} {'WR':>5} {'PF':>5} {'DD':>6} {'stk':>4} {'bars':>6}  per-year")
print(f"{'3R_fixed':<10} {125.0:>7} {62.7:>5} {5.03:>5} {-4.0:>6} {4:>4} {94.5:>6}  2025:72 2026:53")
for name,p in res["alts"].items():
    yb=" ".join(f"{y}:{v['sumR']}" for y,v in p["per_year"].items())
    print(f"{name:<10} {p['sumR']:>7} {p['WR']:>5} {str(p['PF']):>5} {p['maxDD_R']:>6} {p['streak']:>4} {p['avg_bars']:>6}  {yb}")
print("null:",res["null_exposure_best"])
