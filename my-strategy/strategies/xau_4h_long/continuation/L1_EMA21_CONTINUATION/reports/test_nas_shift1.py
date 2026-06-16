import sys, json, tempfile, os
from pathlib import Path
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import runtime_xau as rt, scanner
# snapshot sintético: 70 bars 4H, NAS ATUAL=Y(5.0); histórico i-1 NAS=X(2.0)
t0=1_700_000_000; bars=[{"time":t0+k*14400,"open":100+k,"high":101+k,"low":99+k,"close":100.5+k,"volume":1000} for k in range(70)]
snap={"ohlcv_recent":bars,"nas_dist":5.0,"ob_zones":[{"high":150,"low":140}],"rsi":55.0,"rsi_ma":50.0,"bar_time":bars[-1]["time"],"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240"}
X=2.0  # NAS i-1 (histórico)
S,i=rt.build_live_series(snap, nas_im1=X)
assert i==69, i
v=scanner.nas_dist_shift1(S,i)
print("  scanner.nas_dist_shift1(S,i) =", v, "| esperado X(i-1)=2.0 | atual Y=5.0")
assert v==X, f"FAIL: usou {v} != X"
assert v!=5.0, "FAIL: usou NAS atual como SHIFT1"
assert S.nas_at=={S.T[i-1]:X}, f"FAIL nas_at mapping: {S.nas_at}"
assert S.T[i-1]==bars[-2]["time"], "FAIL: i-1 não é o penúltimo bar"
print("  PASS: NAS SHIFT1 = valor de i-1 (histórico); NÃO usa NAS atual; i-1 = penúltimo bar (sem futuro)")

# teste blocking: sem histórico -> blocked_missing_nas_shift1
tmp=tempfile.mktemp(suffix=".jsonl"); rt.FEATURE_HISTORY=Path(tmp)
out=rt.evaluate(snap)
print("  sem histórico:", out["state"])
assert out["state"]=="blocked_missing_nas_shift1", out["state"]
# após persistir i-1 e re-rodar: o persist grava bar i; precisamos i-1 -> seed manual
Path(tmp).write_text(json.dumps({"bar_time":bars[-2]["time"],"nas_dist":2.0})+"\n")
out2=rt.evaluate(snap)
print("  com histórico i-1 (regime decide o resto):", out2["state"], "| nas_dist_shift1=", out2.get("nas_dist_shift1"))
assert out2.get("nas_dist_shift1")==2.0
os.unlink(tmp)
# teste <60 bars -> blocked_missing_base_rule_live_fields
rt.FEATURE_HISTORY=Path(tempfile.mktemp(suffix=".jsonl"))
snap_short={**snap,"ohlcv_recent":bars[:10]}
Path(rt.FEATURE_HISTORY).write_text(json.dumps({"bar_time":bars[8]["time"],"nas_dist":2.0})+"\n")
out3=rt.evaluate(snap_short)
print("  <60 bars:", out3["state"])
assert out3["state"]=="blocked_missing_base_rule_live_fields", out3["state"]
print("\nTODOS OS ASSERTS PASSARAM")
