#!/usr/bin/env python3
"""RTSE FASE 3a — sonda EIXO ACEITAÇÃO (cortador de FP, bem-powered).
Detector ruidoso = swing-break 15M (rompe máx/mín de Nb barras). Rotula cada disparo TRUE/FALSE pelo M8
(reversão real perto). Feature = ACEITAÇÃO: fração dos próximos N closes que SEGURAM além do nível rompido
(corpo, não pavio). Pergunta: aceitação separa virada-real de falso-rompimento? + null + simulação de corte de FP.
Aceitação é avaliada N barras após o disparo (causal em i+N) = estágio MATURING (custo=latência, ganho=menos FP).
Determinístico. M8=régua, nunca feature."""
import json,csv,statistics as st,random
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
PR=ROOT/"research/xau_15m_bb_nas_leonardo/primitives"
bars={}
for f in sorted(PR.glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]:
        bars[b["t"]]={"t":b["t"],"h":b["h"],"l":b["l"],"c":b["c"]}
S=[bars[t] for t in sorted(bars)]; T=[b["t"] for b in S];C=[b["c"] for b in S];H=[b["h"] for b in S];L=[b["l"] for b in S];n=len(S)
# M8 pivôs
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv"))]
bot=sorted(t for t,k in m8 if k=="BOT");top=sorted(t for t,k in m8 if k=="TOP")
def near(ts,arr,W):
    import bisect;i=bisect.bisect_left(arr,ts-W);return i<len(arr) and arr[i]<=ts+W
Nb=20;N=5;W=24*3600
fires=[]  # (i, dir, level, true)
cur=None
for i in range(Nb,n-N):
    d=None;lev=None
    if C[i]>max(H[i-Nb:i]): d="UP";lev=max(H[i-Nb:i])
    elif C[i]<min(L[i-Nb:i]): d="DOWN";lev=min(L[i-Nb:i])
    if d and d!=cur:
        cur=d
        tru = near(T[i],bot,W) if d=="UP" else near(T[i],top,W)
        # aceitação: fração dos N closes seguintes que seguram além do nível (corpo)
        acc = st.mean([1.0 if ((C[i+j]>lev) if d=="UP" else (C[i+j]<lev)) else 0.0 for j in range(1,N+1)])
        fires.append((d,tru,acc))
    elif d: cur=d
nt=sum(1 for _,t,_ in fires if t); nf=len(fires)-nt
acc_t=[a for _,t,a in fires if t];acc_f=[a for _,t,a in fires if not t]
YRS=(T[-1]-T[0])/(365.25*86400)
print(f"FASE 3a — eixo ACEITAÇÃO | disparos swing-break 15M: {len(fires)} | TRUE(real) {nt} / FALSE(FP) {nf} | {YRS:.1f} anos")
print(f"aceitação média: TRUE={st.mean(acc_t):.3f} vs FALSE={st.mean(acc_f):.3f} | diff={st.mean(acc_t)-st.mean(acc_f):+.3f}")
# null: embaralha rótulos
random.seed(42);diffs=[]
labs=[t for _,t,_ in fires];accs=[a for _,_,a in fires]
for _ in range(200):
    random.shuffle(labs)
    dt_=st.mean([accs[i] for i in range(len(accs)) if labs[i]])-st.mean([accs[i] for i in range(len(accs)) if not labs[i]])
    diffs.append(dt_)
real=st.mean(acc_t)-st.mean(acc_f)
p=sum(1 for x in diffs if abs(x)>=abs(real))/len(diffs)
print(f"null (shuffle labels x200): diff médio {st.mean(diffs):+.3f} | p(|null|>=|real|) = {p:.3f}")
# corte de FP: exigir aceitação >= thr
print(f"\ncorte por aceitação>=thr | recall mantido | FP/ano restante (base FP/ano={nf/YRS:.0f})")
for thr in (0.4,0.6,0.8,1.0):
    keep_t=sum(1 for _,t,a in fires if t and a>=thr);keep_f=sum(1 for _,t,a in fires if (not t) and a>=thr)
    print(f"  thr>={thr}: recall {keep_t/nt:.2f} ({keep_t}/{nt}) | FP/ano {keep_f/YRS:.0f} (cortou {100*(1-keep_f/nf):.0f}%)")
print("\nLEITURA: se TRUE>>FALSE em aceitação (p baixo) e thr corta FP segurando recall -> aceitação É cortador de FP causal.")
