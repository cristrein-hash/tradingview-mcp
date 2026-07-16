#!/usr/bin/env python3
"""E2 — QUALITY READER (Camada 2, P5). SHADOW: 0 Telegram. Consome candidatos MATERIAIS do E1
(logs/e1_candidates.jsonl, por byte-offset), aplica VETOS DETERMINÍSTICOS (Sub-fase A, 0 tokens) sobre o
dossiê VIVO (opção A: lê market_context.json no instante + guarda de deriva), e produz veredito graduado
(strong/watch/discard) em logs/e2_verdicts.jsonl. Ensemble adversarial (Sub-fase B) = atrás de flag
E2_ENSEMBLE (default OFF, gasta Claude). Vetos = funções PURAS f(cand, dossier). py3.9.
CLI: --once · --survey [--replay] · --anchors · --selftest · (default) daemon.
"""
import os, sys, json, time, datetime as dt
from pathlib import Path
BASE = Path(__file__).resolve().parent
REPO = BASE.parent
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
DOSSIER = REPO / "external_factors_v2" / "snapshots" / "market_context.json"
CAND_F = LOGS / "e1_candidates.jsonl"
VERD_F = LOGS / "e2_verdicts.jsonl"
OFFSET_F = LOGS / "e2_offset.json"
STATE_F = LOGS / "e2_state.json"
PIDFILE = LOGS / "e2_quality.pid"
PAUSE_LOCAL = LOGS / "monitor.pause"
PAUSE_GLOBAL = Path("/tmp/claude_recheck.paused")
FLOOR_S = 20

CFG = {"MIN_RR_E2": 2.0, "MAX_CHASE_ATR": 1.5, "DEAD_SESSIONS": {"dead_zone", "asia", "other"},
       "POS_EXTREME": 0.15, "BUY_DENS_MIN": 0.25, "ACT_DENS_CLIMAX": 0.82, "LEG_SELL_MIN": 180,
       "RSI_LOW": 35.0, "RSI_HIGH": 65.0, "EXHAUSTION_MIN": 1, "DRIFT_MAX_CYCLES": 2, "MIN_CONF_SYNTH": 4,
       "MIN_CONFLUENCE": 2, "CYCLE_S": 60}


def now_iso(): return dt.datetime.now(dt.timezone.utc).isoformat()
def fnum(x):
    try: return float(str(x).replace("−", "-").replace("K", "e3").replace(" ", ""))
    except Exception: return None


# ---------- helpers de dossiê ----------
def catalyst(dsr):
    ng = (dsr["axes"].get("macro") or {}).get("news_gate", {}) or {}
    imm = (dsr["axes"].get("macro") or {}).get("imminent_events", []) or []
    ff = fnum(ng.get("ff_event_le_min"))
    return bool(ng.get("high_impact_now") or (ff is not None and ff <= 30)
               or any((fnum(e.get("hours_until")) or 99) <= 1 for e in imm))


def regime(dsr):
    mtf = dsr["axes"].get("mtf", {})
    ts = [mtf.get(t, {}).get("trend") for t in ("1D", "240")]
    if "DOWN" in ts and "UP" not in ts: return "DOWN"
    if "UP" in ts and "DOWN" not in ts: return "UP"
    return "RANGE"


def atr_of(leg):
    if not leg or not leg.get("mag_atr"): return None
    try: return (leg["high"] - leg["low"]) / leg["mag_atr"]
    except Exception: return None


# ---------- 6 vetos (puros) ----------
def veto_session_vacuum(cand, dsr):
    ng = (dsr["axes"].get("macro") or {}).get("news_gate", {}) or {}
    sess = ng.get("session"); cat = catalyst(dsr)
    fired = (sess in CFG["DEAD_SESSIONS"]) and not cat
    return {"name": "session_vacuum", "hard": True, "fired": fired, "value": sess,
            "reason": f"vácuo: sessão {sess} sem catalisador" if fired else ""}


def veto_no_catalyst(cand, dsr):
    cat = catalyst(dsr); br = cand.get("materiality", {}).get("confluence_breakdown", {})
    fired = (not cat) and ((cand.get("rule") == "macro_event") or
                           (cand.get("materiality", {}).get("confluence") == CFG["MIN_CONFLUENCE"] and br.get("macro", 1) == 0))
    return {"name": "no_catalyst", "hard": False, "fired": fired, "value": cat,
            "reason": "sinal sem catalisador/gasolina" if fired else ""}


def veto_bad_rr(cand, dsr):
    # RR-only: o E1 já põe target = próxima zona OU 3R; um target 3R = runway limpo (sem zona oposta
    # em 3R) = POSITIVO. Só veta RR realmente pequeno (alvo perto demais).
    rr = fnum(cand.get("rr"))
    fired = rr is None or rr < CFG["MIN_RR_E2"]
    return {"name": "bad_rr", "hard": True, "fired": fired, "value": rr,
            "reason": f"RR {rr} < {CFG['MIN_RR_E2']} (alvo perto demais)" if fired else ""}


def veto_chase(cand, dsr):
    sl_atr = fnum(cand.get("materiality", {}).get("sl_atr"))
    chase = (sl_atr - 0.1) if sl_atr is not None else None
    fired = chase is not None and chase > CFG["MAX_CHASE_ATR"]
    return {"name": "chase", "hard": True, "fired": fired, "value": round(chase, 2) if chase is not None else None,
            "reason": f"entry a {round(chase,2)}×ATR do nível (perseguição)" if fired else ""}


def veto_stale(cand, dsr, drift_cycles):
    sh = dsr.get("source_health", {})
    bad = []
    if sh.get("mtf", {}).get("status") != "fresh": bad.append("mtf")
    if sh.get("micro_15m", {}).get("status") != "fresh": bad.append("micro")
    if cand.get("rule") == "macro_event" and sh.get("macro", {}).get("status") != "fresh": bad.append("macro")
    if drift_cycles is not None and drift_cycles > CFG["DRIFT_MAX_CYCLES"]: bad.append(f"drift{drift_cycles}")
    fired = bool(bad)
    return {"name": "stale_dossier", "hard": True, "fired": fired, "value": bad,
            "reason": f"dossiê stale: {bad}" if fired else ""}


def veto_counter_regime(cand, dsr):
    direction = cand.get("direction"); reg = regime(dsr); tf = cand.get("tf")
    counter = (direction == "LONG" and reg == "DOWN") or (direction == "SHORT" and reg == "UP")
    if not counter:
        return {"name": "counter_regime_no_exhaustion", "hard": True, "fired": False, "value": {"counter": False},
                "reason": ""}
    m = dsr["axes"].get("mtf", {}); micro = dsr["axes"].get("micro_15m", {}) or {}
    conf = (dsr["axes"].get("confluence") or {}).get("15", {}) or {}
    leg = (m.get(tf, {}) or {}).get("leg") or (m.get("15", {}) or {}).get("leg") or {}
    choch = (m.get(tf, {}) or {}).get("choch", {})
    pos = leg.get("pos_in_leg"); rsi = fnum(micro.get("rsi"))
    sig = []
    if cand.get("rule") == "sweep_reclaim" or (choch.get("up") if direction == "LONG" else choch.get("dn")):
        sig.append("structure_reversal")
    if pos is not None and ((direction == "LONG" and pos <= CFG["POS_EXTREME"]) or (direction == "SHORT" and pos >= 1 - CFG["POS_EXTREME"])):
        sig.append("pos_extreme")
    if direction == "LONG" and fnum(conf.get("buy_dens")) and fnum(conf.get("buy_dens")) >= CFG["BUY_DENS_MIN"] and fnum(conf.get("act_dens")) and fnum(conf.get("act_dens")) >= CFG["ACT_DENS_CLIMAX"]:
        sig.append("auction_capitulation")
    if direction == "SHORT" and ((fnum((conf.get("sell") or {}).get("dens")) or 0) >= CFG["BUY_DENS_MIN"] or (fnum(conf.get("leg_sell")) or 0) >= CFG["LEG_SELL_MIN"]):
        sig.append("auction_capitulation")
    nas = micro.get("nas", {}) or {}
    if (fnum(nas.get("bottom")) if direction == "LONG" else fnum(nas.get("top"))):
        sig.append("nas")
    if cand.get("materiality", {}).get("confluence_breakdown", {}).get("momentum", 0) >= 1 and rsi is not None and ((direction == "LONG" and rsi <= CFG["RSI_LOW"]) or (direction == "SHORT" and rsi >= CFG["RSI_HIGH"])):
        sig.append("momentum_turn")
    fired = len(sig) < CFG["EXHAUSTION_MIN"]
    return {"name": "counter_regime_no_exhaustion", "hard": True, "fired": fired,
            "value": {"counter": True, "signatures": sig},
            "reason": f"contra-regime {reg} sem exaustão (sig={sig})" if fired else ""}


def evaluate_vetos(cand, dsr, drift_cycles):
    vs = [veto_session_vacuum(cand, dsr), veto_no_catalyst(cand, dsr), veto_bad_rr(cand, dsr),
          veto_chase(cand, dsr), veto_stale(cand, dsr, drift_cycles), veto_counter_regime(cand, dsr)]
    hard = [v for v in vs if v["fired"] and v["hard"]]
    soft = [v for v in vs if v["fired"] and not v["hard"]]
    grade = "discard" if hard else ("watch" if soft else "survivor")
    return grade, vs, hard, soft


# ---------- veredito ----------
def make_verdict(cand, dsr, drift_cycles):
    grade, vs, hard, soft = evaluate_vetos(cand, dsr, drift_cycles)
    sh = dsr.get("source_health", {})
    return {"candidate_id": cand.get("id"), "ts": now_iso(), "cycle_ts": cand.get("cycle_ts"),
            "bar_time": cand.get("bar_time"), "direction": cand.get("direction"), "rule": cand.get("rule"),
            "tf": cand.get("tf"), "grade": grade, "veto": (hard[0]["name"] if hard else None),
            "vetos_all": vs, "ensemble": None, "dossier_drift_cycles": drift_cycles,
            "source_health": {k: sh.get(k, {}).get("status") for k in ("mtf", "micro_15m", "macro")},
            "levels": {"entry": cand.get("entry"), "sl": cand.get("sl"), "target": cand.get("target"), "rr": cand.get("rr")}}


def is_material(c):
    return c.get("suppressed") is None and c.get("materiality", {}).get("pass") is True


def load_dossier():
    try: return json.loads(DOSSIER.read_text())
    except Exception: return None


def drift_cycles(cand, dsr):
    dc = dsr.get("_meta", {}).get("cycle_ts"); cc = cand.get("cycle_ts")
    if dc and cc: return round((dc - cc) / CFG["CYCLE_S"])
    return None


def append(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ---------- CLI ----------
def cli_once():
    dsr = load_dossier()
    if not dsr: print("sem dossiê vivo"); return
    n = 0
    for line in CAND_F.read_text().splitlines() if CAND_F.exists() else []:
        try: c = json.loads(line)
        except Exception: continue
        if not is_material(c): continue
        v = make_verdict(c, dsr, drift_cycles(c, dsr)); append(VERD_F, v); n += 1
        print(f"  {v['direction']} {v['rule']} {v['tf']} -> {v['grade']}" + (f" [veto {v['veto']}]" if v['veto'] else ""))
    print(f"processados {n} materiais (nota: dossiê vivo pode ter derivado dos candidatos históricos)")


def cli_survey(use_replay):
    if not use_replay:
        print("--survey sem --replay: usa o dossiê vivo (deriva alta p/ candidatos históricos). Preferir --replay."); return
    import e1_replay, e1_detector as e1
    data = e1_replay.capture()
    d15 = data["15"]; N = len(d15["C"]); start = max(45, N - 120)
    from collections import Counter
    surv = Counter(); killed = Counter(); total = 0; prev = None
    for i in range(start, N):
        dsr = e1_replay.synth(data, i)
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr)
            c["cycle_ts"] = dsr["_meta"]["cycle_ts"]
            if not is_material(c): continue
            total += 1
            grade, vs, hard, soft = evaluate_vetos(c, dsr, 0)
            if grade == "survivor": surv[f"{c['direction']}/{c['rule']}"] += 1
            elif hard: killed[hard[0]["name"]] += 1
        prev = dsr
    print(f"=== SURVEY (replay de hoje) ===\n materiais: {total} | sobreviventes: {sum(surv.values())} | descartados: {sum(killed.values())}")
    print(" sobreviventes por regra:", dict(surv))
    print(" mortos por veto:", dict(killed))
    print(f" -> ~{sum(surv.values())} chamadas Claude/dia neste dia (tendência forte); dias normais menos.")


def cli_anchors():
    import e1_replay, e1_detector as e1
    # ANCORA A: short de hoje passa a Sub-fase A
    data = e1_replay.capture(); d15 = data["15"]; N = len(d15["C"]); start = max(45, N - 120)
    peak_i = max(range(start, N), key=lambda k: d15["C"][k]); prev = None; a_pass = False
    for i in range(start, N):
        dsr = e1_replay.synth(data, i)
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr); c["cycle_ts"] = dsr["_meta"]["cycle_ts"]
            if is_material(c) and c["direction"] == "SHORT" and i >= peak_i:
                grade, vs, hard, soft = evaluate_vetos(c, dsr, 0)
                if grade == "survivor": a_pass = True
        prev = dsr
    print(f"ANCHOR A (short-de-hoje sobrevive Sub-fase A): {'PASS' if a_pass else 'FALHA'}")
    # ANCORA B: SL de hoje (LONG Ásia-morta contra bear, sem exaustão) -> vetado
    b = {"direction": "LONG", "rule": "ema_reclaim", "tf": "15", "entry": 4035.3, "sl": 4027.0,
         "target": 4051.9, "rr": 2.0, "materiality": {"sl_atr": 1.0, "confluence": 3,
         "confluence_breakdown": {"macro": 0, "momentum": 0}}}
    bd = {"_meta": {"cycle_ts": 1}, "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}, "macro": {"status": "fresh"}},
          "axes": {"mtf": {"1D": {"trend": "DOWN"}, "240": {"trend": "DOWN"}, "15": {"leg": {"low": 4024, "high": 4064, "mag_atr": 4.0, "pos_in_leg": 0.4}, "choch": {"up": False, "dn": False}, "zones": {"below": None, "above": {"high": 4051, "low": 4049}}}},
                   "micro_15m": {"close": 4035.3, "rsi": "45", "rsi_ma": "48", "nas": {"bottom": "0"}},
                   "macro": {"risk_level": "normal", "imminent_events": [], "news_gate": {"session": "dead_zone", "high_impact_now": False, "ff_event_le_min": None}},
                   "confluence": {"15": {"buy_dens": 0.0, "act_dens": 0.1, "leg_sell": 5}}}}
    grade, vs, hard, soft = evaluate_vetos(b, bd, 0)
    names = [v["name"] for v in hard]
    b_pass = grade == "discard" and "session_vacuum" in names and "counter_regime_no_exhaustion" in names
    print(f"ANCHOR B (SL-Ásia-morta vetado por vácuo+contra-regime): {'PASS' if b_pass else 'FALHA'} (grade {grade}, hard {names})")
    ok = a_pass and b_pass
    print("ÂNCORAS:", "PASS" if ok else "FALHA")
    return 0 if ok else 1


def cli_selftest():
    # cada veto isolado
    base_d = {"_meta": {"cycle_ts": 1}, "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}, "macro": {"status": "fresh"}},
              "axes": {"mtf": {"1D": {"trend": "DOWN"}, "240": {"trend": "DOWN"}, "15": {"leg": {"low": 90, "high": 110, "mag_atr": 2.0, "pos_in_leg": 0.5}, "choch": {"up": False, "dn": False}, "zones": {"below": {"high": 88, "low": 86}, "above": {"high": 112, "low": 111}}}},
                       "micro_15m": {"close": 100, "rsi": "45", "rsi_ma": "48", "nas": {"bottom": "0", "top": "0"}},
                       "macro": {"risk_level": "normal", "imminent_events": [], "news_gate": {"session": "ny", "high_impact_now": False, "ff_event_le_min": None}},
                       "confluence": {"15": {"buy_dens": 0.0, "act_dens": 0.1, "leg_sell": 5}}}}
    cand = {"direction": "LONG", "rule": "ema_reclaim", "tf": "15", "rr": 3.0,
            "materiality": {"sl_atr": 1.0, "confluence": 4, "confluence_breakdown": {"macro": 1, "momentum": 1}}}
    r = []
    # vacuum: dead_zone + no catalyst
    dv = json.loads(json.dumps(base_d)); dv["axes"]["macro"]["news_gate"]["session"] = "dead_zone"
    r.append(("session_vacuum fire", veto_session_vacuum(cand, dv)["fired"] is True))
    r.append(("session_vacuum no-fire(ny)", veto_session_vacuum(cand, base_d)["fired"] is False))
    # bad_rr
    r.append(("bad_rr fire(rr1)", veto_bad_rr({**cand, "rr": 1.0}, base_d)["fired"] is True))
    r.append(("bad_rr no-fire(rr3)", veto_bad_rr(cand, base_d)["fired"] is False))
    # chase
    r.append(("chase fire", veto_chase({**cand, "materiality": {"sl_atr": 2.0}}, base_d)["fired"] is True))
    # stale
    ds = json.loads(json.dumps(base_d)); ds["source_health"]["mtf"]["status"] = "stale"
    r.append(("stale fire", veto_stale(cand, ds, 0)["fired"] is True))
    # counter-regime: LONG vs DOWN; EXHAUSTION_MIN=1 (permissivo=lição Cp) -> 0 sig FIRE; sweep (1 sig) isenta
    r.append(("counter fire(0 sig)", veto_counter_regime(cand, base_d)["fired"] is True))
    r.append(("counter no-fire(sweep=1sig)", veto_counter_regime({**cand, "rule": "sweep_reclaim"}, base_d)["fired"] is False))
    allok = all(ok for _, ok in r)
    for name, ok in r: print(f"  {'OK' if ok else 'FALHA'} {name}")
    print("SELFTEST:", "PASS" if allok else "FALHA")
    return 0 if allok else 1


# ---------- daemon (Sub-fase A, 0 tokens) ----------
def paused(): return PAUSE_LOCAL.exists() or PAUSE_GLOBAL.exists()


def main_loop():
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            print(f"FATAL: já corre (pid {old})"); sys.exit(1)
        except (ProcessLookupError, ValueError): pass
    PIDFILE.write_text(str(os.getpid()))
    try: offset = json.loads(OFFSET_F.read_text()).get("offset", 0)
    except Exception: offset = 0
    print(f"[e2_quality] ativo | Sub-fase A (vetos determinísticos, 0 tokens) | shadow", flush=True)
    try:
        while True:
            if paused(): time.sleep(FLOOR_S); continue
            try:
                if CAND_F.exists():
                    sz = CAND_F.stat().st_size
                    if sz < offset: offset = 0
                    if sz > offset:
                        with open(CAND_F) as f:
                            f.seek(offset); new = f.read(); offset = f.tell()
                        dsr = load_dossier()
                        for line in new.splitlines():
                            try: c = json.loads(line)
                            except Exception: continue
                            if not is_material(c) or not dsr: continue
                            v = make_verdict(c, dsr, drift_cycles(c, dsr)); append(VERD_F, v)
                            if v["grade"] != "discard":
                                print(f"{now_iso()} [{v['grade']}] {v['direction']}/{v['rule']}/{v['tf']}", flush=True)
                        tmp = OFFSET_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps({"offset": offset})); os.replace(tmp, OFFSET_F)
            except Exception as e:
                print(f"{now_iso()} [erro] {type(e).__name__}:{str(e)[:80]}", flush=True)
            time.sleep(FLOOR_S)
    finally:
        PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--selftest" in sys.argv: sys.exit(cli_selftest())
    elif "--anchors" in sys.argv: sys.exit(cli_anchors())
    elif "--survey" in sys.argv: cli_survey("--replay" in sys.argv)
    elif "--once" in sys.argv: cli_once()
    else: main_loop()
