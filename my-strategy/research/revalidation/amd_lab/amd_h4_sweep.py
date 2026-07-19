#!/usr/bin/env python3
"""AMD H4 SWEEP — backtest Fase B (Cris 2026-07-19), RAW CANÓNICO. Reconstrói o modelo AMD dos PDFs:
sweep de liquidez (PDH/PDL/PWH/PWL) numa vela H4 + reclaim no fecho (rejeição) = "Stop Protegido".
Filtro killzone Londres/NY, bias D1. Entrada DIRETA: fecho H4, SL=ponta da wick de manipulação, TP=2R.
Causal close-only (níveis do dia/semana ANTERIOR completo; sinal só em H4 FECHADA; outcome forward SL-first).
Fonte: 4H = blocos 240m gz (dataset_registry) + raw_4h_ohlc tail; 1H idem (para o refino FVG, script B3).
py3.9. __main__ imprime o painel completo (N·WR·sumR·avgR·DD·ret/DD·streak·por-ano) + null."""
import gzip, json, glob, bisect, statistics, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HD = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD")
REV = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
UTC = dt.timezone.utc; LX = ZoneInfo("Europe/Lisbon")
KILL_START_H = {6, 10, 14}          # H4 start-hour UTC nas killzones Londres/NY (bars cobrem 07-18 UTC)
HORIZON = 60                        # barras H4 para resolver (~10 dias)


def _read_gz(paths):
    bars = {}
    for p in paths:
        with gzip.open(p, "rt") as fh:
            for l in fh:
                i = l.find('"ohlcv":')
                if i < 0: continue
                s = l.find('[', i); e = l.find(']', s)
                if s < 0 or e < 0: continue
                try: arr = json.loads(l[s:e+1])
                except Exception: continue
                for b in arr:
                    t = b.get("time")
                    if t is None or b.get("close") is None: continue
                    bars[t] = [b["open"], b["high"], b["low"], b["close"]]   # last-write cura corrida de captura
    return bars


def load_tf(gz_glob, rev_file):
    bars = _read_gz(sorted(glob.glob(str(HD / gz_glob))))
    try:
        for l in (REV / rev_file).read_text().splitlines():
            if not l.strip(): continue
            b = json.loads(l); bars[b["t"]] = [b["o"], b["h"], b["l"], b["c"]]   # REV tail estende/corrige
    except Exception: pass
    T = sorted(bars)
    return [{"t": t, "o": bars[t][0], "h": bars[t][1], "l": bars[t][2], "c": bars[t][3]} for t in T]


def daily_levels(h4):
    """PDH/PDL por dia UTC (reset 00:00 GMT, como o PDF) do dia ANTERIOR completo. Causal."""
    days = {}
    for b in h4:
        d = dt.datetime.fromtimestamp(b["t"], UTC).date()
        x = days.setdefault(d, [b["h"], b["l"]])
        x[0] = max(x[0], b["h"]); x[1] = min(x[1], b["l"])
    return days


def weekly_levels(h4):
    wk = {}
    for b in h4:
        d = dt.datetime.fromtimestamp(b["t"], UTC).date(); iso = d.isocalendar()[:2]
        x = wk.setdefault(iso, [b["h"], b["l"]])
        x[0] = max(x[0], b["h"]); x[1] = min(x[1], b["l"])
    return wk


def signals(h4, use_bias=False):
    days = daily_levels(h4); wk = weekly_levels(h4)
    out = []; last_dir_bar = {"long": -99, "short": -99}
    for i, b in enumerate(h4):
        hu = dt.datetime.fromtimestamp(b["t"], UTC)
        if hu.hour not in KILL_START_H:            # killzone Londres/NY
            continue
        d = hu.date(); pd = d - dt.timedelta(days=1); iso = d.isocalendar()[:2]
        pw = (pd - dt.timedelta(days=pd.weekday() + 1))     # domingo da semana anterior (aprox)
        pdh = days.get(pd, [None, None])[0]; pdl = days.get(pd, [None, None])[1]
        # semana anterior completa
        pwiso = (d - dt.timedelta(days=d.weekday() + 7)).isocalendar()[:2]
        pwh = wk.get(pwiso, [None, None])[0]; pwl = wk.get(pwiso, [None, None])[1]
        lows = [x for x in (pdl, pwl) if x is not None]
        highs = [x for x in (pdh, pwh) if x is not None]
        # LONG: varre um nível abaixo e fecha acima (reclaim)
        for L in lows:
            if b["l"] < L and b["c"] > L and i - last_dir_bar["long"] >= 6:
                sl = b["l"]; ent = b["c"]; R = ent - sl
                if R <= 0: continue
                out.append({"i": i, "t": b["t"], "dir": "long", "level": round(L, 2), "sl": round(sl, 2),
                            "ent": round(ent, 2), "R": round(R, 2), "tgt": round(ent + 2 * R, 2)})
                last_dir_bar["long"] = i; break
        for H in highs:
            if b["h"] > H and b["c"] < H and i - last_dir_bar["short"] >= 6:
                sl = b["h"]; ent = b["c"]; R = sl - ent
                if R <= 0: continue
                out.append({"i": i, "t": b["t"], "dir": "short", "level": round(H, 2), "sl": round(sl, 2),
                            "ent": round(ent, 2), "R": round(R, 2), "tgt": round(ent - 2 * R, 2)})
                last_dir_bar["short"] = i; break
    return out


def resolve(sig, h4):
    """SL-first conservador (se SL e TP na mesma barra -> LOSS). Devolve 'WIN'/'LOSS'/'OPEN' + barras."""
    for k in range(sig["i"] + 1, min(len(h4), sig["i"] + 1 + HORIZON)):
        b = h4[k]
        if sig["dir"] == "long":
            if b["l"] <= sig["sl"]: return "LOSS", k - sig["i"]
            if b["h"] >= sig["tgt"]: return "WIN", k - sig["i"]
        else:
            if b["h"] >= sig["sl"]: return "LOSS", k - sig["i"]
            if b["l"] <= sig["tgt"]: return "WIN", k - sig["i"]
    return "OPEN", None


def panel(res):
    r = [x for x in res if x["outcome"] in ("WIN", "LOSS")]
    n = len(r); w = sum(1 for x in r if x["outcome"] == "WIN")
    Rmults = [2 if x["outcome"] == "WIN" else -1 for x in r]
    cum = 0; peak = 0; dd = 0; streak = 0; mstreak = 0
    for m in Rmults:
        cum += m; peak = max(peak, cum); dd = min(dd, cum - peak)
        streak = streak + 1 if m < 0 else 0; mstreak = max(mstreak, streak)
    summ = sum(Rmults)
    print(f"  N={n} · WR={100*w/max(1,n):.1f}% ({w}W/{n-w}L) · sumR={summ:+d} · avgR={summ/max(1,n):+.2f}"
          f" · maxDD={dd:.0f}R · ret/DD={summ/max(1,abs(dd) or 1):.1f} · maxStreak={mstreak}"
          f" · OPEN={sum(1 for x in res if x['outcome']=='OPEN')}")
    # por-ano
    by = {}
    for x in r:
        y = dt.datetime.fromtimestamp(x["t"], UTC).year; by.setdefault(y, []).append(2 if x["outcome"] == "WIN" else -1)
    print("  por-ano:", " · ".join(f"{y}:{sum(v):+d}R({sum(1 for m in v if m>0)}/{len(v)})" for y, v in sorted(by.items())))


if __name__ == "__main__":
    print("=== carregando RAW canónico 4H ===")
    h4 = load_tf("4H/XAUUSD_240m_replay_*.jsonl.gz", "raw_4h_ohlc.jsonl")
    d0 = dt.datetime.fromtimestamp(h4[0]["t"], UTC).date(); d1 = dt.datetime.fromtimestamp(h4[-1]["t"], UTC).date()
    print(f"  4H: {len(h4)} barras · {d0} -> {d1}")
    sig = signals(h4)
    for s in sig:
        s["outcome"], s["bars"] = resolve(s, h4)
    print(f"=== SINAIS AMD H4 (sweep PDH/PDL/PWH/PWL + reclaim, killzone L/NY) = {len(sig)} ===")
    print("PAINEL (entrada direta H4, SL=wick, TP 2R):")
    panel(sig)
    print("  longs:", sum(1 for s in sig if s["dir"] == "long"), "· shorts:", sum(1 for s in sig if s["dir"] == "short"))
