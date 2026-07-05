#!/usr/bin/env python3
"""SM (Structure-Momentum designer) probe 0 — inspect data structures.

Read-only. Inspects:
- results/cris_repriced_map_20260704.json (repriced profile of the 35 manual ops)
- results/cris_manual_trades_20260704.json (t0s of the 35)
- primitives 15M location / bar series availability
- mtf sandbox (30M/1H) availability
"""
import json, os, glob

BASE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
SCRATCH = "/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad"

def main():
    rep = json.load(open(f"{BASE}/results/cris_repriced_map_20260704.json"))
    print("== repriced map keys:", list(rep.keys()))
    print("note:", rep.get("note"))
    print("n_ctrl:", rep.get("n_ctrl"))
    lifts = rep["lifts"]
    print("lifts type:", type(lifts), "len:", len(lifts))
    if isinstance(lifts, dict):
        for k, v in list(lifts.items())[:8]:
            print("  ", k, "->", v)
    elif isinstance(lifts, list):
        for v in lifts[:8]:
            print("  ", v)
    print("pairs sample:")
    pairs = rep["pairs"]
    if isinstance(pairs, dict):
        for k, v in list(pairs.items())[:5]:
            print("  ", k, "->", v)
    elif isinstance(pairs, list):
        for v in pairs[:5]:
            print("  ", v)

    man = json.load(open(f"{BASE}/results/cris_manual_trades_20260704.json"))
    print("\n== manual trades type:", type(man))
    if isinstance(man, dict):
        print("keys:", list(man.keys())[:20])
        for k, v in list(man.items())[:3]:
            print("  ", k, "->", str(v)[:300])
    elif isinstance(man, list):
        print("len:", len(man))
        print("first:", json.dumps(man[0], indent=1)[:800])

    # primitives 15M
    for pat in ["primitives*", "*primitives*"]:
        hits = glob.glob(f"{BASE}/{pat}")
        for h in hits:
            print("\n== primitives hit:", h, "dir" if os.path.isdir(h) else "file")
            if os.path.isdir(h):
                sub = sorted(os.listdir(h))
                print("   entries:", len(sub), sub[:15])

    # mtf sandbox
    mtf = f"{SCRATCH}/mtf_sandbox"
    print("\n== mtf_sandbox exists:", os.path.isdir(mtf))
    if os.path.isdir(mtf):
        for e in sorted(os.listdir(mtf)):
            p = os.path.join(mtf, e)
            print("  ", e, "dir" if os.path.isdir(p) else os.path.getsize(p))

if __name__ == "__main__":
    main()
