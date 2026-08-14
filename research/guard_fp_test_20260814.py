#!/usr/bin/env python3
"""TESTE DE FALSO-POSITIVO do guard-CHoCH (Cris 14/08): funcional ou feature lixo?
Nos dias de ALTA (comprar dip funcionou) — quantos longs VENCEDORES (outcome=TP) o guard bloquearia
por engano? E nos dias de queda — quantos PERDEDORES (SL) apanharia (acerto)?
Usa outcomes REAIS (e2_outcomes.jsonl) + a função CHoCH do próprio E0 (causal, sem lookahead). Read-only."""
import json, sys, datetime
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import context_structure as CS
import store_reader as SR

OUT = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/e2_outcomes.jsonl"
UP_DAYS = {"2026-08-05", "2026-08-10", "2026-08-11"}   # dias em que comprar o dip funcionou
DN_DAY = {"2026-08-13"}                                  # o dia da faca


def struct_at(bars, t):
    sub = [b for b in bars if b["t"] <= t]
    if len(sub) < 20:
        return None
    return CS.structure([b["h"] for b in sub], [b["l"] for b in sub], [b["c"] for b in sub])


def epoch_from_id(cid):
    try:
        return int(cid.split("_")[1])
    except Exception:
        return 0


def guard_blocks(t, b60, b240):
    s60 = struct_at(b60, t); s240 = struct_at(b240, t)
    return bool((s60 or {}).get("choch", {}).get("dn") or (s240 or {}).get("choch", {}).get("dn"))


def main():
    b60 = SR.bars("60", 6000) or []
    b240 = SR.bars("240", 6000) or []
    rows = []
    for l in open(OUT):
        l = l.strip()
        if not l:
            continue
        d = json.loads(l)
        if d.get("direction") != "LONG":
            continue
        if d.get("outcome") not in ("TP", "SL"):
            continue
        day = d.get("date_lx", "")
        t = epoch_from_id(d.get("candidate_id", ""))
        if not t:
            continue
        grp = "UP" if day in UP_DAYS else ("DN" if day in DN_DAY else None)
        if grp is None:
            continue
        rows.append((grp, day, t, d["outcome"]))

    for grp, label in (("UP", "DIAS DE ALTA (comprar dip funcionou) — falso-positivo?"),
                       ("DN", "DIA DA FACA (13/08) — acerto?")):
        rs = [r for r in rows if r[0] == grp]
        wins = [r for r in rs if r[3] == "TP"]
        loss = [r for r in rs if r[3] == "SL"]
        win_blk = sum(1 for r in wins if guard_blocks(r[2], b60, b240))
        loss_blk = sum(1 for r in loss if guard_blocks(r[2], b60, b240))
        print("\n=== %s ===" % label)
        print("  longs vencedores (TP): %d | bloqueados pelo guard = %d  → FALSO-POSITIVO %s" % (
            len(wins), win_blk, "%.0f%%" % (100 * win_blk / len(wins)) if wins else "n/a"))
        print("  longs perdedores (SL): %d | bloqueados pelo guard = %d  → acerto %s" % (
            len(loss), loss_blk, "%.0f%%" % (100 * loss_blk / len(loss)) if loss else "n/a"))
    print("\n(FP alto nos dias de alta = estrangula bons longs = FEATURE LIXO. FP baixo + apanha perdedores = FUNCIONAL.)")


if __name__ == "__main__":
    main()
