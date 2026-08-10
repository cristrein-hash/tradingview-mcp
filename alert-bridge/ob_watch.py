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
    """Devolve [{high, low, text}] do OB Detector no store. all_boxes traz o TIPO REAL (DEMAND/SUPPLY);
    fallback para zones (sem tipo) se all_boxes ausente."""
    p = STORE / f"pine_boxes_{tf}.json"
    try:
        d = json.load(open(p))
    except Exception:
        return []
    for s in ((d.get("data") or {}).get("studies") or []):
        if "OB" in (s.get("name") or ""):
            out = [{"high": b["high"], "low": b["low"], "text": str(b.get("text") or "").upper()}
                   for b in (s.get("all_boxes") or []) if "high" in b and "low" in b]
            if out:
                return out
            return [{"high": z["high"], "low": z["low"], "text": ""}
                    for z in (s.get("zones") or []) if "high" in z and "low" in z]
    return []


def _recent_max_close(n=40):
    """Máximo close das últimas n barras 15M do store — para saber se o preço RECONQUISTOU uma supply
    (fecho real acima do topo = polaridade virada suporte). Facto das barras, não métrica inventada."""
    try:
        rows = [json.loads(l) for l in open(STORE / "bars_15m.jsonl") if l.strip() and l[0] == "{"]
    except Exception:
        return None
    cs = [b["c"] for b in rows[-n:] if "c" in b]
    return max(cs) if cs else None


def _overlaps(a_lo, a_hi, b_lo, b_hi):
    return not (a_hi < b_lo or a_lo > b_hi)


def load_ob_zones(price, declared_zones=None):
    """Zonas OB perto do preço como vigia LONG (formato trader_map). Dois tipos, ambos por ESTRUTURA REAL:
      - DEMAND (tipo real) abaixo/no preço = suporte nativo.
      - SUPPLY (tipo real) RECONQUISTADA (preço acima do topo, OU a atravessá-la com fecho recente > topo)
        = suporte por POLARIDADE (ex-supply virada suporte — doutrina Cris no trader_map).
    Dedup vs declaradas (declarada prioridade). Convergência multi-TF marcada."""
    if not ENABLED or not price:
        return []
    declared = declared_zones or []
    rmax = _recent_max_close()                                    # p/ reconquista de supply (facto)
    raw = {}   # (low,high) -> {"tfs": set, "kind": "demand"|"polarity"}
    for tf in TFS:
        for z in _read_ob(tf):
            lo, hi, txt = float(z["low"]), float(z["high"]), z["text"]
            if hi < price - NEAR_PTS:                             # fora da banda por baixo
                continue
            kind = None
            if hi <= price + 3.0:
                # zona ABAIXO do preço: demanda nativa; se for SUPPLY, o preço já a reconquistou = polaridade
                kind = "polarity" if "SUPPLY" in txt else "demand"
            elif "SUPPLY" in txt and (lo - 3.0) <= price <= hi and rmax is not None and rmax > hi:
                # supply que o preço ATRAVESSA e JÁ reconquistou (fecho recente > topo) = suporte polaridade
                kind = "polarity"
            if kind is None:
                continue
            key = (round(lo, 1), round(hi, 1))
            e = raw.setdefault(key, {"tfs": set(), "kind": kind})
            e["tfs"].add(tf)
            if kind == "polarity":
                e["kind"] = "polarity"
    # funde zonas quase-iguais entre TFs (convergência) por sobreposição
    merged = []   # [lo, hi, tfs, kind]
    for (lo, hi), meta in sorted(raw.items(), key=lambda kv: -kv[0][1]):
        placed = False
        for m in merged:
            if _overlaps(lo, hi, m[0], m[1]):
                m[0] = min(m[0], lo); m[1] = max(m[1], hi); m[2] |= meta["tfs"]
                if meta["kind"] == "polarity":
                    m[3] = "polarity"
                placed = True; break
        if not placed:
            merged.append([lo, hi, set(meta["tfs"]), meta["kind"]])
    out = []
    for lo, hi, tfs, kind in merged:
        # dedup vs declaradas
        if any(_overlaps(lo, hi, float(z["low"]), float(z["high"])) for z in declared):
            continue
        conv = "+".join(sorted(tfs))
        strong = len(tfs) >= 2
        tipo = "ex-SUPPLY reconquistada (POLARIDADE=suporte)" if kind == "polarity" else "demanda nativa"
        out.append({
            "id": f"ob_auto_{lo:.0f}_{hi:.0f}",
            "low": lo, "high": hi, "tese": "LONG", "criticidade": "critica",
            "nota": (f"OB Detector v11 AUTO ({conv}{'  CONVERGENTE' if strong else ''}) — {tipo} perto do "
                     f"preço, vigia automática (não declarada). Rejeição p/ cima aqui = compra."),
            "source": "ob_auto", "conv_tfs": sorted(tfs), "kind": kind,
        })
    # mais perto do preço primeiro, cap
    out.sort(key=lambda z: price - z["high"])
    return out[:MAX_ZONES]


if __name__ == "__main__":
    import sys
    price = float(sys.argv[1]) if len(sys.argv) > 1 else 4345.0
    zs = load_ob_zones(price)
    print(f"OB auto-watch @ preço {price} — {len(zs)} zonas (TFs {TFS}, near {NEAR_PTS}pts, cap {MAX_ZONES}):")
    for z in zs:
        print(f"  {z['low']:.1f}-{z['high']:.1f}  [{'+'.join(z['conv_tfs'])}]  {z['kind']:8}  {z['nota'][:55]}")
