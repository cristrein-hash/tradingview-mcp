#!/usr/bin/env python3
"""HTF LOCATION GATE p/ o reclaim engine (long) + espelho short — Cris 2026-08-17 (APROVADO; reescrito após
auditoria: SEM parâmetros inventados, SEM SL-alargado). O reclaim_engine dispara em estrutura de preço PURA
(T/O/H/L/C, sem olhar OB), enviando reclaims altos-no-ar com o mesmo peso do genuíno no fundo de uma demanda HTF.
Este gate consome o dossier E0 canónico (axes.mtf[tf].zones + .leg, as-of; CONSUMIR não reconstruir, nunca
inventar zona) e decide por FACTO ESTRUTURAL BINÁRIO — sem limiares afinados:
  (1) LOCALIZAÇÃO — a entrada está DENTRO de uma zona de demanda HTF (1H/4H/1D), [low<=entry<=high]. Fora = SKIP.
  (2) POSIÇÃO     — metade INFERIOR da zona (entry < ponto-médio geométrico). Metade superior = SKIP.
Enforcing (só envia gate_pass). Fail-open se dossier ausente/velho. Espelho SHORT: perna 1H DOWN (ESTRITO) +
entrada NÃO acima de uma demanda HTF por baixo. NÃO é edge provado — forward=árbitro. py3 stdlib.

Zonas (E0): axes.mtf[tf].zones = {n, above{high,low}, below{high,low}, stack{above:[...], below:[...]}}.
Ponto-médio = (low+high)/2 = centro geométrico, NÃO um parâmetro afinável."""
from pathlib import Path
import json, time

DOSSIER = Path("/Users/cristrein/tradingview-mcp/external_factors_v2/snapshots/market_context.json")
TFS_STRONG = ("60", "240", "1D")   # localização HTF = 1H/4H/1D (o set do Cris; 15M não é HTF)
STALE_S = 3600                     # operacional (não é knob de estratégia): dossier > 1h = fail-open


def load_dossier(path=DOSSIER):
    """Devolve (dossier, stale_bool). Fail-open: ausente/velho -> None/True (não enforça)."""
    try:
        d = json.loads(Path(path).read_text())
    except Exception:
        return None, True
    try:
        age = time.time() - Path(path).stat().st_mtime
    except Exception:
        age = 0
    return d, (age > STALE_S)


POLARITY_ZONES = Path("/Users/cristrein/tradingview-mcp/alert-bridge/.polarity_state/zones.json")


def _demand_zones(dossier):
    """Todas as demandas do sistema, sem inventar: (a) OB below do E0 (1H/4H/1D); (b) zonas de POLARIDADE do
    polarity_tracker (ex_supply_demand = supply furada que virou suporte; LEI validada pelo Cris, task #54).
    Wire aprovado Cris 2026-08-18 ('LIGA') após o gate suprimir o reclaim pós-rompimento no reteste 4422-4429."""
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
    try:
        pz = json.loads(POLARITY_ZONES.read_text())
        for x in (pz if isinstance(pz, list) else pz.get("zones", [])):
            if x.get("type") == "ex_supply_demand" and x.get("low") and x.get("high"):
                zs.append((x["low"], x["high"]))
    except Exception:
        pass                                            # tracker ausente -> gate segue só com E0 (fail-open parcial)
    return zs


def _merge(zs):
    """Funde faixas sobrepostas/adjacentes -> lista (low, high) ordenada."""
    out = []
    for lo, hi in sorted(zs):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def demand_cluster(dossier, entry):
    """A zona de demanda que CONTÉM a entrada. Escolhe a zona ORIGINAL mais APERTADA (não a mancha fundida —
    o merge colava demanda 4377-94 a polaridade 4417-29 numa faixa de 60pt e a 'metade inferior' perdia o
    sentido). Binário [low<=entry<=high]; sem tolerância inventada."""
    inside = [(lo, hi) for lo, hi in _demand_zones(dossier) if lo <= entry <= hi]
    if not inside:
        return None
    lo, hi = min(inside, key=lambda z: z[1] - z[0])
    return {"low": round(lo, 2), "high": round(hi, 2)}


def gate(fire, dossier):
    """Gate binário de um fire do reclaim. fire={entry,...}. Devolve {pass,reason,cluster,pos}. Sem SL alargado."""
    entry = fire["entry"]
    cl = demand_cluster(dossier, entry)
    if not cl:
        return {"pass": False, "reason": "alto-no-ar (fora de zona de demanda HTF)", "cluster": None}
    span = max(cl["high"] - cl["low"], 1e-9)
    pos = (entry - cl["low"]) / span
    mid = (cl["low"] + cl["high"]) / 2.0          # ponto-médio geométrico (não afinável)
    if entry >= mid:
        return {"pass": False, "reason": "metade superior da zona (topo)", "cluster": cl, "pos": round(pos, 2)}
    return {"pass": True, "reason": "metade inferior da zona (fundo)", "cluster": cl, "pos": round(pos, 2)}


def _demand_fully_below(dossier, entry):
    """A demanda HTF mais alta inteiramente abaixo da entrada (o 'fundo de outra pessoa'), ou None. Binário."""
    below = [(lo, hi) for lo, hi in _merge(_demand_zones(dossier)) if hi < entry]
    if not below:
        return None
    lo, hi = max(below, key=lambda x: x[1])
    return {"low": round(lo, 2), "high": round(hi, 2)}


def gate_short(cand, dossier):
    """Espelho SHORT (Cris 2026-08-17). PASSA só se: perna imediata 1H == DOWN (ESTRITO, mais segurança) E a
    entrada NÃO está acima de uma demanda HTF por baixo (binário). Senão -> suprime. Consome axes.mtf[60].leg +
    zones. Fail-open sem dossier. Razão perna-1H = as-of-válida."""
    if dossier is None:
        return {"pass": True, "reason": "fail-open: sem dossier"}
    try:
        entry = float(cand.get("entry"))
    except (TypeError, ValueError):
        return {"pass": True, "reason": "fail-open: entry inválido"}
    mtf = (dossier.get("axes") or {}).get("mtf") or {}
    legdir = ((mtf.get("60") or {}).get("leg") or {}).get("dir")
    if legdir != "down":                          # ESTRITO: só short com perna 1H DOWN confirmada
        return {"pass": False, "leg1h": legdir,
                "reason": "perna 1H não-DOWN (%s) — não shortar topo de perna que não virou" % legdir}
    dem = _demand_fully_below(dossier, entry)
    if dem:
        return {"pass": False, "leg1h": legdir, "demand": dem,
                "reason": "acima de demanda HTF %.2f-%.2f (fundo de outra pessoa)" % (dem["low"], dem["high"])}
    return {"pass": True, "leg1h": legdir, "reason": "perna 1H down, sem demanda HTF por baixo"}


if __name__ == "__main__":
    import sys
    if "--selftest-short" in sys.argv:
        up = {"axes": {"mtf": {"60": {"leg": {"dir": "up"}, "zones": {"stack": {"below": []}}}}}}
        dn = {"axes": {"mtf": {"60": {"leg": {"dir": "down"}, "zones": {"stack": {"below": []}}}}}}
        g1 = gate_short({"entry": 4405.42}, up)          # 08:02 (perna up) -> suprime
        g2 = gate_short({"entry": 4360.0}, dn)           # perna down, sem demanda -> passa
        ok = (g1["pass"] is False) and (g2["pass"] is True)
        print("08:02 up:", g1["pass"], g1["reason"])
        print("down limpa:", g2["pass"], g2["reason"])
        print("selftest-short", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    if "--selftest" in sys.argv:
        d, stale = load_dossier()
        assert d is not None, "dossier E0 ausente"
        LED = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_15m_long/"
                   "ENTRY_ROUTER/.router_state/reclaim_ledger.jsonl")
        fires = [json.loads(l) for l in LED.read_text().splitlines() if l.strip()]
        res = [(f, gate(f, d)) for f in fires]
        det = [x[1]["pass"] for x in res] == [x[1]["pass"] for x in [(f, gate(f, d)) for f in fires]]
        sent = sum(1 for _, g in res if g["pass"])
        for f, g in res:
            print("%-11s %-8s %-5s %-5s %s" % (f.get("etime"), f.get("entry"), f.get("outcome"),
                  "SEND" if g["pass"] else "SKIP", g["reason"][:30]))
        print("[%s] determinístico | binário sem knobs | aprox as-of-now envia %d/%d (NÃO prova; forward=árbitro)"
              % ("OK" if det else "FAIL", sent, len(fires)))
        sys.exit(0 if det else 1)
