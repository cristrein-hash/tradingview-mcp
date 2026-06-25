#!/usr/bin/env python3
"""DA RE-AUDIT probe (read-only, self-restoring) for check_reader_sources.py ratchet.
Materialized to satisfy reproducibility guard. Runs adversarial tests:
  T1 new blind builder matching glob -> must FAIL (exit1)
  T2 new builder NOT matching glob (assembler-style) -> currently PASSES = HOLE
  T3 allowed_as_decision flipped YES -> must FAIL
  T4 outcome leak (mfe_r) in blind packet -> must FAIL
  T5 enumerate blind artifacts carrying blocked fields that the glob never scans
All mutations are reverted. Verified-at: 2026-06-23 DA re-audit.
"""
import subprocess, os, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
GATE = os.path.join(HERE, "check_reader_sources.py")
BLOCKED = ["sup_cat","pol_cat","clean_sky","nas_recent","smc_recent","bubbles_recent",
           "dist_4h_supply","dist_4h_demand","dist_poc","above_value","below_value"]

def run_gate():
    return subprocess.run([sys.executable, GATE], capture_output=True, text=True)

def t1_new_builder_in_glob():
    p = os.path.join(V1, "l2_bpt_ZZDAtest_packet_blind_probe.py")
    open(p, "w").write('sup_cat = d["sup_cat"]\nclean_sky = d["clean_sky"]\n')
    try:
        r = run_gate(); return r.returncode == 1 and "NOVO uso" in r.stdout
    finally:
        os.remove(p)

def t2_new_builder_outside_glob():
    """Builder that embeds blocked field but filename escapes the glob."""
    p = os.path.join(V1, "l2_bpt_ZZDAtest_evil_assembler.py")
    open(p, "w").write('sup_cat = packet["sup_cat"]\n')
    try:
        r = run_gate(); detected = r.returncode == 1 and "NOVO uso" in r.stdout
        return detected  # EXPECT False -> hole
    finally:
        os.remove(p)

def t3_decision_yes():
    mf = os.path.join(HERE, "reader_raw_source_manifest.yaml")
    orig = open(mf).read()
    open(mf, "w").write(orig.replace("allowed_as_decision: NO", "allowed_as_decision: YES", 1))
    try:
        r = run_gate(); return r.returncode == 1 and "allowed_as_decision != NO" in r.stdout
    finally:
        open(mf, "w").write(orig)

def t4_outcome_leak():
    p = os.path.join(V1, "results", "blind_pack_cluster2", "reading_packet_BLIND.md")
    orig = open(p).read()
    open(p, "w").write(orig + "\nmfe_r = 4.2R is_runner=True\n")
    try:
        r = run_gate(); return r.returncode == 1 and "outcome estruturado" in r.stdout
    finally:
        open(p, "w").write(orig)

def t5_unscanned_blind_artifacts():
    scan = set(glob.glob(os.path.join(V1, "l2_bpt_*packet*blind*.py")) +
               glob.glob(os.path.join(V1, "l2_bpt_blind_pack*.py")) +
               glob.glob(os.path.join(V1, "l2_bpt_reading_context_dump.py")) +
               glob.glob(os.path.join(V1, "results", "blind_pack_*", "reading_packet_BLIND.md")))
    candidates = (glob.glob(os.path.join(V1, "l2_bpt_*assembler*.py")) +
                  glob.glob(os.path.join(V1, "results", "blind_pack_*", "reader_dossier_FROZEN.md")) +
                  glob.glob(os.path.join(V1, "results", "blind_pack_*", "manifest.json")) +
                  glob.glob(os.path.join(V1, "results", "l2_bpt_reader_dossier_276.jsonl")) +
                  glob.glob(os.path.join(V1, "results", "l2_bpt_episode_context_packets_276.jsonl")))
    escapees = []
    for f in candidates:
        if f in scan:
            continue
        try:
            txt = open(f, errors="ignore").read()
        except Exception:
            continue
        hits = sorted({b for b in BLOCKED if b in txt})
        if hits:
            escapees.append((os.path.relpath(f, V1), hits))
    return escapees

if __name__ == "__main__":
    print("T1 new builder IN glob -> FAIL expected:", "PASS" if t1_new_builder_in_glob() else "BROKEN")
    print("T2 new builder OUTSIDE glob detected? (False = HOLE):", t2_new_builder_outside_glob())
    print("T3 allowed_as_decision=YES -> FAIL expected:", "PASS" if t3_decision_yes() else "BROKEN")
    print("T4 outcome leak -> FAIL expected:", "PASS" if t4_outcome_leak() else "BROKEN")
    print("T5 UNSCANNED blind artifacts carrying blocked fields:")
    for rel, hits in t5_unscanned_blind_artifacts():
        print(f"    HOLE {rel}: {hits}")
