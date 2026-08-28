#!/usr/bin/env python3
"""FORWARD LABELER — etiqueta automática dos sinais LONG com (phase, score) do distrib_tracker no envio
(FORWARD_PREREG_DISTRIB.md; aplica ordem Cris 28/08 item 2). Semanal via launchd; idempotente por (src,t).
LÊ ledgers existentes — não emite, não altera, não decide. Resolução R fica para a avaliação final.
Fontes: a1a2 alerted.jsonl · AMD amd_setups.jsonl (pinged long) · L1 l1_cycle.log (ciclos não-no_candidate).
py3 stdlib."""
import json
import time
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
TRK = REPO / "alert-bridge/logs/distrib_tracker.jsonl"
OUTF = Path(__file__).resolve().parent / "forward_labels.jsonl"
T0 = 1787875200          # 2026-08-28 00:00 UTC — início do forward (nada antes conta)
MAX_DELTA = 300


def _jl(p):
    try:
        return [json.loads(x) for x in open(p).read().splitlines() if x.strip()]
    except Exception:
        return []


def signals():
    out = []
    for r in _jl(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl"):
        t = r.get("entry_t")
        if t and t >= T0:
            out.append(dict(src="a1a2_" + (r.get("layer") or "?"), t=t, ent=r.get("ent"), sl=r.get("sl")))
    for r in _jl(REPO / "my-strategy/strategies/xau_amd/amd_live/.amd_state/amd_setups.jsonl"):
        if r.get("dir") != "long" or not r.get("candidates_pinged"):
            continue
        t = r.get("h4_bar_t")
        if t and t >= T0:
            out.append(dict(src="amd_long", t=t, setup_id=r.get("setup_id")))
    for r in _jl(REPO / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/.l1_state/l1_cycle.log"):
        t = r.get("ts")
        dec = str(r.get("decision") or r.get("status") or "")
        if t and t >= T0 and dec and "no_candidate" not in dec and "error" not in dec:
            out.append(dict(src="l1", t=int(t), decision=dec))
    return out


def main():
    ticks = [x for x in _jl(TRK) if x.get("logged_at")]
    done = {(r["src"], r["t"]) for r in _jl(OUTF)}
    new = []
    for s in signals():
        if (s["src"], s["t"]) in done:
            continue
        near = min(ticks, key=lambda x: abs(x["logged_at"] - s["t"])) if ticks else None
        d = abs(near["logged_at"] - s["t"]) if near else None
        rec = dict(s, labeled_at=int(time.time()))
        if near and d <= MAX_DELTA:
            rec.update(phase=near.get("phase"), score=near.get("score"), comp=near.get("comp"), tick_delta_s=d)
        else:
            rec.update(phase=None, score=None, gap="SEM_TICK_%ss" % d)   # buraco declarado, nunca inventado
        new.append(rec)
    if new:
        with open(OUTF, "a") as f:
            for r in new:
                f.write(json.dumps(r) + "\n")
    print(f"forward-labeler: {len(new)} novos rótulos · total {len(done) + len(new)} · buracos "
          f"{sum(1 for r in new if r.get('gap'))}")


if __name__ == "__main__":
    main()
