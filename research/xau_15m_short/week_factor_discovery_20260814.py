#!/usr/bin/env python3
"""DESCOBERTA de fatores faca-vs-dip na semana XAU (2026-08-10 -> agora) — read-only, RAW-first.
Objetivo: ver QUE fatores discriminam um breakdown genuino (faca) de um dip compravel, nos eventos
onde o guard PODERIA bloquear (cada choch_dn). Rotulo OBJETIVO por resultado forward (nao juizo meu).

CONSUMIR os motores que JA existem (context_structure para choch/estrutura, context_liquidity para
sweeps/FSM/move_class do dossie) — NAO reconstruir reader paralelo. Fonte = store_reader / ficheiros
RAW nativos que a PRODUCAO consome (bars_5m/15m + raw_1h/4h_ohlc). Features CONTINUAS; nao invento
cutoffs — reporto a DISTRIBUICAO por rotulo e deixo a discriminacao emergir. py3.
"""
import sys, json, datetime as dt
from pathlib import Path

ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
import context_structure as CS

MON = int(dt.datetime(2026, 8, 10, 0, 0, tzinfo=dt.timezone.utc).timestamp())

FILES = {
    "4H": ROOT / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl",
    "1H": ROOT / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl",
    "15M": ROOT / "my-strategy/core/bar_store/store/bars_15m.jsonl",
    "5M": ROOT / "my-strategy/core/bar_store/store/bars_5m.jsonl",
}
# horizonte forward por TF (barras) para medir o que o preco FEZ a seguir
HORIZON = {"4H": 6, "1H": 8, "15M": 12, "5M": 18}


def load(f):
    rows = []
    for l in open(f):
        l = l.strip()
        if not l:
            continue
        r = json.loads(l)
        rows.append({
            "t": int(r.get("t")),
            "o": float(r.get("o", r.get("open"))),
            "h": float(r.get("h", r.get("high"))),
            "l": float(r.get("l", r.get("low"))),
            "c": float(r.get("c", r.get("close"))),
        })
    rows.sort(key=lambda x: x["t"])
    return rows


def utc(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%m-%d %H:%M")


def candle_feats(b):
    """Absorcao BIDIRECIONAL geometrica da vela (features continuas, nao rotulos)."""
    rng = max(1e-9, b["h"] - b["l"])
    body_hi = max(b["o"], b["c"])
    body_lo = min(b["o"], b["c"])
    return {
        "close_pos": (b["c"] - b["l"]) / rng,          # 1=fecho no topo, 0=fecho no fundo
        "lower_wick_frac": (body_lo - b["l"]) / rng,    # pavio inferior (absorcao COMPRADORA)
        "upper_wick_frac": (b["h"] - body_hi) / rng,    # pavio superior (absorcao VENDEDORA)
        "body_dir": 1 if b["c"] > b["o"] else -1 if b["c"] < b["o"] else 0,
        "range": rng,
    }


def choch_events(bars):
    """Onsets de choch_dn causais: barra i onde choch.dn passa a True (era False em i-1)."""
    H = [b["h"] for b in bars]; L = [b["l"] for b in bars]; C = [b["c"] for b in bars]
    # pivots UMA vez sobre todo o historico (causal via confirm_bar), reutilizados por barra
    piv_all = CS.fractal_pivots(H, L, m=2)
    ev = []
    prev = False
    for i in range(20, len(bars)):
        if bars[i]["t"] < MON:              # so a semana precisa de veredito (mas prev vem do dia anterior)
            # ainda preciso de prev perto do inicio da semana: computa a partir de ~30 barras antes
            if bars[i]["t"] < MON - 6 * 3600:
                continue
        s = _structure_fast(H, L, C, i, piv_all)
        dn = bool(s["choch"]["dn"])
        if dn and not prev and bars[i]["t"] >= MON:
            ev.append((i, s))
        prev = dn
    return ev


def _structure_fast(H, L, C, i, piv_all, m=2, atr_n=14):
    """Igual a CS.structure mas reutiliza piv_all (pivots pre-computados) — evita O(N^2)."""
    piv = [e for e in piv_all if e[0] <= i]
    highs = [e for e in piv if e[1] == "H"]; lows = [e for e in piv if e[1] == "L"]
    last_high = highs[-1] if highs else None; last_low = lows[-1] if lows else None
    prev_high = highs[-2] if len(highs) >= 2 else None; prev_low = lows[-2] if len(lows) >= 2 else None
    a = CS.atr(H, L, C, i, atr_n)
    prot_low = last_low[3] if last_low else None
    prot_high = last_high[3] if last_high else None
    choch_dn = prot_low is not None and C[i] < prot_low
    choch_up = prot_high is not None and C[i] > prot_high
    return {"i": i, "close": round(C[i], 3), "atr14": round(a, 4) if a else None,
            "swings": {"last_low": {"price": last_low[3]} if last_low else None},
            "choch": {"up": bool(choch_up), "dn": bool(choch_dn)}}


def outcome(bars, i, s, tf):
    """Rotulo OBJETIVO por resultado: dentro do horizonte, reclamou o higher-low rompido (DIP)
    ou fez novo low significativo sem reclamar (FACA)? Mede em ATR. Reporta tambem deslocamento cru."""
    prot = (s["swings"]["last_low"] or {}).get("price")
    a = s["atr14"] or 1e-9
    h = HORIZON[tf]
    fut = bars[i + 1:i + 1 + h]
    if not fut or prot is None:
        return None
    reclaim = any(b["c"] > prot for b in fut)          # fechou de volta acima do HL rompido
    min_low = min(b["l"] for b in fut)
    max_high = max(b["h"] for b in fut)
    fwd_down_atr = (bars[i]["c"] - min_low) / a         # quao fundo foi (MAE p/ baixo)
    fwd_up_atr = (max_high - bars[i]["c"]) / a          # quao alto bounce (MFE p/ cima)
    # rotulo: DIP se reclamou o HL e bounce dominou; FACA se nao reclamou e continuou a cair
    if reclaim and fwd_up_atr >= fwd_down_atr:
        lab = "DIP"
    elif (not reclaim) and fwd_down_atr > fwd_up_atr:
        lab = "FACA"
    else:
        lab = "AMBIG"
    return {"label": lab, "reclaim": reclaim, "down_atr": round(fwd_down_atr, 2),
            "up_atr": round(fwd_up_atr, 2), "prot": prot}


def seq_struct(bars, i, back=40):
    """Sequencia de topos/fundos ate i: lower-highs vs higher-lows (RAW nativo, causal)."""
    seg = bars[max(0, i - back):i + 1]
    H = [b["h"] for b in seg]; L = [b["l"] for b in seg]
    piv = CS.fractal_pivots(H, L, m=2)
    hi = [e[3] for e in piv if e[1] == "H"][-3:]
    lo = [e[3] for e in piv if e[1] == "L"][-3:]
    lh = sum(1 for k in range(1, len(hi)) if hi[k] < hi[k - 1])
    hl = sum(1 for k in range(1, len(lo)) if lo[k] > lo[k - 1])
    ll = sum(1 for k in range(1, len(lo)) if lo[k] < lo[k - 1])
    return {"lower_highs": lh, "higher_lows": hl, "lower_lows": ll}


def run():
    print("=" * 78)
    print("DESCOBERTA faca-vs-dip — semana XAU 2026-08-10 -> agora | eventos = choch_dn (guard-trigger)")
    print("=" * 78)
    agg = {}  # tf -> list of events
    for tf, f in FILES.items():
        if not f.exists():
            print(f"\n[{tf}] ficheiro ausente"); continue
        bars = load(f)
        ev = choch_events(bars)
        rows = []
        for i, s in ev:
            oc = outcome(bars, i, s, tf)
            if not oc:
                continue
            cf = candle_feats(bars[i])
            sq = seq_struct(bars, i)
            rows.append({"t": bars[i]["t"], "i": i, **oc, **cf, **sq})
        agg[tf] = rows
        nf = sum(1 for r in rows if r["label"] == "FACA")
        nd = sum(1 for r in rows if r["label"] == "DIP")
        na = sum(1 for r in rows if r["label"] == "AMBIG")
        print(f"\n[{tf}] {len(rows)} eventos choch_dn na semana | FACA={nf} DIP={nd} AMBIG={na}")
        for r in rows:
            print("   %s | %-5s | down%4.1f up%4.1f reclaim=%-5s | close_pos%.2f loWick%.2f upWick%.2f body%+d | LH%d HL%d LL%d"
                  % (utc(r["t"]), r["label"], r["down_atr"], r["up_atr"], str(r["reclaim"]),
                     r["close_pos"], r["lower_wick_frac"], r["upper_wick_frac"], r["body_dir"],
                     r["lower_highs"], r["higher_lows"], r["lower_lows"]))
    # DISCRIMINACAO agregada: media das features por rotulo (across TFs)
    print("\n" + "=" * 78)
    print("DISCRIMINACAO — media das features por rotulo (todos TFs juntos)")
    print("=" * 78)
    allrows = [r for rows in agg.values() for r in rows]
    for lab in ("FACA", "DIP"):
        g = [r for r in allrows if r["label"] == lab]
        if not g:
            print(f"  {lab}: 0 eventos"); continue
        def m(k): return sum(r[k] for r in g) / len(g)
        print("  %-5s n=%2d | close_pos=%.2f loWick=%.2f upWick=%.2f body=%+.2f | LH=%.2f HL=%.2f LL=%.2f | reclaim%%=%.0f"
              % (lab, len(g), m("close_pos"), m("lower_wick_frac"), m("upper_wick_frac"), m("body_dir"),
                 m("lower_highs"), m("higher_lows"), m("lower_lows"),
                 100 * sum(1 for r in g if r["reclaim"]) / len(g)))
    print("\n(features contínuas — a linha de corte sai da separação faca/dip, NAO inventada. "
          "Liquidez/confluence/OB-tie = passo 2, recomputados de context_liquidity por evento.)")


if __name__ == "__main__":
    run()
