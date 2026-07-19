#!/usr/bin/env python3
"""AMD F4 — loop de aprendizagem (Cris 2026-07-19). Junta os trades AMD do Cris (JOURNAL trades.jsonl, tag
verde '#N amd …') ↔ o setup que os gerou (amd_setups.jsonl) ↔ os candidatos FVG/OB que o sistema listou →
`amd_selection_gt.jsonl`: QUAL FVG/OB ele escolheu vs os oferecidos. Offline, read-only, on-demand/weekly.
NÃO mecaniza nada — pura MEDIÇÃO (o Cris continua o seletor). Só propor regra mecânica após N≥30-40 +
prereg+forward + gate do Cris. Link: token na tag (primário) ou proximidade (fallback). py3.9.
Uso: python3 amd_learn.py [--status]."""
import sys, json, re, datetime as dt
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
LEDGER = HERE / ".amd_state/amd_setups.jsonl"
GT = HERE / ".amd_state/amd_selection_gt.jsonl"
JTRADES = REPO / "copilot/journal/trades.jsonl"
GRACE_S = 6 * 3600          # tolerância pós-expiry para o entry manual


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def _link(trade, setups):
    """Liga um trade AMD ao seu setup. Primário=token na razão (nível+dir); fallback=proximidade temporal."""
    reason = (trade.get("reason") or "").lower(); tdir = trade.get("direction")
    det = trade.get("detected_epoch") or 0
    cand = [s for s in setups if s.get("dir") == tdir]
    # primário: a razão contém o número do nível do setup
    for s in cand:
        lvl = str(int(round(s.get("level", 0))))
        if lvl in reason and "amd" in reason:
            return s, "explicit"
    # fallback: setup armado antes do trade, dentro da janela+grace
    win = [s for s in cand if s.get("h4_bar_t", 0) <= det <= (s.get("window_expires_epoch", 0) + GRACE_S)]
    if win:
        return max(win, key=lambda s: s.get("h4_bar_t", 0)), "proximity"
    return None, "none"


def _features(trade, setup):
    cs = setup.get("candidates_latest", []) or []
    ent = trade.get("entry")
    chosen = min(cs, key=lambda c: abs((c.get("ent") or 0) - (ent or 0))) if cs else None
    return {
        "chosen": {k: trade.get(k) for k in ("entry", "sl", "tp", "rr", "direction", "reason", "outcome",
                                             "mfe_R", "mae_R", "bars_to_resolve")},
        "offered": cs, "n_candidates": len(cs),
        "chosen_candidate_id": chosen.get("candidate_id") if chosen else None,
        "chosen_off_menu": (chosen is None) or (abs((chosen.get("ent") or 0) - (ent or 0)) > 5),
        "chosen_status": chosen.get("status") if chosen else None,
        "features_of_choice": {
            "R_of_choice": trade.get("rr"),
            "dist_to_level": round(abs((ent or 0) - (setup.get("level") or 0)), 2),
            "dist_to_h4_close": round(abs((ent or 0) - (setup.get("h4_close") or 0)), 2),
        },
        "setup_context": {"bias": setup.get("bias"), "bias_layer1": setup.get("bias_layer1"),
                          "killzone": setup.get("killzone"), "level_kind": "PDL/PWL" if setup["dir"] == "long" else "PDH/PWH",
                          "close_pos": setup.get("close_pos")},
    }


def build_gt():
    trades = [t for t in _jl(JTRADES) if "amd" in (t.get("reason") or "").lower()]
    setups = _jl(LEDGER)
    rows = []
    for t in trades:
        s, conf = _link(t, setups)
        if not s:
            rows.append({"trade_id": t.get("trade_id"), "match_confidence": "none",
                         "chosen": {"entry": t.get("entry"), "outcome": t.get("outcome")}})
            continue
        rows.append({"setup_id": s["setup_id"], "trade_id": t.get("trade_id"), "match_confidence": conf,
                     "snapshot_ref": t.get("snapshot_ref"), **_features(t, s)})
    GT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""))
    return rows, len(trades)


def main():
    rows, n_amd = build_gt()
    linked = [r for r in rows if r.get("match_confidence") in ("explicit", "proximity")]
    print(f"AMD LEARN — trades AMD no journal: {n_amd} · ligados a setup: {len(linked)} "
          f"(explicit {sum(1 for r in linked if r['match_confidence']=='explicit')}/proximity {sum(1 for r in linked if r['match_confidence']=='proximity')})")
    if not linked:
        print("  (sem trades AMD ainda — o GT acumula à medida que operares e marcares #N amd <setup> fvgN)"); return
    on_menu = sum(1 for r in linked if not r.get("chosen_off_menu"))
    wins = sum(1 for r in linked if (r.get("chosen") or {}).get("outcome") == "WIN")
    res = [r for r in linked if (r.get("chosen") or {}).get("outcome") in ("WIN", "LOSS")]
    print(f"  cobertura: {on_menu}/{len(linked)} entradas dentro da lista de candidatos oferecidos")
    print(f"  resultado (resolvidos {len(res)}): {wins}W · WR {100*wins/max(1,len(res)):.0f}%")
    print(f"  → GT em {GT} (mecanizar só após N≥30-40 + prereg+forward + gate do Cris)")


if __name__ == "__main__":
    main()
