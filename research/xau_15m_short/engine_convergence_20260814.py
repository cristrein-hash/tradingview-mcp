#!/usr/bin/env python3
"""ENGINE MULTIFATORIAL (convergência) — faca-vs-dip nos LONG-candidatos da semana, lendo TODAS as linhas
de análise JUNTAS dos indicadores REAIS capturados (replay as-of-bar). READ_OB_ZONES: consome OB Detector
real; NÃO re-deriva estrutura. Cada linha = 1 leitor que vota BREAKDOWN (bloquear long) ou DIP (proteger).
A discriminação é testada no SCORE DE CONVERGÊNCIA (nº de linhas que convergem), nunca num fator isolado.

Linhas: Liquidez(context_liquidity) · Bubbles(buy/sell) · Vela · NAS · DMI · RSI · CHOP · OB-localização.
Consome context_liquidity (stateless). Rótulo objetivo forward MFE/MAE. Amostra pequena = hipótese. py3."""
import sys, json, datetime as dt
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
import context_liquidity as CL

CAP15 = ROOT / "alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-08-10_to_2026-08-14.jsonl"
READS = ROOT / "alert-bridge/logs/candle_reads.jsonl"
MON = int(dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc).timestamp())
BUY = {"plot_0", "plot_2", "plot_4"}   # verde (mapeamento Cp validado)
SELL = {"plot_6", "plot_8", "plot_10"}  # vermelho


def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
def fnum(x):
    try: return float(str(x).replace("−", "-").replace(",", ""))
    except Exception: return None


# 1) universo LONG
longs = {}
for l in open(READS):
    if not l.strip(): continue
    r = json.loads(l); bt = r.get("bar_t")
    if bt is None or int(bt) < MON: continue
    if ((r.get("read") or {}).get("direction") or "") == "LONG":
        longs[int(bt)] = r.get("bar") or {}
evt_times = set(longs)

# 2) stream captura, guardar SÓ as linhas dos eventos (memória)
cap = {}      # as-of t -> full row (só eventos)
allbars = []  # série 15M p/ label
for l in open(CAP15):
    if not l.strip(): continue
    r = json.loads(l)
    oh = r.get("ohlcv"); bars = oh.get("bars") if isinstance(oh, dict) else oh
    if not bars: continue
    last = bars[-1]; t = int(last.get("t") or last.get("time"))
    allbars.append((t, float(last["o"] if "o" in last else last["open"]),
                    float(last.get("h", last.get("high"))), float(last.get("l", last.get("low"))),
                    float(last.get("c", last.get("close")))))
    if t in evt_times:
        cap[t] = {"bars": [(int(b.get("t", b.get("time"))), float(b.get("o", b.get("open"))),
                            float(b.get("h", b.get("high"))), float(b.get("l", b.get("low"))),
                            float(b.get("c", b.get("close")))) for b in bars[-500:]],
                  "sv": r.get("study_values"), "pb": r.get("pine_boxes"),
                  "bub": r.get("pine_shapes_bubbles")}
allbars = sorted(set(allbars)); bt_list = [b[0] for b in allbars]


def atr(i, n=14):
    if i < n: return 5.0
    return (sum(max(allbars[k][2]-allbars[k][3], abs(allbars[k][2]-allbars[k-1][4]),
                    abs(allbars[k][3]-allbars[k-1][4])) for k in range(i-n+1, i+1))/n) or 5.0


def outcome(t):
    try: i = bt_list.index(t)
    except ValueError: return None
    a = atr(i); fut = allbars[i+1:i+9]
    if not fut: return None
    c0 = allbars[i][4]
    mae = (c0-min(b[3] for b in fut))/a; mfe = (max(b[2] for b in fut)-c0)/a
    return {"label": "DIP" if mfe >= mae else "FACA", "mfe": round(mfe, 1), "mae": round(mae, 1)}


def sv_get(sv, name_sub):
    st = sv.get("studies", sv) if isinstance(sv, dict) else sv
    for s in st or []:
        if name_sub in s.get("name", ""): return s.get("values") or {}
    return {}


# ---------- LEITORES (cada um vota: +1 breakdown, -1 dip, 0 neutro) ----------
def read_liquidity(bars15):
    try: liq = CL.compute([{"t": b[0], "o": b[1], "h": b[2], "l": b[3], "c": b[4]} for b in bars15]) or {}
    except Exception: return 0, {}
    seq = liq.get("sequence") or {}; hi = seq.get("high") or {}; lo = seq.get("low") or {}
    v = 0
    if liq.get("direction") == "down" and hi.get("state") == "FAILED" and hi.get("trapped") == "buyers": v += 1
    if lo.get("state") == "RECLAIMED" and lo.get("trapped") == "shorts": v -= 1   # long protegido
    return v, {"dir": liq.get("direction"), "hi": hi.get("state"), "lo": lo.get("state")}


def read_bubbles(bub):
    st = bub if isinstance(bub, list) else (bub.get("studies") if isinstance(bub, dict) else [])
    for s in st or []:
        if "Bubbles" in s.get("name", ""):
            ap = s.get("activations_per_plot") or {}
            bw = sum(v for k, v in ap.items() if k in BUY); sw = sum(v for k, v in ap.items() if k in SELL)
            if sw > bw: return 1, {"buy": bw, "sell": sw}
            if bw > sw: return -1, {"buy": bw, "sell": sw}
    return 0, {}


def read_candle(bar):
    o, h, l, c = bar.get("o"), bar.get("h"), bar.get("l"), bar.get("c")
    if None in (o, h, l, c): return 0, {}
    rng = max(1e-9, h-l); cp = (c-l)/rng; low_w = (min(o, c)-l)/rng
    if low_w >= 0.4: return -1, {"cp": round(cp, 2), "loW": round(low_w, 2)}   # absorção compradora = dip
    if cp <= 0.35: return 1, {"cp": round(cp, 2), "loW": round(low_w, 2)}      # fecho no fundo = breakdown
    return 0, {"cp": round(cp, 2), "loW": round(low_w, 2)}


def read_nas(sv):
    v = sv_get(sv, "NAS")
    if fnum(v.get("NAS_TOP_SIGNAL")): return 1, {"nas": "TOP"}
    if fnum(v.get("NAS_BOTTOM_SIGNAL")): return -1, {"nas": "BOT"}
    return 0, {}


def read_dmi(sv):
    v = sv_get(sv, "Directional")
    p, m = fnum(v.get("+DI")), fnum(v.get("-DI"))
    if p is not None and m is not None:
        if m > p: return 1, {"+DI": p, "-DI": m}
        if p > m: return -1, {"+DI": p, "-DI": m}
    return 0, {}


def read_rsi(sv):
    v = sv_get(sv, "Relative Strength"); r = fnum(v.get("RSI"))
    if r is None: return 0, {}
    if r <= 35: return -1, {"rsi": r}   # oversold → bounce/dip
    if r >= 65: return 1, {"rsi": r}
    return 0, {"rsi": r}


# ---------- SÍNTESE por evento ----------
rows = []
for t, bar in sorted(longs.items()):
    oc = outcome(t)
    if not oc or t not in cap: continue
    c = cap[t]
    votes = {}
    # FIX: a liquidez precisa do HISTÓRICO real (~480 barras), não das 5 do ohlcv truncado da captura.
    i = bt_list.index(t)
    votes["liq"], liq_d = read_liquidity(allbars[max(0, i-480):i+1])
    votes["bub"], _ = read_bubbles(c["bub"])
    votes["candle"], cd = read_candle(bar)
    votes["nas"], _ = read_nas(c["sv"])
    votes["dmi"], _ = read_dmi(c["sv"])
    votes["rsi"], _ = read_rsi(c["sv"])
    breakdown = sum(1 for v in votes.values() if v > 0)
    dip = sum(1 for v in votes.values() if v < 0)
    net = breakdown - dip
    rows.append({"t": t, **oc, "brk": breakdown, "dip": dip, "net": net, "votes": votes, "cd": cd})

print(f"eventos: {len(rows)}  (linhas: liq/bub/candle/nas/dmi/rsi)")
print("="*104)
for r in rows:
    vv = " ".join("%s%+d" % (k, v) for k, v in r["votes"].items() if v)
    print("%s | %-4s mfe%4.1f mae%4.1f | BRK=%d DIP=%d net=%+d | %s"
          % (utc(r["t"]), r["label"], r["mfe"], r["mae"], r["brk"], r["dip"], r["net"], vv))

print("\n" + "="*104)
print("DISCRIMINAÇÃO pela CONVERGÊNCIA (net = breakdown_votes - dip_votes)")
print("="*104)
import statistics as st
for lab in ("FACA", "DIP"):
    g = [r for r in rows if r["label"] == lab]
    if not g: continue
    nets = [r["net"] for r in g]
    print("%s n=%2d | net média %+.2f  mediana %+.0f | net>=+2: %d/%d (%.0f%%)"
          % (lab, len(g), st.mean(nets), st.median(nets),
             sum(1 for x in nets if x >= 2), len(g), 100*sum(1 for x in nets if x >= 2)/len(g)))
# tabela de bloqueio por limiar de convergência
print("\nSe BLOQUEAR quando net>=N (convergência de linhas):")
for N in (1, 2, 3):
    blk = [r for r in rows if r["net"] >= N]
    fac = sum(1 for r in blk if r["label"] == "FACA"); dp = sum(1 for r in blk if r["label"] == "DIP")
    tot_fac = sum(1 for r in rows if r["label"] == "FACA")
    print("  net>=%d: bloqueia %2d (apanha %d/%d FACAs, mata %d DIPs)" % (N, len(blk), fac, tot_fac, dp))
print("\n(convergência lida de TODAS as linhas juntas; amostra pequena = hipótese, não prova.)")
