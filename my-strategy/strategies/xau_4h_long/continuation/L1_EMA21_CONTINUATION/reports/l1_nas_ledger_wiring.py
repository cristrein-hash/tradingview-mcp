#!/usr/bin/env python3
"""FASE 3 — DRY-RUN TEST do wiring do ledger NAS SHIFT1 (fail-closed). NÃO liga cycle/Telegram/produção.
Usa ledger TEMPORÁRIO (não toca o real). Prova:
  T1 i usa i-1 do ledger (fonte congelada)      T4 NAS(i) NÃO é usado como i-1
  T2 ausência de i-1 -> blocked_missing_nas_shift1_ledger
  T3 bar_time corrupto (2017) -> rejeitado (persist E nas_from_history)   T5 live!=ledger -> mismatch block
  + guards: conflicting_duplicate, symbol/tf.
Output: l1_nas_ledger_wiring_result.json."""
import sys, json, tempfile
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R

TF=14400
def fresh_ledger():
    tmp=Path(tempfile.mkdtemp())/"led.jsonl"; R.FEATURE_HISTORY=tmp; R.STATE_DIR=tmp.parent; return tmp
def write_ledger(tmp, rows):
    tmp.write_text("\n".join(json.dumps(r) for r in rows)+"\n")
def now_floor():
    n=int(datetime.now(timezone.utc).timestamp()); return n-(n%TF)

def make_snapshot(nas_prev, nas_eval, rsi=(45.0,50.0)):
    """63 barras 4H terminando em now_floor (última=forming). eval=penúltima (fechada), prev=antepenúltima."""
    nf=now_floor()
    times=[nf-(62-k)*TF for k in range(63)]
    bars=[{"time":t,"open":2000+i,"high":2005+i,"low":1995+i,"close":2000+i,"volume":100} for i,t in enumerate(times)]
    eval_t=times[-2]; prev_t=times[-3]
    return dict(symbol="PEPPERSTONE:XAUUSD",timeframe="240",bar_time=times[-1],
        ohlcv_recent=bars,
        nas_series=[{"time":eval_t,"nas_dist":nas_eval},{"time":prev_t,"nas_dist":nas_prev}],
        rsi_series=[{"time":eval_t,"rsi":rsi[0],"rsi_ma":rsi[1]}],
        ob_zones=[{"high":1990,"low":1980}]), eval_t, prev_t

res={"tests":{}}

# --- guards diretos ---
tmp=fresh_ledger()
ok2017,st2017=R.persist_feature(1488207600, 3.2)                 # 2017 -> deve rejeitar
v2017,vs2017=R.nas_from_history(1488207600)
res["tests"]["T3_corrupt_2017"]={"persist":[ok2017,st2017],"read":[v2017,vs2017],
    "pass":(ok2017 is False and "rejected_bar_time" in st2017 and v2017 is None and "bar_time_guard" in vs2017)}

tmp=fresh_ledger()
nf=now_floor(); bt=nf-TF
R.persist_feature(bt, 0.5)
okdup,stdup=R.persist_feature(bt, 0.9)                            # mesmo bar_time, valor diferente -> conflito
res["tests"]["guard_conflicting_dup"]={"result":[okdup,stdup],"pass":(okdup is False and stdup=="conflicting_duplicate")}

# --- T2: ausência de i-1 no ledger ---
tmp=fresh_ledger()
snap,eval_t,prev_t=make_snapshot(nas_prev=1.50, nas_eval=1.60)
out2=R.evaluate(snap)
res["tests"]["T2_missing_ledger"]={"state":out2["state"],"ledger_status":out2.get("nas_shift1_ledger_status"),
    "pass":(out2["state"]=="blocked_missing_nas_shift1_ledger")}

# --- T1: i usa i-1 do ledger (match live) ---
tmp=fresh_ledger()
snap,eval_t,prev_t=make_snapshot(nas_prev=1.50, nas_eval=1.60)
write_ledger(tmp,[{"bar_time":prev_t,"nas_dist":1.50,"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240"}])
out1=R.evaluate(snap)
res["tests"]["T1_uses_ledger_i_minus_1"]={"state":out1["state"],"ledger_status":out1.get("nas_shift1_ledger_status"),
    "nas_shift1_value":out1.get("nas_shift1_value"),"nas_shift1_source":out1.get("nas_shift1_source"),
    "pass":(out1.get("nas_shift1_ledger_status")=="ok" and out1.get("nas_shift1_value")==1.50
            and out1.get("nas_shift1_source")=="ledger_frozen"
            and out1["state"] not in ("blocked_missing_nas_shift1_ledger","blocked_nas_shift1_ledger_mismatch"))}

# --- T4: NAS(i) NÃO usado como i-1 (ledger prev=1.50, eval=9.99; valor usado deve ser 1.50) ---
tmp=fresh_ledger()
snap,eval_t,prev_t=make_snapshot(nas_prev=1.50, nas_eval=9.99)
write_ledger(tmp,[{"bar_time":prev_t,"nas_dist":1.50,"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240"},
                  {"bar_time":eval_t,"nas_dist":9.99,"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240"}])
out4=R.evaluate(snap)
res["tests"]["T4_nas_i_not_used_as_i_minus_1"]={"nas_shift1_value":out4.get("nas_shift1_value"),
    "eval_value_would_be":9.99,"pass":(out4.get("nas_shift1_value")==1.50 and out4.get("nas_shift1_value")!=9.99)}

# --- T5: live != ledger além da tolerância -> mismatch block ---
tmp=fresh_ledger()
snap,eval_t,prev_t=make_snapshot(nas_prev=1.50, nas_eval=1.60)      # live prev = 1.50
write_ledger(tmp,[{"bar_time":prev_t,"nas_dist":3.00,"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240"}])  # ledger 3.00
out5=R.evaluate(snap)
res["tests"]["T5_live_ledger_mismatch"]={"state":out5["state"],
    "pass":(out5["state"]=="blocked_nas_shift1_ledger_mismatch")}

# --- guard symbol errado no ledger ---
tmp=fresh_ledger()
snap,eval_t,prev_t=make_snapshot(nas_prev=1.50, nas_eval=1.60)
write_ledger(tmp,[{"bar_time":prev_t,"nas_dist":1.50,"symbol":"WRONG:SYM","timeframe":"240"}])
out6=R.evaluate(snap)
res["tests"]["guard_wrong_symbol_blocks"]={"state":out6["state"],
    "pass":(out6["state"]=="blocked_missing_nas_shift1_ledger")}

res["all_pass"]=all(t["pass"] for t in res["tests"].values())
res["verdict"]="PASS" if res["all_pass"] else "FAIL"
(HERE/"l1_nas_ledger_wiring_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
