#!/usr/bin/env python3
"""Auditoria forward do Engine de B v1.1 (pedido Cris 2026-08-19): todos os registos do forward_log,
painel completo N·WR·sumR·streak + estado ON/off por dia. Read-only; consome o log existente."""
import json
from pathlib import Path

LOG = Path(__file__).resolve().parent / "forward_log.jsonl"


def main():
    rows = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()] if LOG.exists() else []
    print(f"registos totais no forward_log: {len(rows)}")
    on = [r for r in rows if r.get("engine")]
    print(f"engine ON (candidato real): {len(on)}  ·  off/skip: {len(rows) - len(on)}")
    res = {"WIN": 0, "LOSS": 0, "OPEN": 0}
    seq = []
    for r in on:
        o = (r.get("outcome") or r.get("status") or "OPEN").upper()
        o = o if o in res else "OPEN"
        res[o] += 1
        e = r.get("entry", {})
        seq.append((r.get("fundo_dt"), e.get("ent"), e.get("sl"), e.get("tgt"), o))
    print(f"resultados: {res['WIN']}W-{res['LOSS']}L-{res['OPEN']}O")
    sumr = res["WIN"] * 3 - res["LOSS"]
    print(f"sumR (3R fixo): {sumr:+.0f}R")
    streak = mx = 0
    for _, _, _, _, o in seq:
        if o == "LOSS":
            streak += 1; mx = max(mx, streak)
        elif o == "WIN":
            streak = 0
    print(f"pior streak L: {mx}")
    print("\ncandidatos (fundo_dt · entry · SL · tgt · outcome):")
    for s in seq:
        print("  ", *s)
    offs = {}
    for r in rows:
        if not r.get("engine"):
            k = str(r.get("reason") or r.get("status"))[:48]
            offs[k] = offs.get(k, 0) + 1
    print("\nmotivos off/skip:")
    for k, v in sorted(offs.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")


if __name__ == "__main__":
    main()
