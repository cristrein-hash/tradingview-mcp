#!/usr/bin/env python3
"""ENGINE MTF MULTIFATORIAL — faca-vs-dip nos LONG-candidatos, lendo TODOS os indicadores REAIS capturados
em 15M + 1H + 4H JUNTOS (replay as-of-bar). READ_OB_ZONES: consome OB Detector real; não re-deriva.
Linhas por TF: liquidez(15M) · vela(15M) · NAS · DMI · RSI · bubbles(janela) · OB-localização. Convergência
= todos os votos de todas as linhas e TFs. Sem thresholds inventados (terços da vela, +DI/−DI, RSI 30/70 =
convenções nativas). Rótulo objetivo forward. Amostra pequena = hipótese. py3."""
import sys, json, datetime as dt, bisect
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
import context_liquidity as CL
import bubble_polarity as BP   # FONTE ÚNICA da polaridade context-dependente (consumir, não hand-roll)
BT = ROOT / "alert-bridge/logs/backtests"
READS = ROOT / "alert-bridge/logs/candle_reads.jsonl"
MON = int(dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc).timestamp())
BUY = {"plot_0", "plot_2", "plot_4"}; SELL = {"plot_6", "plot_8", "plot_10"}


def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
def fnum(x):
    try: return float(str(x).replace("−", "-").replace(",", ""))
    except Exception: return None
def sv_get(sv, sub):
    st = sv.get("studies", sv) if isinstance(sv, dict) else sv
    for s in st or []:
        if sub in s.get("name", ""): return s.get("values") or {}
    return {}
def ob_zones(pb):
    out = []
    for s in ((pb.get("studies") if isinstance(pb, dict) else pb) or []):
        if "OB Detector" in s.get("name", ""):
            for b in (s.get("all_boxes") or []):
                if b.get("text"): out.append((b["text"], float(b["low"]), float(b["high"])))
    return out


# --- carregar as 3 capturas: por TF -> lista (as_of_t, row) ordenada + série de barras ---
def load_tf(tf):
    f = BT / f"XAUUSD_{tf}_replay_2026-08-10_to_2026-08-14.jsonl"
    rows = []; series = []
    for l in open(f):
        if not l.strip(): continue
        r = json.loads(l)
        oh = r.get("ohlcv"); bars = oh.get("bars") if isinstance(oh, dict) else oh
        if not bars: continue
        last = bars[-1]
        _bt = last.get("t") or last.get("time")   # 15M: t da barra (bate com bar_t dos eventos)
        aof = int(_bt) if _bt is not None else (int(r["replay_current_date"]) if r.get("replay_current_date") else None)
        if aof is None: continue   # HTF: cai para replay_current_date
        series.append((aof, float(last.get("o", last.get("open"))), float(last.get("h", last.get("high"))),
                       float(last.get("l", last.get("low"))), float(last.get("c", last.get("close")))))
        rows.append((aof, r))
    rows.sort(key=lambda x: x[0]); series.sort(key=lambda x: x[0])
    return rows, series
TF = {"15m": load_tf("15m"), "60m": load_tf("60m"), "240m": load_tf("240m")}
ROWS15, S15 = TF["15m"]; t15 = [x[0] for x in S15]

# REGIME macro (Layer1 1D) — CONSUMIR regime_l1_v4 (stateless), não re-inventar
sys.path.insert(0, str(ROOT / "my-strategy/core/regime_l1"))
import regime_l1_v4 as RL1
_daily = []
for _l in open(ROOT / "my-strategy/core/bar_store/store/bars_1d.jsonl"):
    if not _l.strip(): continue
    _d = json.loads(_l)
    _daily.append({"ts": dt.datetime.utcfromtimestamp(int(_d["t"])).strftime("%Y-%m-%dT00:00:00"),
                   "open": _d["o"], "high": _d["h"], "low": _d["l"], "close": _d["c"], "volume": 0})
_REGCLS = RL1.build_classifications(_daily)
def regime_at(t):
    s, _stale = RL1.latest_state_before(_REGCLS, t)
    return s or "UNKNOWN"
S240 = TF["240m"][1]; t240 = [x[0] for x in S240]


def htf_row(tf, t):
    rows = TF[tf][0]; keys = [r[0] for r in rows]
    i = bisect.bisect_right(keys, t) - 1
    return rows[i][1] if i >= 0 else None


# --- universo LONG ---
longs = {}
for l in open(READS):
    if not l.strip(): continue
    r = json.loads(l); bt = r.get("bar_t")
    if bt is None or int(bt) < MON: continue
    if ((r.get("read") or {}).get("direction") or "") == "LONG": longs[int(bt)] = r.get("bar") or {}


def atr(i, n=14):
    if i < n: return 5.0
    return (sum(max(S15[k][2]-S15[k][3], abs(S15[k][2]-S15[k-1][4]), abs(S15[k][3]-S15[k-1][4]))
                for k in range(i-n+1, i+1))/n) or 5.0
def outcome(t):
    if t not in t15: return None
    i = t15.index(t); a = atr(i); fut = S15[i+1:i+9]
    if not fut: return None
    c0 = S15[i][4]; mae = (c0-min(b[3] for b in fut))/a; mfe = (max(b[2] for b in fut)-c0)/a
    return {"label": "DIP" if mfe >= mae else "FACA", "mfe": round(mfe, 1), "mae": round(mae, 1)}


# ---------- leitores (voto: +1 breakdown / -1 dip / 0) ----------
def v_liq(i):
    liq = CL.compute([{"t": b[0], "o": b[1], "h": b[2], "l": b[3], "c": b[4]}
                      for b in S15[max(0, i-480):i+1]]) or {}
    seq = liq.get("sequence") or {}; hi = seq.get("high") or {}; lo = seq.get("low") or {}
    if liq.get("direction") == "down" and hi.get("state") == "FAILED" and hi.get("trapped") == "buyers": return 1
    if lo.get("state") == "RECLAIMED" and lo.get("trapped") == "shorts": return -1
    return 0
def v_candle(bar):
    o, h, l, c = bar.get("o"), bar.get("h"), bar.get("l"), bar.get("c")
    if None in (o, h, l, c): return 0
    rng = max(1e-9, h-l); cp = (c-l)/rng; low_w = (min(o, c)-l)/rng
    if low_w >= 0.5: return -1          # pavio inferior grande = absorção compradora (convenção: metade)
    if cp <= 1/3: return 1              # fecho no terço inferior
    return 0
def v_nas(sv):
    v = sv_get(sv, "NAS")
    if fnum(v.get("NAS_TOP_SIGNAL")): return 1
    if fnum(v.get("NAS_BOTTOM_SIGNAL")): return -1
    return 0
def v_dmi(sv):
    v = sv_get(sv, "Directional"); p, m = fnum(v.get("+DI")), fnum(v.get("-DI"))
    if p is not None and m is not None: return 1 if m > p else (-1 if p > m else 0)
    return 0
def v_rsi(sv):
    r = fnum(sv_get(sv, "Relative Strength").get("RSI"))
    if r is None: return 0
    return -1 if r <= 30 else (1 if r >= 70 else 0)   # convenção nativa 30/70
def bub_dom(bub, t, win_s=4*900):
    """lado dominante das bubbles na janela recente (buy/sell/None) — leitura crua, SEM polaridade."""
    for s in (bub if isinstance(bub, list) else []):
        if "Bubbles" in s.get("name", ""):
            win = [a for a in (s.get("activations") or []) if t-win_s <= (a.get("time") or 0) <= t]
            bw = sum(c for a in win for k, c in (a.get("shapes") or {}).items() if k in BUY)
            sw = sum(c for a in win for k, c in (a.get("shapes") or {}).items() if k in SELL)
            return "buy" if bw > sw else ("sell" if sw > bw else None)
    return None


def v_bub_ctx(bub, t, ctx):
    """polaridade CONTEXTO-DEPENDENTE via BUBBLE_POLARITY_RULE. voto +1 breakdown / -1 dip.
    reversal_top: BUY dominante = BEARISH (distribuição no topo). reversal_bottom: SELL = bullish.
    pullback_uptrend: BUY = bullish."""
    dom = bub_dom(bub, t)
    if dom is None: return 0
    c = ctx.get("context")
    if c == "reversal_top":     return 1 if dom == "buy" else 0      # buy no topo absorvido = bearish
    if c == "reversal_bottom":  return -1 if dom == "sell" else 1    # sell absorvido no fundo = bullish; buy=exaustão
    if c == "pullback_uptrend": return -1 if dom == "buy" else 1     # buy retoma = bullish
    return 0


def v_ctx(ctx):
    """o próprio CONTEXTO de região como voto: topo→breakdown, fundo/pullback→dip."""
    c = ctx.get("context")
    if c == "reversal_top": return 1
    if c in ("reversal_bottom", "pullback_uptrend"): return -1
    return 0


def v_4h_region(t, price):
    """ESTRUTURA LOCAL 4H (o call do Cris 12/08): preço no TOPO da range 4H + buy-bubbles absorvidas nos
    highs = DISTRIBUIÇÃO → breakdown (demandas abaixo cedem). Preço no FUNDO + sell absorvida = dip.
    Não depende de haver supply OB acima (topo novo não tem). Consome 4H bars + 4H bubbles reais."""
    i = bisect.bisect_right(t240, t) - 1
    if i < 5 or price is None: return 0, {}
    win = S240[max(0, i-9):i+1]
    hi = max(b[2] for b in win); lo = min(b[3] for b in win)
    if hi <= lo: return 0, {}
    pos = (price - lo) / (hi - lo)                       # 1=topo da range 4H, 0=fundo
    dom = bub_dom((htf_row("240m", t) or {}).get("pine_shapes_bubbles"), t, win_s=4*4*3600)  # janela 4H
    info = {"pos4h": round(pos, 2), "bub4h": dom}
    if pos >= 0.70 and dom == "buy": return 1, info      # distribuição no topo 4H
    if pos <= 0.30 and dom == "sell": return -1, info    # absorção no fundo 4H
    return 0, info
def v_ob(pb, price):
    """localização: rompe abaixo de DEMAND (breakdown) vs segura acima/dentro (contexto dip)."""
    dem = [(lo, hi) for (tx, lo, hi) in ob_zones(pb) if "DEMAND" in tx.upper()]
    if not dem or price is None: return 0
    inside = any(lo <= price <= hi for (lo, hi) in dem)
    below_all = all(price < lo for (lo, hi) in dem) if dem else False
    if below_all: return 1          # já abaixo de toda a demanda visível = breakdown
    if inside: return 0             # dentro de demand = ambíguo (pode furar) -> neutro
    return -1                        # acima da demanda = long tem suporte por baixo


# ---------- síntese MTF ----------
rows = []
for t, bar in sorted(longs.items()):
    oc = outcome(t)
    if not oc: continue
    i = t15.index(t)
    price = bar.get("c")
    row15 = htf_row("15m", t) or {}
    sv15 = row15.get("study_values"); bub15 = row15.get("pine_shapes_bubbles"); pb15 = row15.get("pine_boxes")
    pb4h = (htf_row("240m", t) or {}).get("pine_boxes")
    # CONTEXTO PRIMEIRO (fonte única BP.classify_bubble_context), depois polaridade
    zones = ob_zones(pb4h) + ob_zones(pb15)
    dem_below = any("DEMAND" in tx.upper() and hi < price for tx, lo, hi in zones)
    sup_above = any("SUPPLY" in tx.upper() and lo > price for tx, lo, hi in zones)
    rsi15 = fnum(sv_get(sv15, "Relative Strength").get("RSI"))
    ctx = BP.classify_bubble_context({"regime": regime_at(t),
                                      "zone_below": {"src": "demand" if dem_below else ""},
                                      "zone_above": {"src": "supply" if sup_above else ""}, "rsi": rsi15})
    r4h, r4info = v_4h_region(t, price)
    votes = {"15_liq": v_liq(i), "15_candle": v_candle(bar), "15_nas": v_nas(sv15),
             "15_dmi": v_dmi(sv15), "15_rsi": v_rsi(sv15),
             "15_bub": v_bub_ctx(bub15, t, ctx), "ctx": v_ctx(ctx), "4H_region": r4h}
    for tf, tag in (("60m", "1H"), ("240m", "4H")):
        hr = htf_row(tf, t) or {}
        sv = hr.get("study_values"); pb = hr.get("pine_boxes")
        votes[f"{tag}_nas"] = v_nas(sv); votes[f"{tag}_dmi"] = v_dmi(sv)
        votes[f"{tag}_rsi"] = v_rsi(sv); votes[f"{tag}_ob"] = v_ob(pb, price)
    brk = sum(1 for v in votes.values() if v > 0); dip = sum(1 for v in votes.values() if v < 0)
    rows.append({"t": t, **oc, "brk": brk, "dip": dip, "net": brk-dip, "votes": votes})

print(f"eventos: {len(rows)} | linhas/evento: {len(rows[0]['votes'])} (15M:6 + 1H:4 + 4H:4)")
print("="*112)
for r in rows:
    vv = " ".join("%s%+d" % (k, v) for k, v in r["votes"].items() if v)
    print("%s | %-4s mae%4.1f | BRK=%2d DIP=%2d net=%+d | %s" % (utc(r["t"]), r["label"], r["mae"], r["brk"], r["dip"], r["net"], vv))

print("\n" + "="*112)
print("DISCRIMINAÇÃO MTF (net = breakdown − dip, todas as linhas 15M+1H+4H)")
print("="*112)
import statistics as st
for lab in ("FACA", "DIP"):
    g = [r for r in rows if r["label"] == lab]
    if not g: continue
    nets = [r["net"] for r in g]
    print("%s n=%2d | net média %+.2f mediana %+.0f | net>=+2: %d/%d (%.0f%%) | net<=-2: %d/%d (%.0f%%)"
          % (lab, len(g), st.mean(nets), st.median(nets),
             sum(1 for x in nets if x >= 2), len(g), 100*sum(1 for x in nets if x >= 2)/len(g),
             sum(1 for x in nets if x <= -2), len(g), 100*sum(1 for x in nets if x <= -2)/len(g)))
print("\nSe BLOQUEAR quando net>=N:")
tf_ = sum(1 for r in rows if r["label"] == "FACA")
for N in (2, 3, 4):
    blk = [r for r in rows if r["net"] >= N]
    print("  net>=%d: bloqueia %2d (apanha %d/%d FACAs, mata %d DIPs)"
          % (N, len(blk), sum(1 for r in blk if r["label"] == "FACA"), tf_, sum(1 for r in blk if r["label"] == "DIP")))
