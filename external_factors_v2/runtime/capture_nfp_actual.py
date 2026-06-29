#!/usr/bin/env python3
"""CAPTURA DO ACTUAL pós-NFP (Camada A). No/após o release, puxa PAYEMS (keyless FRED) -> NFP headline real
(MoM), preenche actual_k no calendar_consensus.json e recomputa surpresa->direção (actual-consenso).
Antes do release ou se o dado ainda não saiu na FRED: no-op honesto (mantém pending). Determinístico, py3.9."""
import json,subprocess,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; ccf=SNAP/"calendar_consensus.json"
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
if not ccf.exists(): print("sem calendar_consensus.json — rode calendar_consensus.py primeiro"); raise SystemExit
cc=json.loads(ccf.read_text())
# PAYEMS keyless (nível mensal) -> headline = MoM diff
r=subprocess.run(["curl","-sS","--http1.1","--max-time","60",
  "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PAYEMS&cosd=2024-01-01"],capture_output=True,text=True)
pay=[]
for ln in r.stdout.splitlines()[1:]:
    p=ln.split(",")
    if len(p)<2 or p[1] in("",".","NA"): continue
    pay.append((dt.datetime.strptime(p[0],"%Y-%m-%d").date(),float(p[1])))
pay.sort()
def headline_for(release_date):
    # NFP do release de mês M reporta o mês M-1; PAYEMS obs_date = 1º dia do mês reportado
    rd=dt.datetime.strptime(release_date,"%Y-%m-%d").date()
    rep=(rd.replace(day=1)-dt.timedelta(days=1)).replace(day=1)  # mês anterior ao release
    idx={d:i for i,(d,_) in enumerate(pay)}
    if rep not in idx or idx[rep]==0: return None
    i=idx[rep]; return round(pay[i][1]-pay[i-1][1],0)  # MoM = headline em milhares
def direction(a,c):
    if a is None or c is None: return {"bias":"pending","awaiting":"actual no release"}
    s=a-c
    return {"bias":"bearish" if s>0 else ("bullish" if s<0 else "neutral"),"surprise_k":s,
            "rule":"NFP forte(actual>consenso)->USD↑->ouro↓","resolved_ts":NOWT}
changed=0
for ev in cc.get("upcoming_high_impact",[]):
    if not ev.get("event","").lower().startswith("nonfarm"): continue
    if ev.get("actual_k") is not None: continue
    if NOWT < ev.get("release_ts",NOWT)-3600: print(f"NFP {ev['release_date']} ainda não liberado (em {(ev['release_ts']-NOWT)/3600:.1f}h) — pending"); continue
    a=headline_for(ev["release_date"])
    if a is None: print(f"actual ainda não publicado na FRED p/ {ev['release_date']} — pending (re-rodar após atualização FRED)"); continue
    ev["actual_k"]=a; ev["direction"]=direction(a,ev.get("consensus_k")); changed+=1
    print(f"NFP {ev['release_date']}: actual={a}K consenso={ev.get('consensus_k')}K -> surpresa={ev['direction'].get('surprise_k')}K dir={ev['direction']['bias']}")
if changed:
    ccf.write_text(json.dumps(cc,indent=1,ensure_ascii=False)); print(f"atualizado {ccf}")
else:
    print("nada a atualizar (pending ou já resolvido)")
