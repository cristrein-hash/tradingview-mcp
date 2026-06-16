import json, sys, csv
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
L1 = REPO / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"
sys.path.insert(0, str(L1))
import scanner  # gate atual (regime_l1_v4)

RC = REPO / "my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
TRADES = REPO / "my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/rebuild_v3/trades.jsonl"
OUT_CSV = L1 / "reports/l1_old_vs_new_regime_comparison.csv"
OUT_JSON = L1 / "reports/l1_old_vs_new_regime_comparison.json"

def norm(ts): return ts.replace("Z","")[:16]

# regime_B_v3 estático: ts(date) -> v3_state
oldreg = {}
for l in open(RC):
    r = json.loads(l); oldreg[r["ts"][:10]] = r.get("v3_state")
def b3_state(ts16): return oldreg.get(ts16[:10], "NO_DATA(>2026-05-25)")

# OLD 38 com R-labels (regime_B_v3 BULL)
old = json.loads(open(TRADES).read())
old_by_ts = {norm(t["ts"]): t for t in old}   # n,ts,cls,R,MFE_R...
OLD_TS = set(old_by_ts)

# NEW: varrer todos os bars sob regime_l1_v4 (gate atual)
S = scanner.build_series()
new = {}
for i in range(60, S.N):
    passed,_ = scanner.gate_trace(S, i)
    if not passed: continue
    o = scanner.evaluate(S, i)
    new[norm(o["timestamp"])] = o
NEW_TS = set(new)

allts = sorted(OLD_TS | NEW_TS)
rows = []; cid = 0
for ts in allts:
    cid += 1
    in_old = ts in OLD_TS; in_new = ts in NEW_TS
    status = "BOTH" if (in_old and in_new) else ("OLD_ONLY" if in_old else "NEW_ONLY")
    o = old_by_ts.get(ts); n = new.get(ts)
    r_label = (o["R"] if o else None)
    outcome_known = "yes" if o else "no"
    new_state = (n["state"] if n else "no_candidate")
    exh = (n["exhaustion_gate"] if n else None)
    rsi = (n["rsi_vs_ma"] if n else (None))
    # classificação
    if status == "BOTH":
        cls = "WINNER_PRESERVED" if (r_label is not None and r_label > 0) else "NEUTRAL"  # losers antigos preservados = NEUTRAL (já estavam)
    elif status == "OLD_ONLY":
        cls = "WINNER_LOST" if (r_label is not None and r_label > 0) else "LOSER_REMOVED"
    else:  # NEW_ONLY
        cls = "NEW_UNKNOWN"
    key = []
    if o and o.get("n") in (1,11,36,38): key.append(f"#{o['n']}_preserved")
    if o and o.get("n") in (3,15,18,32): key.append(f"#{o['n']}_rsi_block")
    rows.append({
        "candidate_id": cid, "timestamp": ts,
        "old_selected": in_old, "new_selected": in_new, "status": status,
        "old_regime": "BULL" if in_old else b3_state(ts),  # OLD eram BULL por construção
        "new_regime": "BULL" if in_new else "non-BULL",
        "r_label": r_label, "label_source": ("rebuild_v3/trades.jsonl" if o else ""),
        "outcome_known": outcome_known, "classification": cls,
        "old_state": ("selected_regimeB_v3" if in_old else b3_state(ts)),
        "new_state": new_state, "rsi_vs_ma": rsi,
        "exhaustion_blocked": (exh if exh is not None else ""),
        "key_case": ";".join(key), "notes": ("old trade #%s cls=%s"%(o["n"],o.get("cls")) if o else "regime_l1_v4 admitiu; regime_B_v3="+b3_state(ts)),
    })

with open(OUT_CSV,"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)

# agregados (R só onde conhecido)
old_R = [t["R"] for t in old]
old_sum = round(sum(old_R),2); old_wr = round(100*sum(1 for r in old_R if r>0)/len(old_R),1)
old_win = sum(1 for r in old_R if r>0); old_loss = sum(1 for r in old_R if r<=0)
pf = round(sum(r for r in old_R if r>0)/abs(sum(r for r in old_R if r<0)),2) if any(r<0 for r in old_R) else None
new_only = [r for r in rows if r["status"]=="NEW_ONLY"]
new_only_b3 = {}
for r in new_only: new_only_b3[b3_state(r["timestamp"])] = new_only_b3.get(b3_state(r["timestamp"]),0)+1
summ = {
 "OLD_count": len(OLD_TS), "NEW_count": len(NEW_TS),
 "BOTH": sum(1 for r in rows if r["status"]=="BOTH"),
 "OLD_ONLY": sum(1 for r in rows if r["status"]=="OLD_ONLY"),
 "NEW_ONLY": len(new_only),
 "winners_lost": sum(1 for r in rows if r["classification"]=="WINNER_LOST"),
 "losers_removed": sum(1 for r in rows if r["classification"]=="LOSER_REMOVED"),
 "new_unknown": sum(1 for r in rows if r["classification"]=="NEW_UNKNOWN"),
 "OLD_sumR_in_sample": old_sum, "OLD_WR": old_wr, "OLD_win": old_win, "OLD_loss": old_loss, "OLD_PF": pf,
 "NEW_sumR": "UNKNOWN (38 conhecidos + 25 sem R; não inventar)",
 "new_only_regimeB_v3_states": new_only_b3,
 "NOT_VALIDATION": True,
}
OUT_JSON.write_text(json.dumps(summ, indent=2, ensure_ascii=False))
print(json.dumps(summ, indent=2, ensure_ascii=False))
