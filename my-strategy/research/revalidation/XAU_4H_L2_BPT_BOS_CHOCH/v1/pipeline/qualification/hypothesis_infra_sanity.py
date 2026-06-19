#!/usr/bin/env python3
"""L2/BPT — SANITY da infra de hipóteses. Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
Não calcula outcome, não roda OOS, não toca engine. Confere apenas que a governança está coerente:
registry válido, capit+rsi registrado, dry-runs PASS, gate bloqueia promoção, library sem promovidos,
nenhum aggregator criado, nenhuma decisão alterada. Escreve results/l2_bpt_hypothesis_infra_sanity.csv.
"""
import os, sys, csv, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hypothesis_registry as reg

QD = os.path.dirname(os.path.abspath(__file__))   # pipeline/qualification
D = reg.D
checks = []


def add(name, ok, detail):
    checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})


# 1. registry schema valid
rows = reg.load_registry()
allok = all(reg.validate_hypothesis(h)["valid"] for h in rows)
add("registry_schema_valid", bool(rows) and allok, f"{len(rows)} hipótese(s); todas válidas={allok}")

# 2. capit+rsi registered com status/use corretos
capr = next((h for h in rows if h["hypothesis_id"] == "L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1"), None)
ok2 = bool(capr) and capr["status"] == "PROMISING_IN_SAMPLE" and capr["allowed_engine_use"] == "REVIEW_ONLY" and capr["validation_required"] is True
add("capit_rsi_registered", ok2, f"status={capr and capr['status']} use={capr and capr['allowed_engine_use']}")

# 3. validation dry-run PASS (ready estrutural, sem cálculo)
vrun = os.path.join(D, "l2_bpt_hypothesis_validation_dry_run.csv")
vok = os.path.exists(vrun)
if vok:
    vr = list(csv.DictReader(open(vrun)))
    vok = any(r["hypothesis_id"] == capr["hypothesis_id"] and r["ready_for_validation"] == "YES" for r in vr)
add("validation_dry_run_pass", vok, "ready_for_validation=YES; OOS NÃO rodado")

# 4. DA dry-run PASS (capit+rsi -> manter REVIEW_ONLY / OOS)
drun = os.path.join(D, "l2_bpt_hypothesis_da_audit_dry_run.csv")
dok = os.path.exists(drun)
if dok:
    dr = list(csv.DictReader(open(drun)))
    row = next((r for r in dr if r["hypothesis_id"] == capr["hypothesis_id"]), {})
    dok = row.get("oos_required") == "YES" and "OOS_CANDIDATE" in row.get("suggested_status", "")
add("da_dry_run_pass", dok, "oos_required=YES; manter REVIEW_ONLY")

# 5. promotion gate BLOCKS capit+rsi
grun = os.path.join(D, "l2_bpt_promotion_gate_dry_run.csv")
gok = os.path.exists(grun)
if gok:
    gr = list(csv.DictReader(open(grun)))
    row = next((r for r in gr if r["hypothesis_id"] == capr["hypothesis_id"]), {})
    gok = row.get("can_promote") == "NO" and row.get("blocked_reasons", "") not in ("", "(nenhum)")
add("promotion_gate_blocks_capit_rsi", gok, gok and row.get("blocked_reasons", "")[:90] or "")

# 6. confluence library marks nothing as promoted
libp = os.path.join(QD, "validated_confluence_library.json")
lib = json.load(open(libp))
lok = lib.get("promoted_rules") == [] and all(it.get("allowed_use") != "PROMOTED" and it.get("oos_status") is False for it in lib.get("items", []))
add("confluence_library_no_promoted", lok, f"promoted_rules={lib.get('promoted_rules')}; items={len(lib.get('items', []))}")

# 7. no aggregator created (nenhum arquivo aggregator no pacote)
aggs = glob.glob(os.path.join(QD, "*aggregator*"))
add("no_aggregator_created", len(aggs) == 0, f"arquivos aggregator encontrados={len(aggs)}")

# 8. no decisions changed (decisions_merged não staged/modificado)
import subprocess
root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=QD).stdout.strip()
dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=root).stdout
touched_engine = [l for l in dirty.splitlines() if any(k in l for k in ("decisions_merged", "qualification_extract", "QUALIFICATION_RUBRIC", "strategy_rules", "monitor_xau", "receiver"))]
add("no_decisions_or_engine_changed", len(touched_engine) == 0, f"engine/decisões tocados={len(touched_engine)}")

# escreve csv
OUT = os.path.join(D, "l2_bpt_hypothesis_infra_sanity.csv")
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["check", "result", "detail"])
    w.writeheader()
    w.writerows(checks)

npass = sum(1 for c in checks if c["result"] == "PASS")
print(f"SANITY: {npass}/{len(checks)} PASS -> {OUT}")
for c in checks:
    print(f"  [{c['result']}] {c['check']}: {c['detail']}")
sys.exit(0 if npass == len(checks) else 1)
