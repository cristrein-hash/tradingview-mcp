#!/usr/bin/env python3
"""AMD B3 — refino 1H FVG retestado (Cris 2026-07-19): para cada sinal AMD H4 (amd_h4_sweep.signals),
desce ao RAW 1H canónico e procura um FVG/imbalance na perna de manipulação. Entra no RETESTE do FVG
(entrada mais perto do extremo => SL MENOR => o mesmo 2R exige distância menor). Compara com a entrada
direta H4. Causal close-only (FVG só de barras fechadas; reteste só DEPOIS do FVG formar; outcome forward).
Cobertura 1H = ~2 anos (2024-05->2026-05 + REV tail). py3.9.
FVG bullish (long): bar[k-2].high < bar[k].low (gap) => zona [bar[k-2].high, bar[k].low]. Reteste = 1H
posterior cujo low <= topo do FVG. Entry = topo do FVG. SL = low da manipulação (wick). TP = entry+2R."""
import sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import amd_h4_sweep as A
UTC = dt.timezone.utc
FVG_WAIT_H1 = 16        # janela 1H p/ formar FVG + retestar após o sinal (16h ~ 4 velas H4)
HORIZON_1H = 240        # barras 1H p/ resolver (~10 dias)


def _slice(bars1h, t0, t1):
    return [b for b in bars1h if t0 <= b["t"] < t1]


def refine_long(sig, h1):
    """FVG bull retestado -> SL APERTADO no bordo do FVG (gap_bot), NÃO na wick (o 'SL menor' do Cris).
    Causal: FVG de barras fechadas (k-2,k), reteste em m>k, SL=gap_bot (barra k-2, passada). Sem swing futuro."""
    t = sig["t"]; win = _slice(h1, t, t + FVG_WAIT_H1 * 3600)
    if len(win) < 4:
        return None
    for k in range(2, len(win)):
        gap_top = win[k]["l"]; gap_bot = win[k - 2]["h"]     # FVG bull = [gap_bot, gap_top]
        R = gap_top - gap_bot
        if R <= 0:
            continue
        for m in range(k + 1, len(win)):                     # 1º reteste que entra no FVG
            if win[m]["l"] <= gap_top:
                return {"ent": round(gap_top, 2), "sl": round(gap_bot, 2), "R": round(R, 2),
                        "tgt": round(gap_top + 2 * R, 2), "entry_t": win[m]["t"]}
    return None


def refine_short(sig, h1):
    t = sig["t"]; win = _slice(h1, t, t + FVG_WAIT_H1 * 3600)
    if len(win) < 4:
        return None
    for k in range(2, len(win)):
        gap_bot = win[k]["h"]; gap_top = win[k - 2]["l"]     # FVG bear = [gap_bot, gap_top]
        R = gap_top - gap_bot
        if R <= 0:
            continue
        for m in range(k + 1, len(win)):
            if win[m]["h"] >= gap_bot:
                return {"ent": round(gap_bot, 2), "sl": round(gap_top, 2), "R": round(R, 2),
                        "tgt": round(gap_bot - 2 * R, 2), "entry_t": win[m]["t"]}
    return None


def resolve_1h(direction, ent, sl, tgt, entry_t, h1):
    i = next((k for k, b in enumerate(h1) if b["t"] >= entry_t), None)
    if i is None:
        return "OPEN", None
    for k in range(i + 1, min(len(h1), i + 1 + HORIZON_1H)):
        b = h1[k]
        if direction == "long":
            if b["l"] <= sl: return "LOSS", k - i
            if b["h"] >= tgt: return "WIN", k - i
        else:
            if b["h"] >= sl: return "LOSS", k - i
            if b["l"] <= tgt: return "WIN", k - i
    return "OPEN", None


if __name__ == "__main__":
    print("=== carrega 4H (sinais) + 1H canónico (refino) ===")
    h4 = A.load_tf("4H/XAUUSD_240m_replay_*.jsonl.gz", "raw_4h_ohlc.jsonl")
    h1 = A.load_tf("1H/XAUUSD_60m_replay_*.jsonl.gz", "raw_1h_ohlc.jsonl")
    d0 = dt.datetime.fromtimestamp(h1[0]["t"], UTC).date(); d1 = dt.datetime.fromtimestamp(h1[-1]["t"], UTC).date()
    print(f"  1H: {len(h1)} barras · {d0} -> {d1}")
    sig = A.signals(h4)
    t1h_min = h1[0]["t"]; t1h_max = h1[-1]["t"]
    sig = [s for s in sig if t1h_min <= s["t"] <= t1h_max - FVG_WAIT_H1 * 3600]   # só sinais na janela 1H
    print(f"=== sinais H4 dentro da cobertura 1H: {len(sig)} ===")

    direct = []; refined = []; no_entry = 0
    r_direct_sum = 0.0; r_ref_sum = 0.0
    for s in sig:
        # entrada DIRETA (resolvida no 1H p/ comparação justa)
        od, _ = resolve_1h(s["dir"], s["ent"], s["sl"], s["tgt"], s["t"] + 4 * 3600, h1)
        direct.append({**s, "outcome": od})
        # entrada REFINADA FVG
        ref = (refine_long if s["dir"] == "long" else refine_short)(s, h1)
        if not ref:
            no_entry += 1; continue
        orf, _ = resolve_1h(s["dir"], ref["ent"], ref["sl"], ref["tgt"], ref["entry_t"], h1)
        refined.append({**s, **ref, "outcome": orf})
        # média das distâncias de SL (R em $) p/ mostrar "SL menor"
        r_direct_sum += s["R"]; r_ref_sum += ref["R"]

    def pan(res, label):
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
        print("       por-ano:", " · ".join(f"{y}:{sum(v):+d}R" for y, v in sorted(by.items())))

    print("\n== COMPARAÇÃO (mesma janela 1H) ==")
    pan(direct, "DIRETA H4 (SL=wick)")
    pan(refined, f"REFINADA FVG-1H (SL menor) · {no_entry} sinais sem FVG retestado")
    nref = len(refined)
    if nref:
        print(f"\n  SL médio DIRETA: {r_direct_sum/max(1,nref):.2f}$ · SL médio REFINADA: {r_ref_sum/max(1,nref):.2f}$ "
              f"(reducão {100*(1-r_ref_sum/max(1e-9,r_direct_sum)):.0f}%) — sobre os {nref} sinais com FVG")
