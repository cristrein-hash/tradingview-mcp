#!/usr/bin/env python3
"""HTF LOCATION GATE p/ o reclaim engine (long) — Cris 2026-08-17 (APROVADO).
Fix da cegueira de localização: o reclaim_engine dispara em estrutura de preço PURA (T/O/H/L/C, sem olhar OB),
enviando os reclaims altos-no-ar (4400/4412) com o mesmo peso do genuíno no fundo de uma demanda HTF. Este gate
consome o dossier E0 canónico (axes.mtf[tf].zones.stack, as-of; CONSUMIR não reconstruir, nunca inventar zona) e:
  (1) LOCALIZAÇÃO — a entrada tem de cair dentro/no bordo de um cluster de demanda HTF (60/240/1D; 15M = fraca).
  (2) POSIÇÃO     — terço inferior do cluster (não o topo, onde o chop mata).
  (3) SL          — alargado abaixo do cluster inteiro −0.1ATR (nunca mais apertado que o SL do engine).
ENFORCING = (1)+(2) — a parte PROVADA em níveis-fixos (corta alto-no-ar + topo-de-zona). SHADOW = (3), medida no
ledger (sl_wide/tgt_wide lado a lado) até forward decidir. Fail-open em dossier stale (não suprime com dados velhos).
NÃO é edge provado — forward=árbitro. Espelhado no short (E2) com supply/topo/perna-1H-DOWN. py3 stdlib.

Fonte da forma das zonas (medida no E0): axes.mtf[tf].zones = {n, above{high,low,src}, below{high,low,src},
stack{above:[...], below:[...]}}. 'below' = demanda mais próxima; stack.below = todas as demandas abaixo."""
from pathlib import Path
import json, time

DOSSIER = Path("/Users/cristrein/tradingview-mcp/external_factors_v2/snapshots/market_context.json")
TFS_STRONG = ("60", "240", "1D")   # 15M sozinha = fraca (não conta como cluster)
POS_MAX = 0.40                     # entrada no terço inferior do cluster (0=fundo, 1=topo)
EDGE_TOL_ATR = 0.15                # "no bordo" = até 0.15 ATR acima do topo da demanda ainda conta como dentro
STALE_S = 3600                     # dossier > 1h = stale -> fail-open (não enforça)
TARGET_R = 3.0


def load_dossier(path=DOSSIER):
    """Devolve (dossier, stale_bool). Fail-open: dossier ausente/velho -> None/True (não enforça)."""
    try:
        d = json.loads(Path(path).read_text())
    except Exception:
        return None, True
    try:
        age = time.time() - Path(path).stat().st_mtime
    except Exception:
        age = 0
    return d, (age > STALE_S)


def _demand_zones(dossier):
    """Todas as demandas HTF (60/240/1D) do dossier E0, sem inventar: zones.below + zones.stack.below."""
    zs = []
    mtf = (dossier.get("axes") or {}).get("mtf") or {}
    for tf in TFS_STRONG:
        z = (mtf.get(tf) or {}).get("zones") or {}
        b = z.get("below")
        if isinstance(b, dict) and b.get("high") and b.get("low"):
            zs.append((b["low"], b["high"]))
        for zz in ((z.get("stack") or {}).get("below") or []):
            if zz.get("high") and zz.get("low"):
                zs.append((zz["low"], zz["high"]))
    return zs


def _merge(zs):
    """Funde faixas sobrepostas/adjacentes -> lista (low, high) ordenada."""
    zs = sorted(zs)
    out = []
    for lo, hi in zs:
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def demand_cluster(dossier, entry, atr):
    """Cluster de demanda HTF que contém/abarca a entrada (dentro, ou até EDGE_TOL_ATR acima do topo)."""
    merged = _merge(_demand_zones(dossier))
    tol = EDGE_TOL_ATR * max(atr, 1e-9)
    for lo, hi in merged:
        if lo - tol <= entry <= hi + tol:
            return {"low": round(lo, 2), "high": round(hi, 2)}
    return None


def gate(fire, dossier):
    """Gate de um fire do reclaim engine. fire = {entry, sl, atr, ...}. dossier = E0 as-of.
    Devolve dict com pass/reason/cluster/pos/sl_wide/tgt_wide. ENFORCING usa 'pass'; SHADOW usa sl_wide."""
    entry = fire["entry"]; atr = fire.get("atr") or 1.0; sl0 = fire.get("sl")
    cl = demand_cluster(dossier, entry, atr)
    if not cl:
        return {"pass": False, "reason": "alto-no-ar (fora de cluster de demanda HTF)", "cluster": None}
    span = max(cl["high"] - cl["low"], 1e-9)
    pos = (entry - cl["low"]) / span
    if pos > POS_MAX:
        return {"pass": False, "reason": "topo-de-zona (pos %.2f > %.2f)" % (pos, POS_MAX),
                "cluster": cl, "pos": round(pos, 2)}
    # SHADOW: SL abaixo do cluster inteiro -0.1ATR, mas NUNCA mais apertado que o SL do engine
    sl_wide = round(min(sl0, cl["low"] - 0.1 * atr), 2) if sl0 is not None else round(cl["low"] - 0.1 * atr, 2)
    tgt_wide = round(entry + TARGET_R * (entry - sl_wide), 2)
    return {"pass": True, "reason": "fundo-de-cluster (pos %.2f)" % pos, "cluster": cl,
            "pos": round(pos, 2), "sl_wide": sl_wide, "tgt_wide": tgt_wide}


DEMAND_NEAR_ATR = 2.0     # demanda HTF a <=2 ATR abaixo da entrada = "sobre demanda fresca" -> não shortar


def _nearest_demand_below(dossier, entry):
    """A demanda HTF mais alta inteiramente abaixo da entrada (o 'fundo de outra pessoa')."""
    below = [(lo, hi) for lo, hi in _merge(_demand_zones(dossier)) if hi <= entry]
    if not below:
        return None
    lo, hi = max(below, key=lambda x: x[1])
    return {"low": round(lo, 2), "high": round(hi, 2)}


def gate_short(cand, dossier):
    """Espelho SHORT do location gate (Cris 2026-08-17). Suprime shorts como o 08:02 (@4405, perna 1H UP).
    PASSA só se: perna imediata 1H DOWN E a entrada NÃO está sobre uma demanda HTF fresca por baixo
    (<=DEMAND_NEAR_ATR ATR). Senão -> suprime (topo de perna que sobe / fundo de outra pessoa = não é reversão
    de alta-prob). Consome axes.mtf[60].leg + zones (E0 as-of). Fail-open sem dossier. Razão perna-1H é
    as-of-válida (não depende de OB as-of-agora). Enforcing só na parte medida; forward=árbitro."""
    if dossier is None:
        return {"pass": True, "reason": "fail-open: sem dossier"}
    try:
        entry = float(cand.get("entry"))
    except (TypeError, ValueError):
        return {"pass": True, "reason": "fail-open: entry inválido"}
    mtf = (dossier.get("axes") or {}).get("mtf") or {}
    leg60 = (mtf.get("60") or {}).get("leg") or {}
    legdir = leg60.get("dir")
    atr = ((leg60["high"] - leg60["low"]) / leg60["mag_atr"]) if (
        leg60.get("mag_atr") and leg60.get("high") and leg60.get("low")) else 5.0
    if legdir == "up":
        return {"pass": False, "reason": "perna 1H UP (não shortar perna que sobe)", "leg1h": legdir}
    dem = _nearest_demand_below(dossier, entry)
    if dem and (entry - dem["high"]) <= DEMAND_NEAR_ATR * atr:
        return {"pass": False, "leg1h": legdir, "demand": dem,
                "reason": "sobre demanda HTF fresca %.2f-%.2f (<=%.1fATR)" % (dem["low"], dem["high"], DEMAND_NEAR_ATR)}
    return {"pass": True, "leg1h": legdir, "reason": "perna 1H down, sem demanda fresca por baixo"}


if __name__ == "__main__":
    import sys
    if "--selftest-short" in sys.argv:
        # espelho short: prova que suprime o caso 08:02 (perna 1H UP) e passa perna-down-sem-demanda
        up = {"axes": {"mtf": {"60": {"leg": {"low": 4386.88, "high": 4411.42, "mag_atr": 1.56, "dir": "up"},
              "zones": {"stack": {"below": [{"low": 4377.24, "high": 4394.42}]}}}}}}
        dn = {"axes": {"mtf": {"60": {"leg": {"low": 4300, "high": 4360, "mag_atr": 4.0, "dir": "down"},
              "zones": {"stack": {"below": [{"low": 4200, "high": 4210}]}}}}}}
        g1 = gate_short({"entry": 4405.42}, up)    # o 08:02 real
        g2 = gate_short({"entry": 4360.0}, dn)     # perna down, demanda longe
        print("08:02 @4405 (perna 1H up):", g1["pass"], "-", g1["reason"])
        print("perna-down sem-demanda:  ", g2["pass"], "-", g2["reason"])
        ok = (g1["pass"] is False) and (g2["pass"] is True)
        print("selftest-short", "PASS" if ok else "FAIL", "| razão do 08:02 é as-of-válida (perna 1H, não OB-as-of-agora)")
        sys.exit(0 if ok else 1)
    if "--selftest" in sys.argv:
        d, stale = load_dossier()
        assert d is not None, "dossier E0 ausente"
        LED = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_15m_long/"
                   "ENTRY_ROUTER/.router_state/reclaim_ledger.jsonl")
        fires = [json.loads(l) for l in LED.read_text().splitlines() if l.strip()]
        # atr por-fire: o ledger não guarda atr no fire histórico; usa (entry-sl)/algo? -> reconstrói grosseiro
        for f in fires:
            f.setdefault("atr", abs(f.get("entry", 0) - f.get("sl", 0)) / 0.5 or 5.0)
        res = [(f, gate(f, d)) for f in fires]
        res2 = [(f, gate(f, d)) for f in fires]
        print("CAVEAT: usa o dossier E0 ATUAL como aproximação do as-of de cada fire (o gate LIVE usa o dossier")
        print("fresco de cada ciclo = as-of correto p/ fire fresco). Cluster HTF do E0 agora:", _merge(_demand_zones(d))[:4])
        print("%-12s %-8s %-6s %-6s %-8s %-28s %s" % ("etime", "entry", "out", "GATE", "pos", "reason", "sl_wide"))
        sent = kept_loss = cut_loss = 0
        for f, g in res:
            out = f.get("outcome"); p = g["pass"]
            if p and out == "LOSS": kept_loss += 1
            if (not p) and out == "LOSS": cut_loss += 1
            if p: sent += 1
            print("%-12s %-8s %-6s %-6s %-6s %-28s %s" % (
                f.get("etime"), f.get("entry"), out, "SEND" if p else "SKIP",
                g.get("pos", "-"), g["reason"][:28], g.get("sl_wide", "-")))
        # afirmações honestas
        highair = {4395.78, 4400.91, 4395.91, 4396.78, 4398.29, 4412.36}
        t = []
        t.append(("determinístico", [x[1]["pass"] for x in res] == [x[1]["pass"] for x in res2]))
        t.append(("corta os altos-no-ar (>topo demanda)",
                  all(not g["pass"] for f, g in res if round(f.get("entry", 0), 2) in highair)))
        t.append(("passa >=1 fundo-de-cluster", any(g["pass"] for f, g in res)))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("ENFORCING hoje: enviaria %d/%d fires (cortou %d LOSS altos/topo; manteve %d LOSS de fundo)."
              % (sent, len(fires), cut_loss, kept_loss))
        print("NÃO afirma efeito do SL-alargado (é SHADOW, forward mede). stale=%s" % stale)
        sys.exit(0 if all(r for _, r in t) else 1)
