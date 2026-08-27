#!/usr/bin/env python3
"""LIQUIDITY MAP — mapa hierarquizado de pools SSL/BSL (doutrina PDF 26/08, ordem Cris "começa pelo mapa").

EXTENSÃO do eixo liquidez E0 (consolidation_check corrido; context_liquidity=eventos 15M intradiários,
ISTO=pools estruturais D→4H→1H). Zero recomputação de fontes: consome bars_1d do store + RAW 1H/4H
canónicos + SVP dos study_values (evidência de concentração de volume). CONTEXTO, nunca gatilho.

Cada pool: side (SSL sob mínimos / BSL sobre máximas) · zona [lo,hi] (extremos agrupados ≤0.5×ATR do TF
= zona, não linha) · tf origem · evidência (nº extremos, sobreposição SVP, reações) · relevância
ALTA/MÉDIA/BAIXA (heurística v0 declarada: peso do TF + repetição + SVP + reação) · ciclo de vida
(PENDENTE → CAPTURADA:SWEEP / CAPTURADA:RUN / INCONCLUSIVA, classificada pelo comportamento PÓS-captura,
nunca pelo rompimento) · roadmap = pools pendentes ordenados por distância ao preço (acima/abaixo).

Regras da doutrina honradas: zona-não-linha · D/4H/1H apenas (sem <1H no mapa principal) · sweep≠rompimento
(pós-captura decide) · mapa dinâmico (recomputado por chamada, stateless) · probabilístico (relevância,
não certeza). Saída: dict + snapshot JSON opcional p/ o dossiê E0. py3.9 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
STORE = REPO / "my-strategy/core/bar_store/store"
REV = REPO / "my-strategy/research/revalidation"
SNAP_OUT = REPO / "external_factors_v2/snapshots/liquidity_map.json"

TF_SRC = {"D": (STORE / "bars_1d.jsonl", 3.0), "4H": (REV / "raw_4h_ohlc.jsonl", 2.0),
          "1H": (REV / "raw_1h_ohlc.jsonl", 1.0)}
LOOKBACK = {"D": 200, "4H": 240, "1H": 240}          # barras por TF (mapa estrutural, não micro)
CLUSTER_ATR = 0.5                                     # extremos a ≤0.5×ATR(tf) agrupam numa zona
SWING_K = 3                                           # pivô fractal k barras de cada lado
RUN_ATR = 1.0                                         # pós-captura: continuou ≥1 ATR além = RUN
SWEEP_BARS = 6                                        # pós-captura: voltou p/ dentro em ≤6 barras = SWEEP


def _jl(p, n):
    try:
        rows = [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
        rows.sort(key=lambda x: x["t"])
        return rows[-n:]
    except Exception:
        return []


def _atr(bars, n=14):
    trs = [max(b["h"] - b["l"], abs(b["h"] - a["c"]), abs(b["l"] - a["c"]))
           for a, b in zip(bars, bars[1:])]
    return (sum(trs[-n:]) / min(n, len(trs))) if trs else 5.0


def _swings(bars, k=SWING_K):
    """Pivôs confirmados (só barras já fechadas dos dois lados). Devolve (his, los) com índice."""
    his, los = [], []
    for i in range(k, len(bars) - k):
        if bars[i]["h"] == max(b["h"] for b in bars[i - k:i + k + 1]):
            his.append((i, bars[i]["h"]))
        if bars[i]["l"] == min(b["l"] for b in bars[i - k:i + k + 1]):
            los.append((i, bars[i]["l"]))
    return his, los


def _cluster(points, atr):
    """Agrupa extremos próximos (≤CLUSTER_ATR×atr) em zonas. points=[(i,price)]. -> [{lo,hi,n,born_i,touches_i}]"""
    out = []
    for i, p in sorted(points, key=lambda x: x[1]):
        # largura total capada a 1×ATR (fix 27/08: chain-merge criava "zonas" de 170pt = range, não pool)
        if out and (p - out[-1]["hi"]) <= CLUSTER_ATR * atr and (p - out[-1]["lo"]) <= atr:
            out[-1]["hi"] = max(out[-1]["hi"], p)
            out[-1]["n"] += 1
            out[-1]["idx"].append(i)
        else:
            out.append({"lo": p, "hi": p, "n": 1, "idx": [i]})
    for z in out:
        z["born_i"] = min(z["idx"])
    return out


def _svp_levels():
    """POC/VAH/VAL REAIS do indicador (estudo 'SVP Levels' que o bar-store funde nos study_values via
    data_get_study_values_at_bar — Developing POC/VA High/VA Low). AUDIT-FIX 26/08: a v0 filtrava por
    'volume profile' (nome errado → sempre vazio) e re-derivava evidência só do OHLC; agora LÊ o
    indicador, prioridade da regra do Cris."""
    lv = []
    for tf in ("15", "60", "240", "1D"):
        try:
            d = json.load(open(STORE / f"study_values_{tf}.json")).get("data") or {}
            for st in d.get("studies") or []:
                if st.get("name") == "SVP Levels":
                    for v in (st.get("values") or {}).values():
                        try:
                            lv.append(float(v))
                        except Exception:
                            pass
        except Exception:
            pass
    return lv


def _smc_eq(tf_store):
    """EQH/EQL do SMC LuxAlgo (smc_labels_{tf}.json do store) — POOLS DO INDICADOR, fonte PRIORITÁRIA
    (ordem Cris 27/08 'indicador sempre primeiro'; labels reativados nas 4 tabs 27/08).
    Devolve [(price, kind)]."""
    out = []
    try:
        d = json.load(open(STORE / f"smc_labels_{tf_store}.json")).get("data") or {}
        for st in d.get("studies") or []:
            for l in st.get("labels") or []:
                t = (l.get("text") or "").strip().upper()
                px = l.get("price")
                if px and t.startswith(("EQH", "EQL")):
                    out.append((float(px), t[:3]))
    except Exception:
        pass
    return out


def _lifecycle(zone, side, bars, atr):
    """Comportamento PÓS-captura (doutrina: rompimento NÃO classifica). Avalia após born_i."""
    lo, hi = zone["lo"], zone["hi"]
    edge = lo if side == "SSL" else hi
    cap_i = None
    for i in range(zone["born_i"] + 1, len(bars)):
        pierced = bars[i]["l"] < edge if side == "SSL" else bars[i]["h"] > edge
        if pierced:
            cap_i = i
            break
    if cap_i is None:
        return "PENDENTE", None
    ext = min(b["l"] for b in bars[cap_i:]) if side == "SSL" else max(b["h"] for b in bars[cap_i:])
    depth = (edge - ext) if side == "SSL" else (ext - edge)
    back = None
    for j in range(cap_i, min(len(bars), cap_i + SWEEP_BARS + 1)):
        ok = bars[j]["c"] > edge if side == "SSL" else bars[j]["c"] < edge
        if ok:
            back = j
            break
    if back is not None and depth < RUN_ATR * atr * 2:
        return "CAPTURADA:SWEEP", cap_i
    if depth >= RUN_ATR * atr and back is None:
        return "CAPTURADA:RUN", cap_i
    return "CAPTURADA:INCONCLUSIVA", cap_i


def _relevance(zone, tf_w, svp_hit, touches):
    """Heurística v0 DECLARADA (contexto, não gate): TF + repetição + SVP + reações."""
    score = tf_w + (zone["n"] - 1) * 0.5 + (1.0 if svp_hit else 0.0) + min(touches, 3) * 0.5
    return "ALTA" if score >= 4 else ("MEDIA" if score >= 2.5 else "BAIXA")


def build_map():
    px = None
    b1h = _jl(TF_SRC["1H"][0], LOOKBACK["1H"])
    if b1h:
        px = b1h[-1]["c"]
    svp = _svp_levels()
    pools = []
    for tf, (src, w) in TF_SRC.items():
        bars = _jl(src, LOOKBACK[tf])
        if len(bars) < 30:
            continue
        atr = _atr(bars)
        his, los = _swings(bars)
        # INDICADOR PRIMEIRO: EQH/EQL do SMC entram como extremos (ancorados ao índice da barra mais
        # próxima do preço do label) e marcam o pool como confirmado-pelo-indicador
        tf_store = {"D": "1D", "4H": "240", "1H": "60"}[tf]
        smc_pts = _smc_eq(tf_store)
        smc_prices = set()
        for px_l, kind in smc_pts:
            near_i = min(range(len(bars)),
                         key=lambda i: abs(((bars[i]["h"] if kind == "EQH" else bars[i]["l"])) - px_l))
            if kind == "EQH":
                his.append((near_i, px_l))
            else:
                los.append((near_i, px_l))
            smc_prices.add(round(px_l, 1))
        for side, pts in (("BSL", his), ("SSL", los)):
            for z in _cluster(pts, atr):
                status, cap_i = _lifecycle(z, side, bars, atr)
                touches = sum(1 for b in bars[z["born_i"]:]
                              if z["lo"] - 0.2 * atr <= (b["l"] if side == "SSL" else b["h"]) <= z["hi"] + 0.2 * atr)
                svp_hit = any(z["lo"] - 0.3 * atr <= s <= z["hi"] + 0.3 * atr for s in svp)
                smc_hit = any(z["lo"] - 0.3 * atr <= p <= z["hi"] + 0.3 * atr for p in smc_prices)
                rel = _relevance(z, w + (1.5 if smc_hit else 0.0), svp_hit, touches)
                pools.append({
                    "tf": tf, "side": side, "lo": round(z["lo"], 2), "hi": round(z["hi"], 2),
                    "n_extremos": z["n"], "svp": svp_hit, "smc": smc_hit, "reacoes": touches,
                    "relevancia": rel, "status": status,
                })
    # dedup entre TFs: zonas sobrepostas mesmo side → fica a de maior TF (D>4H>1H), soma evidência
    order = {"D": 0, "4H": 1, "1H": 2}
    pools.sort(key=lambda p: (p["side"], order[p["tf"]]))
    merged = []
    for p in pools:
        hit = next((m for m in merged if m["side"] == p["side"]
                    and not (p["hi"] < m["lo"] or p["lo"] > m["hi"])), None)
        if hit:
            hit["n_extremos"] += p["n_extremos"]
            hit["svp"] = hit["svp"] or p["svp"]
            hit["smc"] = hit.get("smc") or p.get("smc")
            hit["lo"] = min(hit["lo"], p["lo"]); hit["hi"] = max(hit["hi"], p["hi"])
            if p["relevancia"] == "ALTA":
                hit["relevancia"] = "ALTA"
        else:
            merged.append(dict(p))
    # roadmap: pendentes ordenados por distância ao preço
    roadmap = {"acima": [], "abaixo": []}
    if px:
        pend = [p for p in merged if p["status"] == "PENDENTE"]
        roadmap["acima"] = sorted([p for p in pend if p["lo"] > px], key=lambda p: p["lo"] - px)[:5]
        roadmap["abaixo"] = sorted([p for p in pend if p["hi"] < px], key=lambda p: px - p["hi"])[:5]
    return {"ts": int(dt.datetime.now(dt.timezone.utc).timestamp()), "price": px,
            "pools": merged, "roadmap": roadmap}


def write_snapshot():
    m = build_map()
    tmp = SNAP_OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False))
    import os
    os.replace(tmp, SNAP_OUT)
    return m


def print_map():
    m = build_map()
    print(f"═══ LIQUIDITY MAP · preço {m['price']} · {len(m['pools'])} pools ═══")
    for side in ("BSL", "SSL"):
        ps = [p for p in m["pools"] if p["side"] == side and p["relevancia"] != "BAIXA"]
        ps.sort(key=lambda p: -p["lo"])
        print(f"[{side}]")
        for p in ps[:10]:
            print(f"  {p['tf']:>2} {p['lo']:.1f}-{p['hi']:.1f} · {p['relevancia']} · {p['status']}"
                  f" · ext {p['n_extremos']} · SMC {'✓' if p.get('smc') else '·'} · SVP {'✓' if p['svp'] else '·'} · reações {p['reacoes']}")
    print("[ROADMAP pendentes]")
    for d in ("acima", "abaixo"):
        for p in m["roadmap"][d]:
            print(f"  {d} → {p['tf']} {p['side']} {p['lo']:.1f}-{p['hi']:.1f} ({p['relevancia']})")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        t = []
        # sintético: 3 equal-lows ~95 (±0.3) em vales distintos, resto acima
        import math
        bars = []
        for i in range(90):
            base = 100 + 2 * math.sin(i / 5)
            low = base - 1
            if i in (20, 45, 70):
                low = 95 + 0.1 * (i // 30)          # equal lows 95.0/95.1/95.2
            bars.append({"t": i * 3600, "o": base, "h": base + 1, "l": low, "c": base})
        atr = _atr(bars)
        his, los = _swings(bars)
        t.append(("swings detetados", len(his) > 0 and len(los) > 0))
        eq = [(i, p) for i, p in los if p < 96]
        cz = _cluster(eq, atr)
        t.append(("equal-lows ~95 agrupam em 1 zona", len(cz) == 1 and cz[0]["n"] == 3))
        # SWEEP sintético: fura a zona e fecha de volta acima em <=6 barras
        sw = [{"t": i, "o": 100, "h": 101, "l": 99, "c": 100} for i in range(10)]
        sw += [{"t": 10, "o": 100, "h": 100, "l": 93, "c": 96}]      # fura 95, fecha 96 (acima da edge)
        sw += [{"t": 11 + i, "o": 97, "h": 99, "l": 96, "c": 98} for i in range(6)]
        st, _ = _lifecycle({"lo": 95, "hi": 95, "born_i": 2, "n": 3, "idx": [2]}, "SSL", sw, 2.0)
        t.append(("fura+fecha-de-volta = CAPTURADA:SWEEP", st == "CAPTURADA:SWEEP"))
        # RUN sintético: queda contínua sem retorno
        drop = [{"t": i, "o": 100 - i, "h": 101 - i, "l": 99 - i, "c": 100 - i} for i in range(40)]
        st2, _ = _lifecycle({"lo": 90, "hi": 90, "born_i": 2, "n": 1, "idx": [2]}, "SSL", drop, 2.0)
        t.append(("queda contínua através da zona = RUN", st2 == "CAPTURADA:RUN"))
        # PENDENTE sintético: zona longe nunca tocada
        st3, _ = _lifecycle({"lo": 50, "hi": 50, "born_i": 2, "n": 1, "idx": [2]}, "SSL", bars, atr)
        t.append(("zona nunca tocada = PENDENTE", st3 == "PENDENTE"))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    print_map()
