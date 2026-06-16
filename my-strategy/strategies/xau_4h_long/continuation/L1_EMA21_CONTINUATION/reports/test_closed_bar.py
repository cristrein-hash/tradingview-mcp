import sys, json, tempfile
from pathlib import Path
from datetime import datetime, timezone
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import runtime_xau as rt
TF=14400; now=datetime.now(timezone.utc).timestamp()
def mkbars(last_time, n=70):
    return [{"time":int(last_time-(n-1-k)*TF),"open":100+k,"high":101+k,"low":99+k,"close":100.5+k,"volume":1000} for k in range(n)]
COMMON=dict(symbol="PEPPERSTONE:XAUUSD",timeframe="240",nas_dist=5.0,ob_zones=[{"high":150,"low":140}],rsi=55.0,rsi_ma=50.0)

print("=== TESTE 1: última barra EM FORMAÇÃO (now dentro do bar) ===")
last_forming=int(now-3600)  # bar abriu há 1h -> fecha em +3h -> forming
bars=mkbars(last_forming); snap={**COMMON,"ohlcv_recent":bars,"bar_time":bars[-1]["time"]}
rt.FEATURE_HISTORY=Path(tempfile.mktemp(suffix=".jsonl"))
o=rt.evaluate(snap); d=o.get("bar_diagnostics",{})
print(" state:",o["state"])
print(" eval_bar_time:",d.get("eval_bar_time"),"| returned_last:",d.get("returned_last_bar_time"),"| forming_excluded:",d.get("forming_bar_excluded"))
assert o["state"]=="blocked_missing_closed_bar_study_values", o["state"]
assert d["forming_bar_excluded"] is True
assert d["eval_bar_time"]==bars[-2]["time"], "eval_bar deve ser a penúltima (fechada)"
assert rt.FEATURE_HISTORY.exists()==False or rt.FEATURE_HISTORY.read_text()=="" , "forming não deve persistir"
print(" PASS: forming excluído; eval_bar=penúltima fechada; sem persistir; bloqueio preciso")

print("\n=== TESTE 2: todas FECHADAS + NAS i-1 no histórico -> avalia ===")
last_closed=int(now-2*TF)  # último bar fechou há ~4h
bars=mkbars(last_closed); snap={**COMMON,"ohlcv_recent":bars,"bar_time":bars[-1]["time"]}
rt.FEATURE_HISTORY=Path(tempfile.mktemp(suffix=".jsonl"))
# seed NAS i-1 = bar fechado anterior ao eval_bar (penúltimo)
rt.FEATURE_HISTORY.write_text(json.dumps({"bar_time":bars[-2]["time"],"nas_dist":2.0})+"\n")
o=rt.evaluate(snap); d=o.get("bar_diagnostics",{})
print(" state:",o["state"],"| forming_excluded:",d.get("forming_bar_excluded"),"| eval_bar=last? ",d.get("eval_bar_time")==bars[-1]["time"])
print(" nas_dist_shift1 usado:",o.get("nas_dist_shift1"),"(esperado 2.0 = i-1; NÃO 5.0 atual)")
assert d["forming_bar_excluded"] is False
assert d["eval_bar_time"]==bars[-1]["time"]
assert o.get("nas_dist_shift1")==2.0, o.get("nas_dist_shift1")
# eval_bar (fechado) NAS persistido?
assert any(json.loads(l)["bar_time"]==bars[-1]["time"] for l in rt.FEATURE_HISTORY.read_text().splitlines())
print(" PASS: avalia eval_bar fechado; NAS SHIFT1=i-1(2.0), não atual(5.0); persistiu eval_bar fechado")

print("\n=== TESTE 3: todas fechadas, SEM histórico -> blocked_missing_nas_shift1 ===")
rt.FEATURE_HISTORY=Path(tempfile.mktemp(suffix=".jsonl"))
o=rt.evaluate(snap); print(" state:",o["state"])
assert o["state"]=="blocked_missing_nas_shift1", o["state"]
print(" PASS")
print("\nTODOS OS ASSERTS PASSARAM")
