#!/usr/bin/env python3
"""OB AUTO-WATCH (Cris 2026-08-10: "sistema tem de descobrir demandas onde capitula com rapidez, não só nas
zonas declaradas"). LÊ o OB Detector v11 REAL do store (pine_boxes capturados via MCP) e devolve as demandas
OB perto do preço como zonas de vigia — no MESMO formato do trader_map, para a vela/validador as tratarem
igual às declaradas (rejeição + gate do reader + dedup, tudo de borla).

CONSOLIDAÇÃO (guard 2026-07-23, check corrido): o E0 market_context.json `axes.magnets` JÁ conhece as OB
mas só expõe `dist_atr` (distância), NÃO as fronteiras low/high das zonas. A vela precisa do NÍVEL preciso
para a régua de rejeição — logo esta capacidade é NOVA e consome a fonte canónica (store pine_boxes = OB
Detector real que o bar-store capta via MCP). Não reconstrói contexto/regime; só lê zonas.

REGRA DE OURO (Cris): NUNCA inventar zona — consumir o indicador que já existe (OB Detector). Aqui só LÊ.
- Fonte: my-strategy/core/bar_store/store/pine_boxes_{tf}.json (data.studies[].zones), estudo 'OB Detector'.
- DEMANDA = zona perto-de/abaixo do preço (LONG watch). SUPPLY (acima) NÃO entra: a doutrina do Cris só
  permite short em 4337-82 macro — auto-short floodaria e violaria o pacto. Auto-watch = só compras.
- Convergência multi-TF (15M+60M) = mais forte (marcado na nota).
py3.9 stdlib. Sem efeitos colaterais — função pura de leitura."""
import os, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STORE = REPO / "my-strategy/core/bar_store/store"
TFS = tuple((os.environ.get("OB_WATCH_TFS") or "15,60").split(","))   # TFs a ler (default 15M+60M intradiário)
NEAR_PTS = float(os.environ.get("OB_WATCH_NEAR_PTS") or 70.0)         # só demandas até NEAR_PTS abaixo do preço
MAX_ZONES = int(os.environ.get("OB_WATCH_MAX") or 5)                  # cap de zonas auto (evita flood)
ENABLED = os.environ.get("OB_WATCH_OFF", "") != "1"                   # destravável


def _read_ob(tf):
    """Devolve lista de {high, low} do OB Detector no store para o TF, ou []."""
    p = STORE / f"pine_boxes_{tf}.json"
    try:
        d = json.load(open(p))
    except Exception:
        return []
    studies = (d.get("data") or {}).get("studies") or []
    for s in studies:
        if "OB" in (s.get("name") or ""):
            return [z for z in (s.get("zones") or []) if "high" in z and "low" in z]
    return []


def _overlaps(a_lo, a_hi, b_lo, b_hi):
    return not (a_hi < b_lo or a_lo > b_hi)


def load_ob_zones(price, declared_zones=None):
    """Demandas OB perto do preço como zonas de vigia LONG (formato trader_map). Dedup vs zonas declaradas
    (declarada tem prioridade — OB que sobrepõe uma declarada é descartada). Marca convergência multi-TF.
    Devolve lista de dicts {id, low, high, tese:LONG, criticidade:critica, nota, source:ob_auto}."""
    if not ENABLED or not price:
        return []
    declared = declared_zones or []
    # recolhe demandas de todos os TFs, com o(s) TF(s) onde aparece
    raw = {}   # (low,high) arredondado -> set de TFs
    for tf in TFS:
        for z in _read_ob(tf):
            lo, hi = float(z["low"]), float(z["high"])
            # DEMANDA perto do preço: topo da zona <= preço+3 (abaixo/no preço) E dentro da banda NEAR_PTS
            if hi <= price + 3.0 and hi >= price - NEAR_PTS:
                key = (round(lo, 1), round(hi, 1))
                raw.setdefault(key, set()).add(tf)
    # funde zonas quase-iguais entre TFs (convergência) por sobreposição
    merged = []   # [lo, hi, tfs]
    for (lo, hi), tfs in sorted(raw.items(), key=lambda kv: -kv[0][1]):
        placed = False
        for m in merged:
            if _overlaps(lo, hi, m[0], m[1]):
                m[0] = min(m[0], lo); m[1] = max(m[1], hi); m[2] |= tfs; placed = True; break
        if not placed:
            merged.append([lo, hi, set(tfs)])
    out = []
    for lo, hi, tfs in merged:
        # dedup vs declaradas
        if any(_overlaps(lo, hi, float(z["low"]), float(z["high"])) for z in declared):
            continue
        conv = "+".join(sorted(tfs))
        strong = len(tfs) >= 2
        out.append({
            "id": f"ob_auto_{lo:.0f}_{hi:.0f}",
            "low": lo, "high": hi, "tese": "LONG", "criticidade": "critica",
            "nota": (f"OB Detector v11 AUTO ({conv}{'  CONVERGENTE' if strong else ''}) — demanda perto do "
                     f"preço, vigia automática (não declarada). Rejeição p/ cima aqui = compra."),
            "source": "ob_auto", "conv_tfs": sorted(tfs),
        })
    # mais perto do preço primeiro, cap
    out.sort(key=lambda z: price - z["high"])
    return out[:MAX_ZONES]


if __name__ == "__main__":
    import sys
    price = float(sys.argv[1]) if len(sys.argv) > 1 else 4345.0
    zs = load_ob_zones(price)
    print(f"OB auto-watch @ preço {price} — {len(zs)} demandas (TFs {TFS}, near {NEAR_PTS}pts, cap {MAX_ZONES}):")
    for z in zs:
        print(f"  {z['low']:.1f}-{z['high']:.1f}  [{'+'.join(z['conv_tfs'])}]  {z['nota'][:60]}")
