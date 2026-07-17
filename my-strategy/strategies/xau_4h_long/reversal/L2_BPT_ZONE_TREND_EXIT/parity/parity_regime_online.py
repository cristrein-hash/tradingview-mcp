#!/usr/bin/env python3
"""V-1 — PARIDADE FSM DE REGIME (l2_engine vs phase10 original) + prefix-stability.

Gates (fail-loud):
  G1: reg array run(0.03,1.15,0.88) do engine == phase10.run(0.03,1.15,0.88) (barra a barra)
  G2: segmentos (era >=2023) byte-idênticos (json.dumps ==) ao builder do phase10 (P.out)
  G3: onsets BEAR — existe segmento BEAR com d0==2023-05-25 e com d0 in {2026-01-29,2026-01-30}
  G4: prefix-stability — truncando a história em cada uma das últimas K barras (default 300),
      nenhum rótulo passado muda (reg_trunc[i] == reg_full[i] para todo i < m)

Uso: python3 parity_regime_online.py [K_prefix]
"""
import json, sys, io, contextlib
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import l2_engine as E

RAW_PATH = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"


def load(p):  # mesmo contrato do phase10 load() (fonte: phase10_hybrid_regime.py:10)
    b = [json.loads(l) for l in p.read_text().splitlines()]
    b.sort(key=lambda x: x["t"])
    return b


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    B4 = load(RAW_PATH)
    n = len(B4)
    print(f"bars: {n} (t0={B4[0]['t']} tN={B4[-1]['t']})")

    fsm = E.make_regime_fsm(B4)
    reg_e = fsm["run"](0.03, 1.15, 0.88)
    segs_e = fsm["build_segments"](reg_e)

    # -------- original phase10 --------
    sys.path.insert(0, str(REPO / "regime_turnstate_engine/validation"))
    with contextlib.redirect_stdout(io.StringIO()):
        import phase10_hybrid_regime as P
    reg_p = P.run(0.03, 1.15, 0.88)
    segs_p = P.out  # builder de segmentos do phase10 (linhas 119-133)

    # G1
    diff = [i for i in range(n) if reg_e[i] != reg_p[i]]
    g1 = not diff
    print(f"G1 reg-array igual: {'PASS' if g1 else 'FAIL'}" + ("" if g1 else f" — {len(diff)} diffs, primeiro i={diff[0]} ({reg_e[diff[0]]} vs {reg_p[diff[0]]})"))

    # G2
    je, jp = json.dumps(segs_e, sort_keys=True), json.dumps(segs_p, sort_keys=True)
    g2 = je == jp
    print(f"G2 segmentos byte-idênticos (>=2023): {'PASS' if g2 else 'FAIL'} — engine {len(segs_e)} segs, phase10 {len(segs_p)} segs")
    if not g2:
        for a, b in zip(segs_e, segs_p):
            if a != b:
                print("  primeiro diff:\n   engine :", a, "\n   phase10:", b)
                break

    # G3
    bear_d0 = [s['d0'] for s in segs_e if s['regime'] == 'BEAR']
    g3a = '2023-05-25' in bear_d0
    g3b = any(d in bear_d0 for d in ('2026-01-29', '2026-01-30'))
    g3 = g3a and g3b
    print(f"G3 onsets BEAR: {'PASS' if g3 else 'FAIL'} — 2023-05-25 {'ok' if g3a else 'AUSENTE'}; 2026-01-29/30 {'ok' if g3b else 'AUSENTE'}")
    print(f"   BEAR d0s: {bear_d0}")

    # G4 prefix-stability
    bad = []
    for m in range(n - K, n):
        fsm_t = E.make_regime_fsm(B4[:m])
        reg_t = fsm_t["run"](0.03, 1.15, 0.88)
        for i in range(m):
            if reg_t[i] != reg_e[i]:
                bad.append((m, i, reg_t[i], reg_e[i]))
                break
        if (m - (n - K)) % 50 == 0:
            print(f"   prefix {m - (n - K) + 1}/{K}...", flush=True)
    g4 = not bad
    print(f"G4 prefix-stability (últimas {K} barras): {'PASS' if g4 else 'FAIL'}")
    if bad:
        for m, i, a, b in bad[:5]:
            print(f"   trunc@{m}: reg[{i}] {a} != {b}")

    ok = g1 and g2 and g3 and g4
    print(f"\nV-1 RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
