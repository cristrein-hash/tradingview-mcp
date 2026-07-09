#!/usr/bin/env python3
"""FASE 3 — confirma persistência do estudo NAS visível/computado. Read-only (toggle mínimo só se
oculto). Sem draw/screenshot/clear/símbolo-change. Verifica n_bars>0 + NAS_DISTANCE + timestamps 4H.
Output: l1_preproduction_nas_visibility_result.json."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
from tv_read_adapter import _MCP
BAR=14400; NAS="pkqE7L"
res={"phase":"preproduction_nas_visibility"}
c=_MCP(); c.start()
try:
    st=c.call("chart_get_state")
    res["chart_symbol"]=(st or {}).get("symbol"); res["chart_tf"]=(st or {}).get("resolution") or (st or {}).get("timeframe")
    res["is_xau_4h"]=(res["chart_symbol"]=="PEPPERSTONE:XAUUSD" and str(res["chart_tf"])=="240")
    di=c.call("data_get_indicator",{"entity_id":NAS})
    res["visible"]=(di or {}).get("visible")
    if res["visible"] is False:
        c.call("indicator_toggle_visibility",{"entity_id":NAS,"visible":True})
        res["toggled_visible"]=True
        di=c.call("data_get_indicator",{"entity_id":NAS}); res["visible"]=(di or {}).get("visible")
    else:
        res["toggled_visible"]=False
    r=c.call("data_get_study_values_at_bar",{"study_filter":"NAS","count":8})
    nas=None
    for s in (r or {}).get("studies") or []:
        if "NAS" in (s.get("name") or "").upper(): nas=s; break
    bars=(nas or {}).get("bars") or []
    times=[b.get("time") for b in bars]
    def dist(b):
        v=b.get("values") or {}
        for k in v:
            if "DISTANCE" in k.upper(): return v[k]
        return None
    dvals=[dist(b) for b in bars]
    res["nas_study_name"]=(nas or {}).get("name"); res["n_bars"]=len(bars)
    res["has_distance_all"]=bool(bars) and all(d is not None for d in dvals)
    res["timestamps_4h_distinct"]=len(times)>1 and len(set(times))==len(times) and all((times[k+1]-times[k])%BAR==0 for k in range(len(times)-1))
    res["last3"]=[{"time":b.get("time"),"dist":dist(b)} for b in bars[-3:]]
    res["verdict"]="PASS" if (res["is_xau_4h"] and res["visible"] is True and res["n_bars"]>1
                              and res["has_distance_all"] and res["timestamps_4h_distinct"]) else "REVIEW"
finally:
    try: c.stop()
    except Exception: pass
(HERE/"l1_preproduction_nas_visibility_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
