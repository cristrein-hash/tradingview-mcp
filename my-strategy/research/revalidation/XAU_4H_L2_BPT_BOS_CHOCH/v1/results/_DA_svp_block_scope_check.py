#!/usr/bin/env python3
"""DA SCOPE CHECK (read-only) — classifica os arquivos dirty do working tree em IN-SCOPE (SVP-block +
foundation-anchor) vs OUT-OF-SCOPE para o commit deste bloco. Usado pela auditoria DA 2026-06-23.
Roda do repo root. Verified at: 2026-06-23."""
import subprocess

IN_SCOPE = {
    "docs/XAU_4H_L2_BPT_READER_SVP_ACCEPTANCE_RAW_AUDIT.md",
    "docs/XAU_4H_L2_BPT_READER_SOURCE_MAPPING_AUDIT.md",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/l2_bpt_raw_backbone_builder.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/l2_bpt_raw_svp_acceptance_builder.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_raw_backbone_episodes.jsonl",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_raw_svp_acceptance_episodes.jsonl",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_lookahead_window_check.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_svp_raw_structure_audit.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_svp_raw_study_audit.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_svp_raw_study_audit2.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_svp_volume_feasibility.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/_DA_svp_block_scope_check.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/source_gate/reader_raw_source_manifest.yaml",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_reader_source_mapping_inventory.csv",
}
# arquivos dirty pre-existentes, NAO produzidos por este bloco — devem ficar FORA do commit
KNOWN_OUT = {
    "my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/plot_t8_canonical.py",
    "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_hypothesis_infra_sanity.csv",
}

out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
dirty = [l[3:] for l in out.splitlines() if l]
in_s = [f for f in dirty if f in IN_SCOPE]
out_s = [f for f in dirty if f in KNOWN_OUT]
other = [f for f in dirty if f not in IN_SCOPE and f not in KNOWN_OUT]
print(f"IN-SCOPE dirty ({len(in_s)}):");  [print("  +", f) for f in in_s]
print(f"OUT-OF-SCOPE pre-existing ({len(out_s)}) — NAO commitar neste bloco:"); [print("  !", f) for f in out_s]
print(f"OTHER untracked/unclassified ({len(other)}):"); [print("  ?", f) for f in other]
