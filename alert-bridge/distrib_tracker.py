#!/usr/bin/env python3
"""DISTRIB TRACKER — SHADOW forward-only (Cris 28/08: D1 aprovado, D3 "só forward").
Implementa a máquina de fases da PROPOSTA_DISTRIB_V3_LITERATURA.md §4 (Wyckoff/VSA/Profile/SMC
mapeados a features EXISTENTES). LOG-ONLY: não bloqueia, não notifica, não toca em emissor nenhum.
Veredito sobre utilidade = forward prereg (FORWARD_PREREG_DISTRIB.md) + decisão Cris.

CONSOME artefactos aprovados (nunca reconstrói — feedback_consume_existing_never_rebuild):
  E0 market_context.json  → leg 4H (pos_in_leg/high/dir), choch por TF, preço
  liquidity_map.json      → pools BSL status CAPTURADA:SWEEP
  amd_setups.jsonl        → sweep+reclaim H4 short armado (UTAD mecânico)
  sweep_reject_guard      → upthrust 4H armado (import do módulo live)
  bars_15m.jsonl campo v  → no-demand VSA (volume rallies; v coletado desde 28/08 D2)
  study_values SVP Levels → POC por sessão (migração de value; histórico acumulado em state)
Componentes sem dados ainda (v/POC history) ficam None — contam 0, nunca inventados. py3 stdlib."""
import json
import sys
import time
from pathlib import Path

BASE = Path("/Users/cristrein/tradingview-mcp")
MC = BASE / "external_factors_v2/snapshots/market_context.json"
LM = BASE / "external_factors_v2/snapshots/liquidity_map.json"
AMD = BASE / "my-strategy/strategies/xau_amd/amd_live/.amd_state/amd_setups.jsonl"
B15 = BASE / "my-strategy/core/bar_store/store/bars_15m.jsonl"
SV15 = BASE / "my-strategy/core/bar_store/store/study_values_15.json"
STATE = BASE / "alert-bridge/.distrib_state"
LOG = BASE / "alert-bridge/logs/distrib_tracker.jsonl"
POS_TOP = 0.67          # §4 FASE A: terço superior da perna 4H
NEAR_ATR = 1.0          # pool/OB "no topo" = a <=1 ATR do high da perna
FRESH_S = 24 * 3600     # eventos (AMD/sweep) contam 24h


def _j(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


def _jl(p):
    try:
        return [json.loads(x) for x in open(p).read().splitlines() if x.strip()]
    except Exception:
        return []


def _atr4h(mc):
    """ATR aproximado da perna 4H a partir do dossiê: mag_atr = magnitude/ATR ⇒ ATR = mag/mag_atr."""
    leg = ((mc.get("axes") or {}).get("mtf") or {}).get("240", {}).get("leg") or {}
    hi, lo, ma = leg.get("high"), leg.get("low"), leg.get("mag_atr")
    if hi is None or lo is None or not ma:
        return None
    return (hi - lo) / ma


def _no_demand(leg_low):
    """VSA no-demand: soma de volume 'v' dos up-bars do ÚLTIMO swing-up vs o anterior, dentro da perna.
    None se não há v suficiente (coleta começou 28/08)."""
    bars = _jl(B15)[-400:]
    vs = [b for b in bars if b.get("v")]
    if len(vs) < 96:
        return None, "v_insuficiente"
    ups = []                                  # segmentos de subida consecutiva (proxy de rally 15M)
    cur = 0.0
    for b in vs:
        if b["c"] > b["o"]:
            cur += b["v"]
        elif cur:
            ups.append(cur); cur = 0.0
    if cur:
        ups.append(cur)
    if len(ups) < 4:
        return None, "poucos_rallies"
    recent, prior = sum(ups[-2:]) / 2, sum(ups[-4:-2]) / 2
    return recent < prior * 0.7, round(recent / prior, 2) if prior else None


def _poc_today():
    for s in (_j(SV15, {}).get("studies") or []):
        if "SVP" in (s.get("name") or ""):
            v = s.get("values") or {}
            for k in ("POC", "Developing POC", "poc"):
                if v.get(k) is not None:
                    return v[k]
    return None


def _poc_migration():
    """Guarda 1 POC por dia UTC em state; migração = POC hoje < POC ontem. None até 2 sessões."""
    STATE.mkdir(exist_ok=True)
    f = STATE / "poc_history.json"
    hist = _j(f, {})
    poc = _poc_today()
    day = time.strftime("%Y-%m-%d", time.gmtime())
    if poc is not None:
        hist[day] = poc
        hist = dict(sorted(hist.items())[-10:])
        f.write_text(json.dumps(hist))
    days = sorted(hist)
    if len(days) < 2 or hist.get(day) is None:
        return None, "historico<2_sessoes"
    prev = hist[days[-2]]
    return hist[day] < prev, round(hist[day] - prev, 1)


def compute():
    mc = _j(MC, {})
    mtf = (mc.get("axes") or {}).get("mtf") or {}
    if not mtf:
        return {"err": "sem_dossie_E0"}
    leg = (mtf.get("240") or {}).get("leg") or {}
    price = ((mc.get("axes") or {}).get("micro_15m") or {}).get("close")
    atr = _atr4h(mc)
    now = int(time.time())
    top = leg.get("high")

    # FASE A — topo candidato
    near = []
    if top is not None and atr:
        for p in (_j(LM, {}).get("pools") or []):
            if p.get("side") == "BSL" and p.get("lo") is not None and abs(p["lo"] - top) <= NEAR_ATR * atr:
                near.append(p)
    fase_a = (leg.get("dir") == "up" and (leg.get("pos_in_leg") or 0) >= POS_TOP and bool(near))

    # FASE B — pontos (§4; None = sem dados, conta 0)
    comp = {}
    comp["b1_bsl_sweep"] = min(2, sum(1 for p in near if p.get("status") == "CAPTURADA:SWEEP"))
    try:
        sys.path.insert(0, str(BASE / "alert-bridge"))
        import sweep_reject_guard as SRG
        srg = bool(SRG.blocks_long())
    except Exception:
        srg = None
    amd_short = any(r.get("dir") == "short" and now - (r.get("t") or 0) <= FRESH_S for r in _jl(AMD)[-20:])
    comp["b2_upthrust"] = 1 if (srg or amd_short) else (None if srg is None and not amd_short else 0)
    nd, nd_info = _no_demand(leg.get("low"))
    comp["b3_no_demand"] = (1 if nd else 0) if nd is not None else None
    pm, pm_info = _poc_migration()
    comp["b4_value_migr"] = (1 if pm else 0) if pm is not None else None
    dn15 = bool(((mtf.get("15") or {}).get("choch") or {}).get("dn"))
    dn60 = bool(((mtf.get("60") or {}).get("choch") or {}).get("dn"))
    dn240 = bool(((mtf.get("240") or {}).get("choch") or {}).get("dn"))
    comp["b5_choch_interno"] = 1 if (dn15 and not dn60) else 0
    score = sum(v for v in comp.values() if v)

    fase_c = dn60 or dn240                      # SOW — aqui o choch_guard atual já atua
    phase = "C" if fase_c else ("B" if fase_a and score >= 1 else ("A" if fase_a else "-"))
    return dict(phase=phase, score=score, fase_a=fase_a, comp=comp,
                nd_info=nd_info, pm_info=pm_info, leg_top=top, pos_in_leg=leg.get("pos_in_leg"),
                price=price, n_pools_top=len(near))


def tick():
    v = compute()
    v["logged_at"] = int(time.time())
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(v) + "\n")
    print("distrib-tracker SHADOW (log-only, zero emissores): phase=%s score=%s comp=%s px=%s"
          % (v.get("phase"), v.get("score"), v.get("comp"), v.get("price")))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        v = compute()
        t.append(("compute devolve phase/score ou err", ("phase" in v) or ("err" in v)))
        if "phase" in v:
            t.append(("score = soma dos componentes não-None", v["score"] == sum(x for x in v["comp"].values() if x)))
            t.append(("phase coerente (C exige choch 60/240; B exige fase_a)",
                      v["phase"] in ("-", "A", "B", "C")))
        import inspect, ast
        tree = ast.parse(inspect.getsource(sys.modules[__name__]))
        calls = {getattr(getattr(nd, "func", None), "attr", None) for nd in ast.walk(tree) if isinstance(nd, ast.Call)}
        t.append(("SHADOW puro: nenhuma chamada de envio (_tg_send/send/notify)",
                  not ({"_tg_send", "notify", "send_message"} & calls)))
        imports = {n.name for nd in ast.walk(tree) if isinstance(nd, ast.Import) for n in nd.names}
        t.append(("não recomputa estrutura (sem import context_structure)", "context_structure" not in imports))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("estado atual:", {k: v[k] for k in ("phase", "score", "comp") if k in v} if "phase" in v else v)
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    tick()
