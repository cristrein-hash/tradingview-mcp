#!/usr/bin/env python3
"""FASE 2 — NAS durability + startup fail-closed. (A) live: NAS visível/computado, n_bars>0, distância.
(B) startup guard: evaluate() com nas_series vazio -> blocked_missing_nas_live_series (sem envio, tripwire).
Read-only. Output: l1_nas_durability_check_result.json."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
BAR=14400; res={"phase":"nas_durability"}

# tripwire Telegram
R.notify=lambda *a,**k:(_ for _ in ()).throw(AssertionError("notify chamado"))
_trip={"run":False}
def _r(*a,**k): _trip["run"]=True; raise AssertionError("subprocess.run chamado")
R.subprocess.run=_r

# (A) live NAS
try:
    from tv_read_adapter import _MCP
    c=_MCP(); c.start()
    try:
        st=c.call("chart_get_state")
        di=c.call("data_get_indicator",{"entity_id":"pkqE7L"})
        rr=c.call("data_get_study_values_at_bar",{"study_filter":"NAS","count":8})
        nas=None
        for s in (rr or {}).get("studies") or []:
            if "NAS" in (s.get("name") or "").upper(): nas=s; break
        bars=(nas or {}).get("bars") or []
        def dist(b):
            v=b.get("values") or {}
            return next((v[k] for k in v if "DISTANCE" in k.upper()), None)
        res["live"]={"symbol":(st or {}).get("symbol"),"tf":(st or {}).get("resolution") or (st or {}).get("timeframe"),
            "nas_visible":(di or {}).get("visible"),"n_bars":len(bars),
            "distance_present":bool(bars) and all(dist(b) is not None for b in bars),
            "last_dist":dist(bars[-1]) if bars else None}
        res["live"]["pass"]=(res["live"]["nas_visible"] is True and res["live"]["n_bars"]>1 and res["live"]["distance_present"])
    finally:
        try: c.stop()
        except Exception: pass
except Exception as e:
    res["live"]={"error":str(e)[:200],"pass":False}

# (B) startup guard: snapshot com nas_series VAZIO
def make_snap(nas_series):
    now=int(datetime.now(timezone.utc).timestamp()); nf=now-(now%BAR)
    times=[nf-(62-k)*BAR for k in range(63)]
    bars=[{"time":t,"open":2000+i,"high":2005+i,"low":1995+i,"close":2000+i,"volume":100} for i,t in enumerate(times)]
    eval_t=times[-2]
    return dict(symbol="PEPPERSTONE:XAUUSD",timeframe="240",bar_time=times[-1],ohlcv_recent=bars,
        nas_series=nas_series,rsi_series=[{"time":eval_t,"rsi":45.0,"rsi_ma":50.0}],ob_zones=[{"high":1990,"low":1980}])
out_empty=R.evaluate(make_snap([]))
res["startup_guard_empty_nas"]={"state":out_empty["state"],"operational":out_empty.get("operational"),
    "pass":(out_empty["state"]=="blocked_missing_nas_live_series" and out_empty.get("operational") is False)}
res["telegram_tripwire_zero"]=(not _trip["run"])
res["verdict"]="PASS" if (res.get("live",{}).get("pass") and res["startup_guard_empty_nas"]["pass"]
    and res["telegram_tripwire_zero"]) else "REVIEW"
(HERE/"l1_nas_durability_check_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
