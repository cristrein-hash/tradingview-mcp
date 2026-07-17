#!/usr/bin/env python3
"""L2/BPT — SCANNER por ciclo (FASE 2 runtime). Autoridade única = l2_engine (motor paridade V-1..V-4).

Por ciclo:
  1. Recomputa FSM+segmentos sobre a HISTÓRIA INTEIRA do ledger (path-dependent desde 2020).
  2. GUARD prefix-stability: grava .runtime_state/l2_regime_segments.json e compara com o do
     ciclo anterior — se QUALQUER rótulo/segmento PASSADO mudou -> HARD_STOP sem alertas.
  3. Deteta candidato novo na(s) barra(s) fechada(s) nova(s): detector v2.2 (RAW truncado à barra
     = semântica online causal) -> prune V2 -> episódio gap<=6 (journal l2_candidates.jsonl)
     -> context_sl (dsq live das boxes DEMAND) -> keep() da zona -> ENTRY candidate.
  4. Devolve rótulo de regime por barra nova (p/ transições de posição no runtime).
  5. SEMPRE loga {regime_atual, zona_bear_deep, dist_preço_à_zona}.

Cadeia entry/sl com o quirk G4 (sl_atr round-2dp) preservado — ver parity_rederive_regua.py.
dsq live espelha demand_supply_quality.py (nd = max-by-high dos DEMAND hi<=p, senão inside[0];
touched = low<=nd_top na janela de 12 barras; valores 2dp como no CSV).

Notas de honestidade (documentadas em STRATEGY.md):
  - No frontier o RAW é truncado à barra avaliada (sem futuro). Acceptance é decision-invariant
    (o break bar já fecha acima do nível); PL5/swing_origin (só fallback LATE_WIDE_REVIEW)
    pode divergir do research que via 5 barras de futuro.
  - Em catch-up, as boxes DEMAND são as-of-AGORA (não as-of-bar) -> alerta marcado LATE + flag.

py3.9 stdlib. Sem MCP neste módulo (dados injetados pelo runtime).
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import l2_engine as E  # noqa: E402

STATE_DIR = HERE / ".runtime_state"
LEDGER_PATH = STATE_DIR / "l2_bars_4h.jsonl"
FEATURES_PATH = STATE_DIR / "l2_features.jsonl"
CANDS_PATH = STATE_DIR / "l2_candidates.jsonl"
SEGMENTS_PATH = STATE_DIR / "l2_regime_segments.json"

FSM_PARAMS = (0.03, 1.15, 0.88)          # config aprovada (V-1/V-2)
EPISODE_GAP = 6                          # sl_context_fullbase.py:6-12
DSQ_TOUCH_WIN = 12                       # demand_supply_quality.py WIN=12
WIDE_STOP_PTS = 80                       # flag advisory no alerta

_LBL = {"BULL": "U", "BEAR": "B", "RANGE": "R", None: "?"}
_LBL_INV = {v: k for k, v in _LBL.items()}


# ---------------------------------------------------------------------
# IO ledger / features / candidates (writes atómicos tmp+os.replace)
# ---------------------------------------------------------------------
def _atomic_write_lines(path, lines):
    p = Path(path); p.parent.mkdir(exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w") as f:
        for ln in lines:
            f.write(ln + "\n")
    os.replace(tmp, p)


def load_ledger(path=LEDGER_PATH):
    p = Path(path)
    if not p.exists():
        return []
    bars = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    bars.sort(key=lambda b: b["t"])
    return bars


def save_ledger(bars, path=LEDGER_PATH):
    _atomic_write_lines(path, [json.dumps(b, ensure_ascii=False) for b in bars])


def load_features(path=FEATURES_PATH):
    """{t: {'rsi':..., 'bubbles_recent':[...]}}; última linha por t ganha (append semantics)."""
    p = Path(path)
    out = {}
    if not p.exists():
        return out
    for ln in p.read_text().splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        out[r["t"]] = r
    return out


def save_features(feats_by_t, path=FEATURES_PATH):
    rows = [feats_by_t[t] for t in sorted(feats_by_t)]
    _atomic_write_lines(path, [json.dumps(r, ensure_ascii=False) for r in rows])


def load_candidate_idxs(path=CANDS_PATH):
    p = Path(path)
    if not p.exists():
        return []
    idxs = []
    for ln in p.read_text().splitlines():
        if ln.strip():
            idxs.append(json.loads(ln)["entry_idx"])
    return sorted(set(idxs))


def append_candidate(rec, path=CANDS_PATH):
    p = Path(path); p.parent.mkdir(exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------
# RAW builder (contrato do detector) e FSM
# ---------------------------------------------------------------------
def build_raw(ledger, feats_by_t):
    """RAW records do contrato do detector/sl_context a partir de ledger+features."""
    raw = []
    for b in ledger:
        f = feats_by_t.get(b["t"], {})
        raw.append({"ts_epoch": b["t"], "open": b["o"], "high": b["h"], "low": b["l"],
                    "close": b["c"], "volume": b.get("v", 0), "rsi": f.get("rsi"),
                    "bubbles_recent": f.get("bubbles_recent") or [],
                    "nas_recent": [], "smc_recent": []})
    return raw


def compute_regime(ledger):
    """FSM sobre a história inteira. Devolve (fsm, reg, segs)."""
    fsm = E.make_regime_fsm(ledger)
    reg = fsm["run"](*FSM_PARAMS)
    segs = E.prepare_segments(fsm["build_segments"](reg))
    return fsm, reg, segs


# ---------------------------------------------------------------------
# GUARD prefix-stability
# ---------------------------------------------------------------------
def prefix_guard(T, reg, segs, path=SEGMENTS_PATH, save=True):
    """Compara rótulos+segmentos com o snapshot do ciclo anterior. Qualquer mudança no
    PASSADO -> (False, detalhe). Se ok (e save=True), persiste o snapshot novo."""
    labels = "".join(_LBL.get(r, "?") for r in reg)
    cur = {"T": T, "labels": labels,
           "segments": [{k: s[k] for k in ("start", "end", "regime", "hi", "lo")} for s in segs]}
    p = Path(path)
    prev = None
    if p.exists():
        try:
            prev = json.loads(p.read_text())
        except Exception:
            return False, {"reason": "prefix_state_corrupto", "path": str(p)}
    if prev is not None:
        pT, pL = prev.get("T") or [], prev.get("labels") or ""
        if len(pT) > len(T):
            return False, {"reason": "ledger_encolheu", "prev_n": len(pT), "cur_n": len(T)}
        for i in range(len(pT)):
            if pT[i] != T[i]:
                return False, {"reason": "ledger_prefix_mudou", "i": i,
                               "prev_t": pT[i], "cur_t": T[i]}
            if i < len(pL) and pL[i] != labels[i]:
                return False, {"reason": "rotulo_passado_mudou", "i": i, "t": T[i],
                               "prev": _LBL_INV.get(pL[i]), "cur": _LBL_INV.get(labels[i])}
        ps = prev.get("segments") or []
        cs = cur["segments"]
        if len(ps) > len(cs):
            return False, {"reason": "segmentos_encolheram", "prev_n": len(ps), "cur_n": len(cs)}
        for i, s in enumerate(ps):
            c = cs[i]
            if i < len(ps) - 1:                      # segmentos FECHADOS: byte-iguais
                if s != c:
                    return False, {"reason": "segmento_passado_mudou", "i": i,
                                   "prev": s, "cur": c}
            else:                                    # último do snapshot: pode estender end/hi/lo
                if s["start"] != c["start"] or s["regime"] != c["regime"]:
                    return False, {"reason": "segmento_corrente_mudou_start_ou_regime",
                                   "i": i, "prev": s, "cur": c}
    if save:
        p.parent.mkdir(exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(cur))
        os.replace(tmp, p)
    return True, {"reason": "ok", "had_prev": prev is not None, "n": len(T)}


# ---------------------------------------------------------------------
# dsq live (espelho de demand_supply_quality.py — só os campos que o context_sl usa)
# ---------------------------------------------------------------------
def build_dsq_row(i, C, L, atr, demand_boxes, asof="bar"):
    """Campos do context_sl a partir das boxes DEMAND do chart (mesma semântica do CSV:
    nd = max-by-high dos DEMAND hi<=p, senão inside[0]; dist/valores round-2dp; touched
    = qualquer low em [i-12,i] <= nd_top). demand_boxes: [(hi,lo)...] na ordem do chart."""
    p = C[i]
    below = [(hi, lo) for hi, lo in demand_boxes if hi <= p]
    inside = [(hi, lo) for hi, lo in demand_boxes if lo <= p <= hi]
    nd = max(below, key=lambda b: b[0]) if below else (inside[0] if inside else None)
    if nd is None or not atr:
        return {"nearest_4h_demand_low": "", "dist_4h_demand_low_atr": "",
                "demand_4h_touched_on_retest": "0", "_dsq_asof": asof}
    d_low = round((p - nd[1]) / atr, 2)
    touched = any(L[j] <= nd[0] for j in range(max(0, i - DSQ_TOUCH_WIN), i + 1))
    return {"nearest_4h_demand_low": str(round(nd[1], 2)),
            "dist_4h_demand_low_atr": str(d_low),
            "demand_4h_touched_on_retest": "1" if touched else "0",
            "_dsq_asof": asof}


# ---------------------------------------------------------------------
# Avaliação de UMA barra (frontier/catch-up) — semântica online causal
# ---------------------------------------------------------------------
def evaluate_bar(ledger, feats_by_t, i, demand_boxes, cand_idxs, selector, segs,
                 dsq_row=None, asof="bar"):
    """Corre a cadeia candidato->prune->episódio->context_sl->keep na barra i (fechada).
    RAW truncado a i (sem futuro). Devolve dict com o resultado de cada gate."""
    res = {"ledger_idx": i, "bar_time": ledger[i]["t"], "stage": None,
           "candidate": None, "entry_candidate": None}
    raw = build_raw(ledger[:i + 1], feats_by_t)
    det = E.make_detector(raw)
    c = det["candidate_l2_v2_2"](i)
    if not (c and "pivot_idx" in c):
        res["stage"] = "no_candidate"
        res["reject"] = (c or {}).get("reject")
        return res
    res["candidate"] = {k: c[k] for k in ("entry_idx", "level", "source", "tipo",
                                          "variant", "score", "break_idx", "pivot_idx")}
    if det["prune_v2"](c):
        res["stage"] = "pruned"
        return res
    res["stage"] = "pruned_base_v2"
    res["journal_append"] = True                      # candidato sobrevivente entra no journal
    # episódio gap<=6: representante = PRIMEIRO (sem candidato pruned nas 6 barras anteriores)
    if any(i - EPISODE_GAP <= x <= i - 1 for x in cand_idxs):
        res["stage"] = "episode_member_not_rep"
        return res
    slc = E.make_sl_context(raw, {})
    atr = slc["ATR"][i]
    if not atr:
        res["stage"] = "no_atr"                        # reps filtram ATR (sl_context_fullbase:12)
        return res
    if dsq_row is None:
        dsq_row = build_dsq_row(i, slc["C"], slc["L"], atr, demand_boxes, asof=asof)
    res["dsq"] = dsq_row
    slc = E.make_sl_context(raw, {i: dsq_row})
    sl_raw, risk_raw, typ, dist = slc["context_sl"](i)
    if sl_raw is None:
        res["stage"] = "no_trade"
        res["no_trade_reason"] = typ                   # TOP_EXHAUSTION_NO_LONG
        return res
    # cadeia da régua (quirk G4): sl_atr round-2dp -> sl -> entry/risk 2dp
    entry = round(ledger[i]["c"], 2)
    sl_atr_r2 = round(risk_raw / atr, 2)
    sl = round(ledger[i]["c"] - sl_atr_r2 * atr, 2)
    risk = round(entry - sl, 2)
    res["regua"] = {"entry": entry, "sl": sl, "risk": risk, "sl_type": typ,
                    "dist_demand_atr": dist}
    kept, x = selector["keep_signal"](i, entry)
    res["stage"] = "kept" if kept else "zone_rejected"
    res["zone_context"] = None
    if x is not None:
        res["zone_context"] = {"regime": x["reg"], "pos": round(x["pos"], 3),
                               "ztop": [round(v, 2) for v in x["ztop"]] if x.get("ztop") else None,
                               "zdeep": [round(v, 2) for v in x["zdeep"]] if x.get("zdeep") else None}
    if kept:
        res["entry_candidate"] = {
            "bar_time": ledger[i]["t"], "ledger_idx": i,
            "entry": entry, "sl": sl, "risk": risk, "sl_type": typ,
            "dist_demand_atr": dist, "tipo": c["tipo"], "source": c["source"],
            "regime": x["reg"], "zona": res["zone_context"],
            "wide_stop": bool(risk > WIDE_STOP_PTS), "dsq_asof": asof,
        }
    return res


# ---------------------------------------------------------------------
# Painel de zona (sempre logado)
# ---------------------------------------------------------------------
def zone_panel(ledger, reg, segs, selector):
    """{regime_atual, zona_bear_deep, dist_preço_à_zona} — nasce útil (regime atual BEAR)."""
    if not ledger:
        return {"regime_atual": None}
    last = ledger[-1]
    regime_now = reg[-1]
    panel = {"regime_atual": regime_now, "last_bar_time": last["t"],
             "last_close": round(last["c"], 2), "zona_bear_deep": None,
             "dist_preco_a_zona": None}
    idx = selector["seg_idx"](last["t"])
    if regime_now == "BEAR" and idx is not None and idx > 0:
        zd = selector["bear_deep"](idx)
        if zd:
            panel["zona_bear_deep"] = [round(zd[0], 2), round(zd[1], 2)]
            panel["dist_preco_a_zona"] = round(last["c"] - zd[1], 2)  # >0 = acima do topo da zona
    return panel


# ---------------------------------------------------------------------
# run_cycle — chamado pelo runtime
# ---------------------------------------------------------------------
def run_cycle(ledger, feats_by_t, demand_boxes, new_bar_idxs,
              segments_path=SEGMENTS_PATH, cands_path=CANDS_PATH, save_guard=True):
    """Ciclo completo do scanner. new_bar_idxs: índices do ledger das barras fechadas NOVAS
    (ordem crescente; catch-up incluso). Devolve dict com guard/panel/labels/resultados."""
    fsm, reg, segs = compute_regime(ledger)
    T = fsm["T"]
    ok, gd = prefix_guard(T, reg, segs, path=segments_path, save=save_guard)
    if not ok:
        return {"status": "blocked_prefix_instability", "guard": gd}
    selector = E.make_selector(segs, T, fsm["H"], fsm["L"])
    exitm = E.make_trend_exit(ledger, segs)           # regime_at verbatim (bisect por seg start)
    panel = zone_panel(ledger, reg, segs, selector)
    cand_idxs = load_candidate_idxs(cands_path)
    latest = len(ledger) - 1
    bar_results = []
    for i in new_bar_idxs:
        asof = "bar" if i == latest else "now"        # catch-up: boxes as-of-agora (honesto)
        r = evaluate_bar(ledger, feats_by_t, i, demand_boxes, cand_idxs, selector, segs,
                         asof=asof)
        r["regime_label"] = exitm["regime_at"](i)     # rótulo p/ transições de posição
        r["late_bars"] = latest - i
        if r.get("journal_append"):
            append_candidate({"entry_idx": i, "t": ledger[i]["t"],
                              "tipo": r["candidate"]["tipo"], "source": r["candidate"]["source"],
                              "stage": r["stage"]}, cands_path)
            cand_idxs = sorted(set(cand_idxs + [i]))
        if r.get("entry_candidate"):
            r["entry_candidate"]["late_bars"] = latest - i
        bar_results.append(r)
    return {"status": "ok", "guard": gd, "panel": panel, "bar_results": bar_results,
            "regime_labels": {ledger[i]["t"]: exitm["regime_at"](i) for i in new_bar_idxs}}


# ---------------------------------------------------------------------
# Rebuild do journal de candidatos (bootstrap/selftest) — semântica research (RAW inteiro)
# ---------------------------------------------------------------------
def rebuild_candidates_journal(ledger, feats_by_t, cands_path=CANDS_PATH):
    """Corre o gerador completo (research semantics) e reescreve o journal com a pruned base.
    Devolve (idxs, cands_by_idx)."""
    raw = build_raw(ledger, feats_by_t)
    det = E.make_detector(raw)
    cands = det["run_candidate_generator"]()
    kept = [c for c in cands if not det["prune_v2"](c)]
    rows = [{"entry_idx": c["entry_idx"], "t": raw[c["entry_idx"]]["ts_epoch"],
             "tipo": c["tipo"], "source": c["source"], "stage": "pruned_base_v2_rebuild"}
            for c in sorted(kept, key=lambda c: c["entry_idx"])]
    _atomic_write_lines(cands_path, [json.dumps(r, ensure_ascii=False) for r in rows])
    return [r["entry_idx"] for r in rows], {c["entry_idx"]: c for c in kept}


# ---------------------------------------------------------------------
# SELFTEST sobre o ledger seed (sem MCP)
# ---------------------------------------------------------------------
def _selftest_seed():
    import csv
    import tempfile
    REPO = HERE.parents[4]
    RAW4H = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
    FROZEN = (REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/"
              "repro_recovery/raw_features_2020_2026.jsonl")
    V1R = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
    PRUNED_CSV = V1R / "l2_bpt_v2_2_pruned_base_v2.csv"
    DSQ_CSV = V1R / "l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"
    REGUA_CSV = V1R / "l2_bpt_regua_structural.csv"

    tmpd = Path(tempfile.mkdtemp(prefix="l2_scanner_selftest_"))
    fails = []

    ledger = [json.loads(l) for l in open(RAW4H)]
    ledger.sort(key=lambda b: b["t"])
    frozen = [json.loads(l) for l in open(FROZEN)]
    feats = {r["ts_epoch"]: {"t": r["ts_epoch"], "rsi": r.get("rsi"),
                             "bubbles_recent": r.get("bubbles_recent") or []} for r in frozen}

    # G1: rebuild do journal reproduz a pruned base V2 (2965) byte-a-byte
    cpath = tmpd / "cands.jsonl"
    idxs, _by = rebuild_candidates_journal(ledger, feats, cpath)
    csv_kept = sorted(int(r["candidate_id"][1:]) for r in csv.DictReader(open(PRUNED_CSV)))
    g1 = idxs == csv_kept
    print(f"G1 journal==pruned_base_V2: {'PASS' if g1 else 'FAIL'} ({len(idxs)} vs {len(csv_kept)})")
    if not g1:
        fails.append("G1")
    print(f"   último candidato: idx={idxs[-1]} t={ledger[idxs[-1]]['t']}")

    # G2: frontier path reproduz as últimas barras da régua (dsq do CSV, RAW truncado)
    regua = {int(r["bar_idx"]): r for r in csv.DictReader(open(REGUA_CSV))}
    dsq_all = {int(r["candidate_id"][1:]): r for r in csv.DictReader(open(DSQ_CSV))}
    fsm, reg, segs = compute_regime(ledger)
    selector = E.make_selector(segs, fsm["T"], fsm["H"], fsm["L"])
    last3 = sorted(regua)[-3:]
    for bi in last3:
        prior = [x for x in idxs if x < bi]
        r = evaluate_bar(ledger, feats, bi, [], prior, selector, segs,
                         dsq_row=dsq_all.get(bi), asof="csv")
        rg = regua[bi]
        ok_stage = r["stage"] in ("kept", "zone_rejected")   # régua=245 (pré-keep); kept = os 17
        ok_entry = r.get("regua") and r["regua"]["entry"] == float(rg["entry"])
        ok_sl = r.get("regua") and r["regua"]["sl"] == float(rg["sl"])
        tag = "PASS" if (ok_stage and ok_entry and ok_sl) else "FAIL"
        print(f"G2 frontier bar {bi}: {tag} stage={r['stage']} "
              f"entry {r.get('regua', {}).get('entry')} vs {rg['entry']} · "
              f"sl {r.get('regua', {}).get('sl')} vs {rg['sl']}")
        if tag == "FAIL":
            fails.append(f"G2:{bi}")

    # G3: prefix-guard não dispara em corrida repetida (mesmo ledger 2x)
    spath = tmpd / "segments.json"
    ok1, d1 = prefix_guard(fsm["T"], reg, segs, path=spath)
    ok2, d2 = prefix_guard(fsm["T"], reg, segs, path=spath)
    g3 = ok1 and ok2 and d2.get("had_prev")
    print(f"G3 prefix-guard idempotente: {'PASS' if g3 else 'FAIL'} ({d1} / {d2})")
    if not g3:
        fails.append("G3")

    # G4: guard DISPARA se um rótulo passado mudar (sanidade do próprio guard)
    reg_mut = list(reg)
    reg_mut[100] = "BEAR" if reg_mut[100] != "BEAR" else "BULL"
    ok3, d3 = prefix_guard(fsm["T"], reg_mut, segs, path=spath, save=False)
    g4 = not ok3
    print(f"G4 guard deteta mutação: {'PASS' if g4 else 'FAIL'} ({d3.get('reason')})")
    if not g4:
        fails.append("G4")

    # painel de zona (informativo)
    print("panel:", json.dumps(zone_panel(ledger, reg, segs, selector), ensure_ascii=False))
    print(f"SELFTEST SCANNER: {'PASS' if not fails else 'FAIL ' + str(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--selftest-seed" in sys.argv:
        sys.exit(_selftest_seed())
    print("uso: python3 scanner_l2.py --selftest-seed")
