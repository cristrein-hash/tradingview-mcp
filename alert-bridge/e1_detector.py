#!/usr/bin/env python3
"""E1 — CANDIDATE DETECTOR (Camada 2, P4). Determinístico, 0 tokens, SHADOW (NÃO emite Telegram).
Lê o dossiê market_context.json (mtime-watch), aplica 6 gatilhos estruturais (ecoam os engines aprovados)
e pontua CADA candidato por MULTI-CONFLUÊNCIA (estrutura MTF · zonas · act_dens/auction · momentum ·
SVP-HTF · macro). Anti-spam (materialidade+cooldown+dedup). Loga tudo em logs/e1_candidates.jsonl para o
E2 (P5) consumir. Permissivo (recall alto — a precisão é do E2). py3.9.
CLI: --once (1 ciclo sobre o dossiê vivo) · --selftest (regras sobre dossiês sintéticos) · (default) daemon.
"""
import os, sys, json, time, hashlib, datetime as dt
from pathlib import Path
BASE = Path(__file__).resolve().parent
REPO = BASE.parent
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
DOSSIER = REPO / "external_factors_v2" / "snapshots" / "market_context.json"
CAND_F = LOGS / "e1_candidates.jsonl"
STATE_F = LOGS / "e1_state.json"
PIDFILE = LOGS / "e1_detector.pid"
PAUSE_LOCAL = LOGS / "monitor.pause"
PAUSE_GLOBAL = Path("/tmp/claude_recheck.paused")
FLOOR_S = 30
# limiares. PRINCÍPIO (dos engines/definição) vs FIT (a calibrar no shadow, NÃO fixar a olhar 1 dia).
MIN_RR = 1.5                 # a calibrar (shadow) — não fixar a hoje
MIN_SL_ATR = 0.3; MAX_SL_ATR = 3.0
MIN_CONFLUENCE = 2           # REVERTIDO 3->2 (era FIT a hoje). E1 permissivo=recall; shadow calibra.
MAX_R_ATR15 = 2.0            # PRINCÍPIO: SL local ~1-2×ATR (escala A1/Cp); cap de SL largo
MAX_TARGET_R = 5.0           # PRINCÍPIO: alvo canónico 3R; cap generoso anti-fantasia
COOLDOWN_BARS = 4; DEDUP_BARS = 12; BAR_S = 900   # anti-spam ops — a calibrar no shadow (não a hoje)
STRUCT_TFS = ("240", "60", "15")


def now_iso(): return dt.datetime.now(dt.timezone.utc).isoformat()
def fnum(x):
    try: return float(str(x).replace("−", "-").replace("K", "e3").replace(" ", ""))
    except Exception: return None


def atr_of(leg):
    if not leg or not leg.get("mag_atr"): return None
    try: return (leg["high"] - leg["low"]) / leg["mag_atr"]
    except Exception: return None


# ---------- multi-confluência ----------
def confluence_score(d, direction, tf):
    """Pontua um candidato de direção D por eixo. Devolve (score, breakdown)."""
    mtf = d["axes"].get("mtf", {}); micro = d["axes"].get("micro_15m", {}) or {}
    conf = (d["axes"].get("confluence") or {}).get("15", {}) or {}
    macro = d["axes"].get("macro", {}) or {}
    want = "DOWN" if direction == "SHORT" else "UP"
    b = {}
    # 1. estrutura MTF: HTF concordam com a direção
    htf = [mtf.get(t, {}).get("trend") for t in ("60", "240", "1D")]
    b["mtf_align"] = sum(1 for x in htf if x == want)
    # 2. zona real no TF do gatilho
    z = mtf.get(tf, {}).get("zones") or {}
    b["zone"] = 1 if ((direction == "SHORT" and z.get("above")) or (direction == "LONG" and z.get("below"))) else 0
    # 3. auction / act_dens
    if direction == "LONG":
        b["auction"] = 1 if fnum(conf.get("buy_dens")) and fnum(conf.get("buy_dens")) >= 0.25 else 0
    else:
        sd = (conf.get("sell") or {}).get("dens")
        b["auction"] = 1 if (fnum(sd) and fnum(sd) >= 0.25) or (fnum(conf.get("leg_sell")) and fnum(conf.get("leg_sell")) >= 60) else 0
    # 4. momentum: RSI + DMI a favor
    rsi, rsi_ma = fnum(micro.get("rsi")), fnum(micro.get("rsi_ma"))
    dmi = micro.get("dmi", {}) or {}; pdi, mdi = fnum(dmi.get("plus_di")), fnum(dmi.get("minus_di"))
    mom = 0
    if rsi and rsi_ma:
        mom += 1 if (direction == "LONG" and rsi > rsi_ma) or (direction == "SHORT" and rsi < rsi_ma) else 0
    if pdi and mdi:
        mom += 1 if (direction == "LONG" and pdi > mdi) or (direction == "SHORT" and mdi > pdi) else 0
    b["momentum"] = mom
    # 5. SVP-HTF pressão a favor
    press = [mtf.get(t, {}).get("svp", {}).get("pressure") for t in ("60", "240")]
    want_p = "sell" if direction == "SHORT" else "buy"
    b["svp_htf"] = sum(1 for p in press if p == want_p)
    # 6. macro não-contra (catalisador/sessão)
    ng = macro.get("news_gate", {}) or {}
    b["macro"] = 1 if (ng.get("high_impact_now") or ng.get("session") in ("london_strong", "ny_open", "ny")) else 0
    return sum(b.values()), b


# ---------- níveis ----------
def levels(direction, close, sl_ref, atr, tf_zones, pos=None):
    # fix#1: sl_ref = swing LOCAL do 15M (passado por detect), atr = ATR15 — SL tight executável, nunca o
    # swing do TF do gatilho (que dava 50pts). fix#4: alvo cap a MAX_TARGET_R.
    # fix#5 (anti-atraso): só entra em posição FRESCA da perna — SHORT no topo (pos>=0.5), LONG no fundo.
    if pos is not None:
        if direction == "SHORT" and pos < 0.5: return None
        if direction == "LONG" and pos > 0.5: return None
    if atr is None or sl_ref is None: return None
    sl = sl_ref - 0.1 * atr if direction == "LONG" else sl_ref + 0.1 * atr
    r = abs(close - sl)
    if r <= 0 or r > MAX_R_ATR15 * atr: return None            # SL demasiado largo p/ 15M-local = setup fraco
    if direction == "LONG":
        z = (tf_zones or {}).get("above") or {}
        raw = z.get("low") if z.get("low") and z["low"] > close else close + 3 * r
        tgt = min(raw, close + MAX_TARGET_R * r)
    else:
        z = (tf_zones or {}).get("below") or {}
        raw = z.get("high") if z.get("high") and z["high"] < close else close - 3 * r
        tgt = max(raw, close - MAX_TARGET_R * r)
    rr = abs(tgt - close) / r
    if rr < 1.0: return None                                    # alvo mais perto que o SL = descarta
    return {"entry": round(close, 2), "sl": round(sl, 2), "target": round(tgt, 2), "rr": round(rr, 2), "r": round(r, 3)}


# ---------- 6 gatilhos (d=atual, p=anterior) ----------
def _sw(mtf, tf, k): return (mtf.get(tf, {}).get("swings") or {}).get(k) or {}


def detect(d, p):
    """Devolve lista de candidatos crus (pré anti-spam)."""
    out = []
    mtf = d["axes"].get("mtf", {}); micro = d["axes"].get("micro_15m", {}) or {}
    close = fnum(micro.get("close"))
    pmtf = (p or {}).get("axes", {}).get("mtf", {}) if p else {}
    pmicro = (p or {}).get("axes", {}).get("micro_15m", {}) if p else {}
    if close is None: return out

    # fix#1: SL SEMPRE ancorado ao swing LOCAL do 15M (+ATR15), qualquer que seja o TF do gatilho.
    m15 = mtf.get("15", {}); leg15 = m15.get("leg") or {}; atr15 = atr_of(leg15)
    sl15_low = _sw(mtf, "15", "last_low").get("price")
    sl15_high = _sw(mtf, "15", "last_high").get("price")
    pclose = fnum((pmicro or {}).get("close")) if pmicro else None

    for tf in STRUCT_TFS:
        m = mtf.get(tf, {}); zones = m.get("zones")
        pos_tf = (m.get("leg") or {}).get("pos_in_leg")   # pos-freshness do TF do gatilho (princípio A1/Cp)
        pm = pmtf.get(tf, {})
        ll, lh = _sw(mtf, tf, "last_low"), _sw(mtf, tf, "last_high")
        pl, ph = _sw(mtf, tf, "prev_low"), _sw(mtf, tf, "prev_high")

        # R3 CHoCH (transição false->true) — SL 15M-local, entrada fresca (pos)
        if m.get("choch", {}).get("dn") and not (pm.get("choch", {}) or {}).get("dn"):
            lv = levels("SHORT", close, sl15_high, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="choch", tf=tf, direction="SHORT", src="mtf.choch.dn/SL15m", **lv))
        if m.get("choch", {}).get("up") and not (pm.get("choch", {}) or {}).get("up"):
            lv = levels("LONG", close, sl15_low, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="choch", tf=tf, direction="LONG", src="mtf.choch.up/SL15m", **lv))

        # R1 sweep+reclaim (gatilho no TF; SL 15M-local; entrada fresca)
        if ll.get("price") and pl.get("price") and ll["price"] < pl["price"] and close > pl["price"]:
            lv = levels("LONG", close, sl15_low, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="sweep_reclaim", tf=tf, direction="LONG", src="swept prev_low+reclaim/SL15m", **lv))
        if lh.get("price") and ph.get("price") and lh["price"] > ph["price"] and close < ph["price"]:
            lv = levels("SHORT", close, sl15_high, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="sweep_reclaim", tf=tf, direction="SHORT", src="swept prev_high+reclaim/SL15m", **lv))

        # R4 zone reject — SL 15M-local, entrada fresca
        za, zb = (zones or {}).get("above") or {}, (zones or {}).get("below") or {}
        if pclose and za.get("low") and pclose >= za["low"] and close < za["low"]:
            lv = levels("SHORT", close, sl15_high, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="zone_reject", tf=tf, direction="SHORT", src="reject supply/SL15m", **lv))
        if pclose and zb.get("high") and pclose <= zb["high"] and close > zb["high"]:
            lv = levels("LONG", close, sl15_low, atr15, zones, pos_tf)
            if lv: out.append(dict(rule="zone_reject", tf=tf, direction="LONG", src="reject demand/SL15m", **lv))

    # R5 ema reclaim (15M): fundo/topo de perna + cruza EMA21 — SL 15M-local
    ema21 = fnum(micro.get("ema", {}).get("ema21")); pema21 = fnum((pmicro or {}).get("ema", {}).get("ema21"))
    pos = leg15.get("pos_in_leg")
    if ema21 and pema21 and pclose is not None and pos is not None:
        if pos <= 0.25 and pclose <= pema21 and close > ema21:
            lv = levels("LONG", close, sl15_low, atr15, m15.get("zones"))
            if lv: out.append(dict(rule="ema_reclaim", tf="15", direction="LONG", src="leg-bottom+ema21/SL15m", **lv))
        if pos >= 0.75 and pclose >= pema21 and close < ema21:
            lv = levels("SHORT", close, sl15_high, atr15, m15.get("zones"))
            if lv: out.append(dict(rule="ema_reclaim", tf="15", direction="SHORT", src="leg-top+ema21/SL15m", **lv))

    # R6 macro event (high_impact + reação preço > 1 ATR) — SL 15M-local
    ng = (d["axes"].get("macro", {}) or {}).get("news_gate", {}) or {}
    if ng.get("high_impact_now") and pclose is not None and atr15:
        move = close - pclose
        if abs(move) >= 1.0 * atr15:
            dirn = "LONG" if move > 0 else "SHORT"
            ref = sl15_low if dirn == "LONG" else sl15_high
            lv = levels(dirn, close, ref, atr15, m15.get("zones"))
            if lv: out.append(dict(rule="macro_event", tf="15", direction=dirn, src="news high_impact/SL15m", **lv))
    return out


# ---------- materialidade + anti-spam ----------
def materiality(cand, d, atr):
    m = {"min_rr_ok": cand["rr"] >= MIN_RR,
         "sl_atr": round(cand["r"] / atr, 2) if atr else None,
         "zone_touch": "zone" in cand.get("src", "") or "reject" in cand.get("src", "")}
    sl_ok = atr and MIN_SL_ATR <= (cand["r"] / atr) <= MAX_SL_ATR
    score, brk = confluence_score(d, cand["direction"], cand["tf"])
    m["confluence"] = score; m["confluence_breakdown"] = brk
    m["pass"] = bool(m["min_rr_ok"] and sl_ok and score >= MIN_CONFLUENCE)
    return m


def cand_hash(c):
    return hashlib.md5(f"{c['rule']}{c['tf']}{c['direction']}{round(c['entry'])}{round(c['sl'])}".encode()).hexdigest()[:12]


from config_stack import DEAD_SESSIONS as DEAD_SESSIONS_E2   # fonte única (config_stack, Fase 4)


def _verdict_veto_of(cand_id):
    """Veto do gate E2 para um candidato emitido (lê a cauda de e2_verdicts). None se não encontrado."""
    try:
        lines = (LOGS / "e2_verdicts.jsonl").read_text().splitlines()[-300:]
        for l in reversed(lines):
            r = json.loads(l)
            if r.get("candidate_id") == cand_id:
                return r.get("veto")
    except Exception:
        pass
    return None


def anti_spam(cand, state, bar_time, sess=None):
    h = cand_hash(cand); key = f"{cand['rule']}:{cand['tf']}:{cand['direction']}"
    last_cd = state.get("cooldown", {}).get(key)
    if last_cd and bar_time and (bar_time - last_cd) < COOLDOWN_BARS * BAR_S:
        return "cooldown"
    last_dd = state.get("dedup", {}).get(h)
    dd_t = last_dd.get("t") if isinstance(last_dd, dict) else last_dd   # compat estado antigo (int)
    if dd_t and bar_time and (bar_time - dd_t) < DEDUP_BARS * BAR_S:
        # dedup CONSCIENTE DO DESTINO (Cris 2026-07-17): se o original foi gate-vetoado por
        # session_vacuum e a sessão ATUAL já não é morta, o re-trigger merece re-avaliação.
        if (isinstance(last_dd, dict) and sess and sess not in DEAD_SESSIONS_E2
                and _verdict_veto_of(last_dd.get("id")) == "session_vacuum"):
            return None
        return "dedup"
    return None


# ---------- ciclo ----------
def load_state():
    try: return json.loads(STATE_F.read_text())
    except Exception: return {"cooldown": {}, "dedup": {}, "prev_dossier": None, "last_bar_t": None}


def save_state(s):
    tmp = STATE_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(s)); os.replace(tmp, STATE_F)


def run_once(state):
    try: d = json.loads(DOSSIER.read_text())
    except Exception as e: return [], f"dossie ilegivel: {type(e).__name__}"
    sh = d.get("source_health", {})
    if sh.get("mtf", {}).get("status") == "absent" or sh.get("micro_15m", {}).get("status") == "absent":
        return [], "eixo critico absent"
    bar_t = (d["axes"].get("micro_15m") or {}).get("bar_time")
    # só avalia estrutura no fecho de barra 15M (causal); macro-event pode intrabar
    p = state.get("prev_dossier")
    raw = detect(d, p)
    emitted = []
    for c in raw:
        atr = atr_of((d["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
        c["materiality"] = materiality(c, d, atr)
        sess_now = (d["axes"]["macro"].get("news_gate") or {}).get("session")
        sup = anti_spam(c, state, bar_t, sess_now)
        c["suppressed"] = sup
        c["id"] = f"e1_{d['_meta']['cycle_ts']}_{c['rule']}_{c['tf']}_{c['direction']}"
        c["ts"] = now_iso(); c["bar_time"] = bar_t
        c["dossier"] = {"price": d["_meta"]["price_ref"],
                        "mtf": {t: {"trend": d["axes"]["mtf"].get(t, {}).get("trend"),
                                    "pos": (d["axes"]["mtf"].get(t, {}).get("leg") or {}).get("pos_in_leg")} for t in ("240", "60", "15")},
                        "act_dens": (d["axes"].get("confluence") or {}).get("15", {}).get("act_dens"),
                        "macro": {"risk": d["axes"]["macro"].get("risk_level"), "session": (d["axes"]["macro"].get("news_gate") or {}).get("session")}}
        with open(CAND_F, "a") as f:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
        if sup is None and c["materiality"]["pass"]:
            state.setdefault("cooldown", {})[f"{c['rule']}:{c['tf']}:{c['direction']}"] = bar_t
            state.setdefault("dedup", {})[cand_hash(c)] = {"t": bar_t, "id": c["id"]}   # id p/ dedup destino-consciente
            emitted.append(c)
    state["prev_dossier"] = d
    state["last_bar_t"] = bar_t
    return emitted, None


def paused(): return PAUSE_LOCAL.exists() or PAUSE_GLOBAL.exists()


def main_loop():
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            print(f"FATAL: já corre (pid {old})"); sys.exit(1)
        except (ProcessLookupError, ValueError): pass
    PIDFILE.write_text(str(os.getpid()))
    state = load_state(); last_mtime = 0
    print(f"[e1_detector] ativo | dossie={DOSSIER.name} | shadow (0 Telegram)", flush=True)
    try:
        while True:
            if paused(): time.sleep(FLOOR_S); continue
            try:
                mt = DOSSIER.stat().st_mtime
                if mt != last_mtime:
                    last_mtime = mt
                    emitted, err = run_once(state); save_state(state)
                    if err: print(f"{now_iso()} [skip] {err}", flush=True)
                    elif emitted: print(f"{now_iso()} [candidatos] {len(emitted)}: " + ", ".join(f"{c['direction']}/{c['rule']}/{c['tf']}(conf{c['materiality']['confluence']})" for c in emitted), flush=True)
            except Exception as e:
                print(f"{now_iso()} [erro] {type(e).__name__}:{str(e)[:80]}", flush=True)
            time.sleep(FLOOR_S)
    finally:
        PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--once" in sys.argv:
        st = load_state()
        em, err = run_once(st); save_state(st)
        print(f"erro: {err}" if err else f"candidatos ATIVOS: {len(em)}")
        for c in em:
            print(f"  {c['direction']} {c['rule']} {c['tf']} | entry {c['entry']} SL {c['sl']} tgt {c['target']} RR {c['rr']} "
                  f"| conf {c['materiality']['confluence']} {c['materiality']['confluence_breakdown']}")
        print(f"(todos os candidatos crus — incl. suprimidos/reprovados — em {CAND_F.name})")
    elif "--selftest" in sys.argv:
        def mk(choch_dn=False, close=108.0):
            return {"_meta": {"cycle_ts": 1, "price_ref": close},
                    "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}},
                    "axes": {"mtf": {
                        "240": {"trend": "DOWN", "leg": {"low": 90, "high": 110, "mag_atr": 2.0, "pos_in_leg": 0.9, "dir": "down"},
                                "choch": {"dn": choch_dn, "up": False},
                                "swings": {"last_high": {"price": 110, "bar": 5}, "last_low": {"price": 90, "bar": 2},
                                           "prev_high": {"price": 108, "bar": 1}, "prev_low": {"price": 92, "bar": 0}},
                                "zones": {"above": {"high": 112, "low": 111}, "below": {"high": 90, "low": 88}}, "svp": {"pressure": "sell"}},
                        "60": {"trend": "DOWN", "svp": {"pressure": "sell"}}, "1D": {"trend": "DOWN"},
                        "15": {"trend": "DOWN", "leg": {"low": 90, "high": 110, "mag_atr": 2.0, "pos_in_leg": 0.9},
                               "swings": {"last_high": {"price": 110, "bar": 5}, "last_low": {"price": 100, "bar": 2}}, "zones": {}}},
                        "micro_15m": {"close": close, "bar_time": 1000, "ema": {"ema21": 111}, "rsi": "40", "rsi_ma": "45",
                                      "dmi": {"plus_di": "10", "minus_di": "25"}},
                        "macro": {"risk_level": "normal", "news_gate": {"session": "ny", "high_impact_now": False}},
                        "confluence": {"15": {"act_dens": 1.0, "buy_dens": 0.0, "sell": {"dens": 0.5}, "leg_sell": 100}}}}
        p, d = mk(False), mk(True)
        cands = detect(d, p)
        short_choch = [c for c in cands if c["rule"] == "choch" and c["direction"] == "SHORT" and c["tf"] == "240"]
        score, brk = confluence_score(d, "SHORT", "240")
        ok_trigger = len(short_choch) == 1
        ok_conf = score >= 5
        ok_pass = bool(short_choch and materiality(short_choch[0], d, atr_of(d["axes"]["mtf"]["240"]["leg"]))["pass"])
        print(f"CHoCH-dn transição -> SHORT candidato: {ok_trigger} (n={len(short_choch)})")
        print(f"confluência SHORT: score={score} breakdown={brk} (esp>=5): {ok_conf}")
        print(f"materialidade pass (RR ok + SL banda + conf>=2): {ok_pass}")
        print("RESULTADO:", "PASS" if (ok_trigger and ok_conf and ok_pass) else "FALHA")
        sys.exit(0 if (ok_trigger and ok_conf and ok_pass) else 1)
    else:
        main_loop()
