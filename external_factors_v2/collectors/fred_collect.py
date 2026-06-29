#!/usr/bin/env python3
"""FASE 1 — coletor FRED KEYLESS (fredgraph.csv público). Puxa cada série do factor_registry, full history desde
2019, e grava painel com (series_id, obs_date, release_ts, value). release_ts = obs_date + asof_lag (proxy keyless;
vintage real vem com API key depois). Determinístico, headless-safe, sem secret. Saída: snapshots/macro_panel.jsonl"""
import json,subprocess,datetime as dt,time
from pathlib import Path
H=Path(__file__).parent.parent
REG=json.loads((H/"config/factor_registry.json").read_text())
OUT=H/"snapshots"; OUT.mkdir(exist_ok=True)
COSD="2019-01-01"
def pull(fred):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fred}&cosd={COSD}"
    r=subprocess.run(["curl","-sS","--http1.1","--max-time","60",url],capture_output=True,text=True)
    txt=r.stdout
    if not txt or "," not in txt: raise RuntimeError((r.stderr or "vazio")[:80])
    rows=[]
    for ln in txt.splitlines()[1:]:
        p=ln.split(",")
        if len(p)<2 or p[1] in ("",".","NA"): continue
        try: v=float(p[1])
        except: continue
        d=dt.datetime.strptime(p[0],"%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        rows.append((int(d.timestamp()),v))
    return rows
panel=[]
for s in REG["tier1_series"]:
    time.sleep(2.0)
    try: raw=pull(s["fred"])
    except Exception as e: print(f"  ! {s['fred']} falhou: {e}"); continue
    lag=s["asof_lag_days"]*86400
    # yoy p/ cpi/ppi (monthly), senão level
    if s["transform"]=="yoy_pct":
        bydate={t:v for t,v in raw}; ser=[]
        for t,v in raw:
            ty=t-365*86400; prev=min(bydate, key=lambda x:abs(x-ty)) if bydate else None
            if prev and abs(prev-ty)<40*86400 and bydate[prev]!=0:
                ser.append((t,round(100*(v/bydate[prev]-1),3)))
    else:
        ser=raw
    for obs,v in ser:
        panel.append({"series_id":s["id"],"fred":s["fred"],"obs_date":obs,"release_ts":obs+lag,"value":v})
    print(f"  {s['fred']:<10} {s['id']:<16} n={len(ser)} ult={ser[-1][1] if ser else '-'}")
panel.sort(key=lambda r:(r["series_id"],r["obs_date"]))
with open(OUT/"macro_panel.jsonl","w") as fh:
    for r in panel: fh.write(json.dumps(r)+"\n")
print(f"\nmacro_panel.jsonl: {len(panel)} obs, {len(set(r['series_id'] for r in panel))} séries -> {OUT/'macro_panel.jsonl'}")
