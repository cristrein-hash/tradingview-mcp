#!/usr/bin/env python3
"""MOTOR DE CRUZAMENTO MTF (Cris 2026-07-21) — compõe UMA imagem contextual a partir da leitura profunda.

Consome contextual_read.read_all() (zonas OB TIPADAS SUPPLY/DEMAND + SVP POC/VAH/VAL + estrutura SMC BOS/CHoCH,
por TF) + regime vivo, e CRUZA entre timeframes. NÃO é vetos/score/determinismo — é a composição de camadas numa
imagem única para leitura contextual (feedback_contextual_convergence_not_determinism):

  1. Confluência de zonas OB: uma zona no TF-foco (15M) confirmada por zona OB do MESMO TIPO que sobrepõe em preço
     em 1H/4H/1D = institucional (o que faltou no BUY dos 4000). Marca quantos e quais TFs confirmam.
  2. Confluência SVP: POC/VAH/VAL de 1H/4H/1D que cai DENTRO da zona = suporte/resistência de valor.
  3. Confluência SMC: box SMC de HTF que sobrepõe a zona.
  4. Estrutura BOS/CHoCH por TF: último evento perto do preço + caráter (continuação/reversão).
  5. Regime vivo (BEAR/BULL/RANGE): alinhamento com a direção da zona (contexto, NUNCA veto).

Uso: python3 mtf_cross.py            (imprime a imagem cruzada)
     from mtf_cross import cross      (devolve o dict composto)
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from contextual_read import read_all, TFS

CORE = Path(__file__).resolve().parent
REGIME_F = CORE / "regime_engine/.regime_state/current_regime.json"
NAS_F = CORE / "bar_store/store/nas_15m.jsonl"
BUB_F = CORE / "bar_store/store/bubbles_15m.jsonl"
BARS15_F = CORE / "bar_store/store/bars_15m.jsonl"       # p/ ancorar NAS/bubbles ao PREÇO (join por tempo)
OB_NAME = "OB Detector"
SMC_NAME = "Smart Money"
HTFS = ("1H", "4H", "1D")            # timeframes superiores para confirmar o foco
NAS_MAP = {"plot_0": "LONG", "plot_1": "SHORT"}   # shape_plots reais (LONG/SHORT; ignora TOP/BOTTOM per canon)
NAS_MAX_AGE_S = 6 * 3600             # NAS mais velho que isto = contexto stale (mostra idade)
# Bubbles Leviathan — mapa canónico (cp_engine/a1a2_context_build): plot_0/2/4=BUY S/M/L · plot_6/8/10=SELL S/M/L.
# NOTA: polaridade buy/sell é RAW; a INTERPRETAÇÃO (bullish/bearish) é contexto-dependente (feedback_bubbles_polarity_rule).
BUB_BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}
BUB_SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
BUB_WINDOW_S = 3 * 3600              # janela recente de fluxo de bubbles (display global)
FLOW_RECENT_S = 24 * 3600            # confluência espacial NAS/bubbles = só fluxo das últimas 24h (não o store todo)


def _overlap(a_hi, a_lo, b_hi, b_lo):
    """Duas bandas de preço intersectam-se?"""
    return a_lo <= b_hi and b_lo <= a_hi


def _regime():
    try:
        d = json.loads(REGIME_F.read_text())
        return {"regime": d.get("regime"), "stable": d.get("stable_daily"), "as_of": d.get("as_of_bar")}
    except Exception:
        return {"regime": None, "stable": None, "as_of": None}


def _jl(f):
    try:
        return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def _nas_recent():
    """Sinal NAS mais recente (LONG/SHORT) do store 15M + idade. Sem preço no store → camada DIRECIONAL, não espacial."""
    rows = [r for r in _jl(NAS_F) if r.get("t") and NAS_MAP.get(r.get("plot"))]
    if not rows:
        return None
    r = max(rows, key=lambda r: r["t"])
    return {"dir": NAS_MAP[r["plot"]], "t": r["t"], "age_s": int(time.time()) - r["t"]}


def _bubbles_recent():
    """Fluxo RAW de bubbles na janela recente: soma ponderada por tamanho (S1/M2/L3) de BUY vs SELL — SÓ p/ display.
    Polaridade RAW; interpretação bullish/bearish é contexto-dependente (não asserida aqui)."""
    cut = int(time.time()) - BUB_WINDOW_S
    buy = sell = 0
    for r in _jl(BUB_F):
        if not r.get("t") or r["t"] < cut:
            continue
        p = r.get("plot")
        if p in BUB_BUY:
            buy += BUB_BUY[p]
        elif p in BUB_SELL:
            sell += BUB_SELL[p]
    return {"buy": buy, "sell": sell}


def _bars15_map():
    """{t -> (low, high)} das barras 15M do store, p/ dar PREÇO aos eventos NAS/bubbles (join por tempo)."""
    m = {}
    for r in _jl(BARS15_F):
        t = r.get("t")
        if t is not None and r.get("l") is not None and r.get("h") is not None:
            m[int(t)] = (r["l"], r["h"])
    return m


LEG_LOOKBACK = 12                    # ~3h de 15M — a PERNA imediata (não o regime macro 4H/1D lento)
LEG_STRONG_PTS = 20.0                # deslocamento ≥20pts na janela = perna com força (markup/markdown)


def _leg_read(px):
    """DIREÇÃO E FORÇA DA PERNA IMEDIATA (15M, ~3h) — a leitura que faltou na noite 2026-07-21 (o motor shortou
    um markup porque o regime macro dizia BEAR). Estrutura de swing (HH+HL = markup UP / LH+LL = markdown DOWN)
    + deslocamento líquido. NÃO é o regime (macro lento); é a perna operativa. Devolve {dir, net_pts, strong}."""
    bars = [r for r in _jl(BARS15_F) if r.get("c") is not None][-LEG_LOOKBACK - 1:]
    if len(bars) < 6:
        return {"dir": "RANGE", "net_pts": 0.0, "strong": False}
    highs = [b["h"] for b in bars]; lows = [b["l"] for b in bars]; closes = [b["c"] for b in bars]
    net = closes[-1] - closes[0]
    mid = len(bars) // 2
    old_hi, new_hi = max(highs[:mid]), max(highs[mid:])
    old_lo, new_lo = min(lows[:mid]), min(lows[mid:])
    hh_hl = new_hi > old_hi and new_lo > old_lo         # higher-high + higher-low = markup
    lh_ll = new_hi < old_hi and new_lo < old_lo         # lower-high + lower-low = markdown
    if hh_hl and net > 0:
        d = "UP"
    elif lh_ll and net < 0:
        d = "DOWN"
    else:
        d = "RANGE"
    return {"dir": d, "net_pts": round(net, 1), "strong": abs(net) >= LEG_STRONG_PTS and d != "RANGE"}


def _consumed(zones, px, leg_dir):
    """Zonas OB do MESMO tipo VARRIDAS na direção da perna, agora do lado 'já-comido' do preço = sinal de FORÇA
    (compra a esmagar supply em cadeia = o oposto de resistência). Conta supplies abaixo (markup) / demands acima
    (markdown). Foi a cadeia 4066→4077→4084→... consumida que o motor ignorou."""
    if px is None or leg_dir == "RANGE":
        return 0
    if leg_dir == "UP":     # markup: supplies que ficaram ABAIXO do preço = comidas
        return sum(1 for z in zones if z["type"] == "SUPPLY" and z["high"] < px)
    return sum(1 for z in zones if z["type"] == "DEMAND" and z["low"] > px)   # markdown


def _nas_events(bmap):
    """Eventos NAS (últimas 24h) com PREÇO real (do bar no tempo do evento): LONG→low do bar (fundo marcado),
    SHORT→high (topo). Só assim a confluência é ESPACIAL — um NAS SHORT lá em cima NÃO conta para uma DEMAND."""
    cut = int(time.time()) - FLOW_RECENT_S
    out = []
    for r in _jl(NAS_F):
        t = r.get("t"); d = NAS_MAP.get(r.get("plot"))
        if t is None or not d or int(t) < cut:
            continue
        b = bmap.get(int(t))
        if not b:
            continue
        out.append({"dir": d, "price": b[0] if d == "LONG" else b[1], "t": int(t)})
    return out


def _bub_events(bmap):
    """Eventos bubble (últimas 24h) com FAIXA de preço (low..high do bar) + lado BUY/SELL (mapa canónico).
    Confluência espacial: o bar do evento tem de SOBREPOR a zona. Polaridade RAW (contexto-dependente)."""
    cut = int(time.time()) - FLOW_RECENT_S
    out = []
    for r in _jl(BUB_F):
        t = r.get("t"); p = r.get("plot")
        side = "BUY" if p in BUB_BUY else ("SELL" if p in BUB_SELL else None)
        if t is None or not side or int(t) < cut:
            continue
        b = bmap.get(int(t))
        if not b:
            continue
        out.append({"side": side, "lo": b[0], "hi": b[1], "t": int(t)})
    return out


def _ob_zones(tf_ctx):
    """Zonas OB Detector TIPADAS do TF."""
    for nm, zs in tf_ctx.get("zones", {}).items():
        if OB_NAME.lower() in nm.lower():
            return [z for z in zs if z.get("type")]      # só as tipadas SUPPLY/DEMAND
    return []


def _smc_boxes(tf_ctx):
    for nm, zs in tf_ctx.get("zones", {}).items():
        if SMC_NAME.lower() in nm.lower():
            return zs
    return []


def _svp_levels(tf_ctx):
    v = tf_ctx.get("values", {})
    for nm, d in v.items():
        if nm == "SVP Levels":
            return {k: d[k] for k in ("POC", "VAH", "VAL") if d.get(k) is not None}
    return {}


def _momentum(tf_ctx):
    """RSI / ADX / CHOP do TF (do reader, que já os lê) — camadas de momentum/tendência/chop p/ convergência."""
    v = tf_ctx.get("values", {})
    def g(study, key):
        for nm, d in v.items():
            if study.lower() in nm.lower() and d.get(key) is not None:
                return d[key]
        return None
    return {"rsi": g("Relative Strength", "RSI"), "rsi_ma": g("Relative Strength", "RSI-based MA"),
            "adx": g("Directional", "ADX"), "chop": g("Choppiness", "CHOP")}


def _structure(tf_ctx, px):
    """Último BOS e CHoCH mais próximos do preço + caráter inferido pela posição do preço.
    NOTA: LuxAlgo não dá direção no texto; a direção aqui é INFERIDA (preço acima/abaixo do nível) e precisa de
    confirmação visual do Cris. BOS = continuação; CHoCH = mudança de caráter (reversão)."""
    ev = tf_ctx.get("smc", [])
    if not ev or px is None:
        return {}
    def nearest(kind):
        cand = [e for e in ev if e["text"] == kind]
        if not cand:
            return None
        e = min(cand, key=lambda e: abs(e["price"] - px))
        return {"price": e["price"], "side": "acima" if e["price"] > px else "abaixo"}
    return {"BOS": nearest("BOS"), "CHoCH": nearest("CHoCH")}


def cross(ctx=None, focus="15M"):
    ctx = ctx or read_all()
    px = ctx.get("price")
    reg = _regime()
    tfmap = ctx["tf"]

    # pré-computa zonas HTF (OB tipadas + SMC boxes) e níveis SVP por TF
    htf_ob = {tf: _ob_zones(tfmap.get(tf, {})) for tf in HTFS}
    htf_smc = {tf: _smc_boxes(tfmap.get(tf, {})) for tf in HTFS}
    htf_svp = {tf: _svp_levels(tfmap.get(tf, {})) for tf in HTFS}

    out_zones = []
    for z in _ob_zones(tfmap.get(focus, {})):
        hi, lo, ty = z["high"], z["low"], z["type"]
        ob_conf, smc_conf, svp_conf = [], [], []
        for tf in HTFS:
            # confluência OB: MESMO tipo + sobreposição
            if any(_overlap(hi, lo, o["high"], o["low"]) and o["type"] == ty for o in htf_ob[tf]):
                ob_conf.append(tf)
            # confluência SMC: qualquer box sobrepõe
            if any(_overlap(hi, lo, b["high"], b["low"]) for b in htf_smc[tf]):
                smc_conf.append(tf)
            # confluência SVP: nível cai DENTRO da zona
            for k, lvl in htf_svp[tf].items():
                if lo <= lvl <= hi:
                    svp_conf.append(f"{tf} {k}")
        out_zones.append({
            "high": hi, "low": lo, "type": ty,
            "dist": abs((hi + lo) / 2 - (px or 0)),
            "contains_price": (px is not None and lo <= px <= hi),
            "ob_htf": ob_conf, "smc_htf": smc_conf, "svp": svp_conf,
            "institutional": len(ob_conf) >= 1,
        })
    out_zones.sort(key=lambda z: z["dist"])

    structure = {tf: _structure(tfmap.get(tf, {}), px) for tf in (focus,) + HTFS}
    nas = _nas_recent()
    bubbles = _bubbles_recent()
    momentum = _momentum(tfmap.get(focus, {}))     # ADX/CHOP do foco + RSI 15M
    momentum["rsi_5m"] = _momentum(tfmap.get("5M", {})).get("rsi")   # RSI multi-TF: alinhamento amortece o ruído
    momentum["rsi_15m"] = momentum.get("rsi")                        # da barra em formação (Cris 2026-07-21)
    momentum["rsi_1h"] = _momentum(tfmap.get("1H", {})).get("rsi")
    bmap = _bars15_map()
    nas_ev = _nas_events(bmap)                      # eventos NAS/bubbles ANCORADOS ao preço (join por tempo)
    bub_ev = _bub_events(bmap)
    # concordância ESPACIAL: o evento tem de cair NO preço da zona (NAS) ou o seu bar SOBREPOR a zona (bubbles).
    # Um NAS SHORT lá em cima já NÃO conta para uma DEMAND cá em baixo (fim do remendo direcional-global).
    for z in out_zones:
        hi, lo, ty = z["high"], z["low"], z["type"]
        want = "LONG" if ty == "DEMAND" else "SHORT"
        want_side = "BUY" if ty == "DEMAND" else "SELL"
        z_nas = [e for e in nas_ev if e["dir"] == want and lo <= e["price"] <= hi]
        z_bub = [e for e in bub_ev if e["side"] == want_side and _overlap(hi, lo, e["hi"], e["lo"])]
        z["nas_agree"] = len(z_nas) > 0
        z["bub_agree"] = (len(z_bub) > 0) if bub_ev else None
        z["nas_n"] = len(z_nas); z["bub_n"] = len(z_bub)
    leg = _leg_read(px)
    leg["consumed"] = _consumed(out_zones, px, leg["dir"])   # zonas varridas em cadeia = força da perna
    return {"price": px, "regime": reg, "focus": focus, "zones": out_zones,
            "structure": structure, "nas": nas, "bubbles": bubbles, "momentum": momentum, "leg": leg}


def _regime_align(ty, regime):
    """Alinhamento contexto (NUNCA veto): DEMAND(long) favorável em BULL; SUPPLY(short) favorável em BEAR."""
    if not regime:
        return "?"
    if ty == "DEMAND":
        return "a-favor" if regime == "BULL" else ("contra-tendência" if regime == "BEAR" else "neutro")
    return "a-favor" if regime == "BEAR" else ("contra-tendência" if regime == "BULL" else "neutro")


def print_view():
    im = cross()
    px = im["price"]; reg = im["regime"]
    print(f"═══ CRUZAMENTO MTF · foco {im['focus']} · preço {px} · regime {reg['regime']} ({reg['as_of']}) ═══")
    lg = im.get("leg") or {}
    print(f"[PERNA IMEDIATA 15M ~3h]  dir {lg.get('dir')} · {lg.get('net_pts'):+.0f}pts · {'FORTE' if lg.get('strong') else 'fraca'} · zonas consumidas em cadeia: {lg.get('consumed')}")
    nas, bub = im.get("nas"), im.get("bubbles") or {}
    print("\n[FLUXO 15M]  (direcional, não espacial — polaridade bubbles = contexto)")
    if nas:
        age_h = nas["age_s"] / 3600
        stale = " STALE" if nas["age_s"] > NAS_MAX_AGE_S else ""
        print(f"  NAS       último {nas['dir']} há {age_h:.1f}h{stale}")
    else:
        print("  NAS       — sem sinal no store")
    if bub.get("buy") or bub.get("sell"):
        dom = "BUY" if bub["buy"] >= bub["sell"] else "SELL"
        print(f"  Bubbles   janela {BUB_WINDOW_S//3600}h: BUY {bub['buy']} vs SELL {bub['sell']} → domínio {dom}")
    else:
        print("  Bubbles   — sem bubbles na janela")
    print("\n[ESTRUTURA SMC por TF]  (direção INFERIDA — confirmar visual)")
    for tf in (im["focus"],) + HTFS:
        s = im["structure"].get(tf) or {}
        b, ch = s.get("BOS"), s.get("CHoCH")
        parts = []
        if ch: parts.append(f"CHoCH {ch['price']:.1f} ({ch['side']})")
        if b: parts.append(f"BOS {b['price']:.1f} ({b['side']})")
        print(f"  {tf:4} {' · '.join(parts) if parts else '—'}")
    print("\n[ZONAS OB no foco — cruzadas com HTF]  (ordenadas por proximidade ao preço)")
    for z in im["zones"][:6]:
        mark = "◄PREÇO" if z["contains_price"] else ""
        conf = []
        if z["ob_htf"]: conf.append("OB " + "/".join(z["ob_htf"]))
        if z["smc_htf"]: conf.append("SMC " + "/".join(z["smc_htf"]))
        if z["svp"]: conf.append("SVP " + ", ".join(z["svp"]))
        strength = "🏛️ INSTITUCIONAL" if z["institutional"] else "· local"
        align = _regime_align(z["type"], reg["regime"])
        flow = []
        if z.get("nas_agree"): flow.append(f"NAS✓×{z.get('nas_n', 0)}")
        if z.get("bub_agree") is True: flow.append(f"bubbles✓×{z.get('bub_n', 0)}")
        fs = ("  fluxo:" + " ".join(flow)) if flow else ""
        print(f"  {z['low']:.1f}-{z['high']:.1f} {z['type']:6} {mark:6} {strength:16} regime:{align}{fs}")
        if conf:
            print(f"         confluência: {' | '.join(conf)}")


if __name__ == "__main__":
    print_view()
