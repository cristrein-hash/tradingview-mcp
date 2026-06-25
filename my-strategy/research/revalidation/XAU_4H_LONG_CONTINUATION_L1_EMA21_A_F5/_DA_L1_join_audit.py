#!/usr/bin/env python3
"""AUDITORIA DO JOIN (DA): confirma que ts L1 → barra raw_features mapeia certo (|Δt|<7200s + data alinha) e mostra
regime_v3 + VAL + close em alguns trades (incl. 2020-mais-antigo). Verified 2026-06-25."""
import json, bisect, gzip, datetime as dt
from pathlib import Path
V1 = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
appr = json.load(open(Path(__file__).parent / "l1_approved34.json"))
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_e"] = toep(r["ts"])
rb.sort(key=lambda r: r["_e"]); rbt = [r["_e"] for r in rb]
def reg_asof(et): k = bisect.bisect_right(rbt, et) - 1; return (rb[k].get("raw_state"), rb[k]["ts"]) if k >= 0 else (None, None)
def l1_epoch(ts): return int(dt.datetime.fromisoformat(ts).replace(tzinfo=dt.timezone.utc).timestamp())
def bar_of(et):
    k = bisect.bisect_left(TS, et); cands = [j for j in (k - 1, k, k + 1) if 0 <= j < N]
    return min(cands, key=lambda j: abs(TS[j] - et)) if cands else None
# distribuição de regime nos 34 + auditoria de join
regs = {}
for a in appr:
    et = l1_epoch(a["ts"]); i = bar_of(et); rg, _ = reg_asof(TS[i])
    regs[rg] = regs.get(rg, 0) + 1
print("distribuição regime_v3 nos 34 L1:", regs)
print("\n=== JOIN AUDIT (amostra) ===")
print(f"{'L1_ts':>17} | {'barra_matched_ISO':>17} | {'|Δt|s':>6} | {'regime':>11} | {'reg_ts':>11} | {'close':>8}")
sample = [appr[0], appr[1], appr[len(appr) // 2], appr[-1]]
for a in sample:
    et = l1_epoch(a["ts"]); i = bar_of(et); biso = dt.datetime.utcfromtimestamp(TS[i]).strftime("%Y-%m-%dT%H:%M")
    rg, rts = reg_asof(TS[i]); dtt = abs(TS[i] - et)
    print(f"{a['ts']:>17} | {biso:>17} | {dtt:>6} | {str(rg):>11} | {str(rts)[:11]:>11} | {C[i]:>8.2f}")
mx = max(abs(TS[bar_of(l1_epoch(a['ts']))] - l1_epoch(a['ts'])) for a in appr)
print(f"\n|Δt| MÁXIMO entre os 34 = {mx}s (pass se <7200)")
