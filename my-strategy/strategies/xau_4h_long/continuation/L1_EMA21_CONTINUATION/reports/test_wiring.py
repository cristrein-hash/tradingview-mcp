import sys, json, tempfile
from pathlib import Path
from datetime import datetime, timezone
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import runtime_xau as rt
TF=14400; now=datetime.now(timezone.utc).timestamp()
rt.FEATURE_HISTORY=Path(tempfile.mktemp(suffix=".jsonl"))
def mkbars(last_time,n=70): return [{"time":int(last_time-(n-1-k)*TF),"open":100+k,"high":101+k,"low":99+k,"close":100.5+k,"volume":1000} for k in range(n)]
COMMON=dict(symbol="PEPPERSTONE:XAUUSD",timeframe="240",ob_zones=[{"high":150,"low":140}])

print("=== T1: forming last + séries por TIME (índice deslocado de propósito) ===")
lf=int(now-3600); bars=mkbars(lf)                  # bars[-1]=forming, eval=bars[-2], prev=bars[-3]
eval_t=bars[-2]["time"]; prev_t=bars[-3]["time"]; forming_t=bars[-1]["time"]
# séries com ORDEM embaralhada + bar forming + bar extra -> só TIME deve casar
nas_series=[{"time":forming_t,"nas_dist":9.99},{"time":eval_t,"nas_dist":1.50},{"time":prev_t,"nas_dist":2.20},{"time":prev_t-TF,"nas_dist":0.1}]
rsi_series=[{"time":forming_t,"rsi":99,"rsi_ma":1},{"time":eval_t,"rsi":55.0,"rsi_ma":50.0},{"time":prev_t,"rsi":40,"rsi_ma":45}]
snap={**COMMON,"ohlcv_recent":bars,"bar_time":bars[-1]["time"],"nas_series":nas_series,"rsi_series":rsi_series}
o=rt.evaluate(snap); al=o.get("study_alignment",{}); d=o.get("bar_diagnostics",{})
print(" state:",o["state"],"| forming_excluded:",d.get("forming_bar_excluded"))
print(" eval_bar_time:",d.get("eval_bar_time"),"== bars[-2]:",d.get("eval_bar_time")==eval_t)
print(" nas_eval:",al.get("nas_eval_value"),"src==eval:",al.get("nas_eval_source_time")==eval_t)
print(" nas_shift1:",al.get("nas_shift1_value"),"src==prev:",al.get("nas_shift1_source_time")==prev_t)
print(" rsi_eval:",al.get("rsi_eval_value"),"src==eval:",al.get("rsi_eval_source_time")==eval_t)
assert al["nas_eval_value"]==1.50 and al["nas_eval_source_time"]==eval_t
assert al["nas_shift1_value"]==2.20 and al["nas_shift1_source_time"]==prev_t
assert al["rsi_eval_value"]==(55.0,50.0) and al["rsi_eval_source_time"]==eval_t
assert al["nas_eval_value"]!=9.99 and al["nas_shift1_value"]!=9.99, "usou forming!"
assert o["state"] in ("no_candidate","blocked_l1_refined_filter","blocked_exhaustion","operational_candidate")
print(" PASS: alinhou por TIME; NAS SHIFT1 do prev fechado; RSI do eval; forming(9.99) IGNORADO; avaliou (não bloqueou por study)")

print("\n=== T2: série SEM o time do eval -> blocked_missing_closed_bar_study_values ===")
nas2=[{"time":forming_t,"nas_dist":9.99},{"time":prev_t,"nas_dist":2.2}]  # falta eval_t
snap2={**snap,"nas_series":nas2}
o2=rt.evaluate(snap2); print(" state:",o2["state"])
assert o2["state"]=="blocked_missing_closed_bar_study_values", o2["state"]
print(" PASS: bloqueia quando eval não alinha (não usa índice/forming)")

print("\n=== T3: prova anti-índice — só forming presente -> bloqueia (não pega por posição) ===")
snap3={**snap,"nas_series":[{"time":forming_t,"nas_dist":9.99}],"rsi_series":[{"time":forming_t,"rsi":99,"rsi_ma":1}]}
o3=rt.evaluate(snap3); print(" state:",o3["state"])
assert o3["state"]=="blocked_missing_closed_bar_study_values"
print(" PASS: nunca usa forming/índice")
print("\nTODOS OS ASSERTS PASSARAM")
