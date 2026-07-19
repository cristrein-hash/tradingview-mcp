#!/usr/bin/env python3
"""AMD v2 — reconstrução CORRIGIDA (Cris 2026-07-19, após auditoria das próprias medições). Corrige os
4 erros da v1: (1) nível varre-se UMA vez (não re-sinaliza); (2) sweep com REJEIÇÃO decisiva (fecho na
metade oposta do range, não dip incidental); (3) SL abaixo do ORDER BLOCK 1H que está por baixo do FVG
(estrutura), não no bordo do FVG nem na wick; (4) FILTRO de tendência D1. Entry = FVG 1H retestado.
Causal close-only, RAW canónico. py3.9. Audita e imprime painel + trace de exemplos."""
import sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import amd_h4_sweep as A
UTC = dt.timezone.utc; LX = ZoneInfo("Europe/Lisbon")
KILL = {6, 10, 14}              # H4 open-hour UTC = killzones Londres/NY (auditado: bares em 2/6/10/14/18/22)
FVG_WAIT_H1 = 16
HORIZON_1H = 240
REJ = 0.5                       # fecho na metade oposta do range (rejeição real, não dip incidental)
OB_BUF = 0.15                   # buffer abaixo do OB (fração do ATR-ish; aqui em fração do R do FVG)


def daily_series(h4):
    """Fecho diário (última barra do dia UTC) — para bias D1 causal."""
    dd = {}
    for b in h4:
        d = dt.datetime.fromtimestamp(b["t"], UTC).date(); dd[d] = b["c"]     # último close do dia
    ds = sorted(dd)
    return ds, dd


def ema(vals, n):
    k = 2 / (n + 1); out = []; e = None
    for v in vals:
        e = v if e is None else v * k + e * (1 - k); out.append(e)
    return out


def bias_map(h4, n=20):
    """bias por DIA: 'up' se close_dia > EMA20(closes diários) até ONTEM; senão 'down'. Causal (usa só dias<=d-1)."""
    ds, dd = daily_series(h4)
    closes = [dd[d] for d in ds]; e = ema(closes, n)
    bm = {}
    for i, d in enumerate(ds):
        if i < n: bm[d] = None; continue
        bm[d] = "up" if closes[i] > e[i] else "down"     # bias do dia d (conhecido no fecho de d)
    return bm, ds


def signals_v2(h4, use_bias=True):
    days = A.daily_levels(h4); wk = A.weekly_levels(h4)
    bm, ds = bias_map(h4)
    used = set(); out = []
    for i, b in enumerate(h4):
        hu = dt.datetime.fromtimestamp(b["t"], UTC)
        if hu.hour not in KILL: continue
        d = hu.date(); rng = b["h"] - b["l"]
        if rng <= 0: continue
        pd_ = d - dt.timedelta(days=1)
        pwiso = (d - dt.timedelta(days=d.weekday() + 7)).isocalendar()[:2]
        pdh, pdl = days.get(pd_, [None, None]); pwh, pwl = wk.get(pwiso, [None, None])
        # bias do dia ANTERIOR (causal — conhecido antes do dia d)
        bias = bm.get(pd_)
        close_pos = (b["c"] - b["l"]) / rng                 # 0=fecho no low, 1=fecho no high
        # LONG: varre nível abaixo, fecha ACIMA com rejeição (close na metade de cima)
        for L in [x for x in (pdl, pwl) if x is not None]:
            key = ("L", round(L, 2))
            if key in used: continue
            if b["l"] < L and b["c"] > L and close_pos >= REJ:
                if use_bias and bias == "down": used.add(key); continue   # contra-tendência: descarta (mas gasta o nível)
                out.append({"i": i, "t": b["t"], "dir": "long", "level": round(L, 2), "bias": bias,
                            "wick": round(b["l"], 2), "h4c": round(b["c"], 2), "close_pos": round(close_pos, 2)})
                used.add(key); break
        for H in [x for x in (pdh, pwh) if x is not None]:
            key = ("H", round(H, 2))
            if key in used: continue
            if b["h"] > H and b["c"] < H and (1 - close_pos) >= REJ:
                if use_bias and bias == "up": used.add(key); continue
                out.append({"i": i, "t": b["t"], "dir": "short", "level": round(H, 2), "bias": bias,
                            "wick": round(b["h"], 2), "h4c": round(b["c"], 2), "close_pos": round(close_pos, 2)})
                used.add(key); break
    return out


def _slice(h1, t0, t1): return [x for x in h1 if t0 <= x["t"] < t1]


def entry_fvg_ob(sig, h1):
    """Entry = FVG 1H retestado. SL = ABAIXO do Order Block 1H (última vela de baixa antes do impulso que
    criou o FVG) que está por baixo do FVG. Causal. Devolve dict ou None."""
    t = sig["t"]; win = _slice(h1, t, t + FVG_WAIT_H1 * 3600)
    if len(win) < 4: return None
    long = sig["dir"] == "long"
    for k in range(2, len(win)):
        if long:
            gap_top = win[k]["l"]; gap_bot = win[k - 2]["h"]
        else:
            gap_bot = win[k]["h"]; gap_top = win[k - 2]["l"]
        if gap_top <= gap_bot: continue                      # sem FVG
        # ORDER BLOCK: última vela OPOSTA (long->vela de baixa / short->vela de alta) em [.. , k-2]
        ob = None
        for j in range(k - 2, max(-1, k - 2 - 12), -1):
            down = win[j]["c"] < win[j]["o"]
            if (long and down) or ((not long) and (not down)):
                ob = win[j]; break
        if ob is None: continue
        R_ = (ob["h"] - gap_bot) if long else (gap_top - ob["l"])   # placeholder recalc abaixo
        for m in range(k + 1, len(win)):                     # reteste do FVG
            hit = (win[m]["l"] <= gap_top) if long else (win[m]["h"] >= gap_bot)
            if hit:
                if long:
                    ent = gap_top; sl = ob["l"] - OB_BUF * (gap_top - gap_bot)   # abaixo do OB
                    R = ent - sl
                    if R <= 0: return None
                    return {"ent": round(ent, 2), "sl": round(sl, 2), "R": round(R, 2),
                            "tgt": round(ent + 2 * R, 2), "entry_t": win[m]["t"], "ob_low": round(ob["l"], 2)}
                else:
                    ent = gap_bot; sl = ob["h"] + OB_BUF * (gap_top - gap_bot)
                    R = sl - ent
                    if R <= 0: return None
                    return {"ent": round(ent, 2), "sl": round(sl, 2), "R": round(R, 2),
                            "tgt": round(ent - 2 * R, 2), "entry_t": win[m]["t"], "ob_high": round(ob["h"], 2)}
    return None


def list_candidates(sig, h1):
    """LISTA todos os FVG/OB candidatos no 1H da janela do setup (NÃO escolhe um — material para o Cris
    decidir). RETESTED + FORMED_UNTESTED. SL abaixo/acima do OB. Causal. Usado pela F2 live (Ping-2)."""
    t = sig["t"]; win = _slice(h1, t, t + FVG_WAIT_H1 * 3600)
    if len(win) < 4: return []
    long = sig["dir"] == "long"; sid = sig.get("setup_id", "?"); out = []
    for k in range(2, len(win)):
        if long: gap_top = win[k]["l"]; gap_bot = win[k - 2]["h"]
        else: gap_bot = win[k]["h"]; gap_top = win[k - 2]["l"]
        if gap_top <= gap_bot: continue
        ob = None
        for j in range(k - 2, max(-1, k - 2 - 12), -1):
            down = win[j]["c"] < win[j]["o"]
            if (long and down) or ((not long) and (not down)): ob = win[j]; break
        if ob is None: continue
        retest_t = None
        for m in range(k + 1, len(win)):
            hit = (win[m]["l"] <= gap_top) if long else (win[m]["h"] >= gap_bot)
            if hit: retest_t = win[m]["t"]; break
        if long:
            ent = gap_top; sl = ob["l"] - OB_BUF * (gap_top - gap_bot); R = ent - sl; tgt = ent + 2 * R
        else:
            ent = gap_bot; sl = ob["h"] + OB_BUF * (gap_top - gap_bot); R = sl - ent; tgt = ent - 2 * R
        if R <= 0: continue
        out.append({"candidate_id": f"{sid}#fvg_{gap_bot:.2f}_{gap_top:.2f}",
                    "fvg": [round(gap_bot, 2), round(gap_top, 2)], "ob_edge": round(ob["l"] if long else ob["h"], 2),
                    "ent": round(ent, 2), "sl": round(sl, 2), "R": round(R, 2), "tgt": round(tgt, 2),
                    "status": "RETESTED" if retest_t else "FORMED", "retest_t": retest_t})
    return out


def resolve_1h(direction, ent, sl, tgt, entry_t, h1):
    i = next((k for k, b in enumerate(h1) if b["t"] >= entry_t), None)
    if i is None: return "OPEN", None
    for k in range(i + 1, min(len(h1), i + 1 + HORIZON_1H)):
        b = h1[k]
        if direction == "long":
            if b["l"] <= sl: return "LOSS", k - i
            if b["h"] >= tgt: return "WIN", k - i
        else:
            if b["h"] >= sl: return "LOSS", k - i
            if b["l"] <= tgt: return "WIN", k - i
    return "OPEN", None


def panel(res, label):
    r = [x for x in res if x["outcome"] in ("WIN", "LOSS")]
    n = len(r); w = sum(1 for x in r if x["outcome"] == "WIN")
    Rm = [2 if x["outcome"] == "WIN" else -1 for x in r]
    cum = pk = ddv = st = mst = 0
    for m in Rm:
        cum += m; pk = max(pk, cum); ddv = min(ddv, cum - pk); st = st + 1 if m < 0 else 0; mst = max(mst, st)
    by = {}
    for x in r:
        y = dt.datetime.fromtimestamp(x["t"], UTC).year; by.setdefault(y, []).append(2 if x["outcome"] == "WIN" else -1)
    print(f"  [{label}] N={n} · WR={100*w/max(1,n):.1f}% ({w}W/{n-w}L) · sumR={sum(Rm):+d} · avgR={sum(Rm)/max(1,n):+.2f}"
          f" · maxDD={ddv:.0f}R · ret/DD={sum(Rm)/max(1,abs(ddv) or 1):.1f} · streak={mst} · OPEN={sum(1 for x in res if x['outcome']=='OPEN')}")
    print("       por-ano:", " · ".join(f"{y}:{sum(v):+d}R({sum(1 for m in v if m>0)}/{len(v)})" for y, v in sorted(by.items())))


if __name__ == "__main__":
    h4 = A.load_tf("4H/XAUUSD_240m_replay_*.jsonl.gz", "raw_4h_ohlc.jsonl")
    h1 = A.load_tf("1H/XAUUSD_60m_replay_*.jsonl.gz", "raw_1h_ohlc.jsonl")
    print(f"4H {len(h4)} · 1H {len(h1)} ({dt.datetime.fromtimestamp(h1[0]['t'],UTC).date()}->{dt.datetime.fromtimestamp(h1[-1]['t'],UTC).date()})")
    sig = signals_v2(h4, use_bias=True)
    t0, t1 = h1[0]["t"], h1[-1]["t"] - FVG_WAIT_H1 * 3600
    sig1h = [s for s in sig if t0 <= s["t"] <= t1]
    print(f"sinais v2 (once-per-level + rejeição + bias): total {len(sig)} · na janela 1H {len(sig1h)} "
          f"(long {sum(1 for s in sig1h if s['dir']=='long')}/short {sum(1 for s in sig1h if s['dir']=='short')})")
    ent = []; noent = 0
    for s in sig1h:
        e = entry_fvg_ob(s, h1)
        if not e: noent += 1; continue
        oc, _ = resolve_1h(s["dir"], e["ent"], e["sl"], e["tgt"], e["entry_t"], h1)
        ent.append({**s, **e, "outcome": oc})
    print(f"com FVG+OB entry: {len(ent)} · sem setup: {noent}")
    print("\n== PAINEL v2 (FVG entry + SL abaixo do OB 1H + bias D1) ==")
    panel(ent, "AMD v2")
    print("\n== TRACE (5 exemplos p/ auditoria) ==")
    for x in ent[:5]:
        print(f"  {x['dir']} {dt.datetime.fromtimestamp(x['t'],UTC).strftime('%Y-%m-%d %H:%M')} bias={x['bias']} "
              f"nivel={x['level']} | ent={x['ent']} SL={x['sl']} ({'OBlow '+str(x.get('ob_low')) if x['dir']=='long' else 'OBhigh '+str(x.get('ob_high'))}) "
              f"R={x['R']} tgt={x['tgt']} -> {x['outcome']}")
