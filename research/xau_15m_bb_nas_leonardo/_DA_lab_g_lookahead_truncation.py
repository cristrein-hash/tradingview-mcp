#!/usr/bin/env python3
"""DA LAB G — ATAQUE 1: look-ahead empírico por TRUNCAMENTO.
Para uma amostra estratificada de candidatos, recomputa TODAS as features g_* novas
e os campos do builder usados por sysA/sysB (reclaim_atr, above_ema21, reclaim_ema_bars)
usando SOMENTE s[:cj+1] (barras <= cj). Se algum valor divergir do armazenado no jsonl,
há look-ahead ou não-determinismo. Também rebuilda o regime v5h com o universo de barras
truncado em t<=cj_t e compara com g_v5h armazenado.
Nada é escrito fora de stdout. Seed-free (determinístico).
"""
import json, bisect, datetime as dt, statistics as st
from pathlib import Path

HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in sorted((HERE / "primitives").glob("*.primitives.json"))}
PRIMK = {k[:10]: v for k, v in PRIM.items()}
U = sorted([json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")], key=lambda r: r["cj_t"])

def ema_at(arr, i, n):
    c = arr[max(0, i - 3 * n):i + 1]; k = 2 / (n + 1); e = c[0]
    for v in c[1:]: e = v * k + e * (1 - k)
    return e

def ema_win(vals, n):
    if not vals: return None
    k = 2 / (n + 1); e = vals[0]
    for v in vals[1:]: e = v * k + e * (1 - k)
    return e

def local_lows(L, upto):
    out = []
    for q in range(2, upto - 2):
        if L[q] == min(L[q - 2:q + 3]): out.append(q)
    return out

# ---------- Parte A: features 15m recomputadas em série TRUNCADA s[:cj+1] ----------
def recompute_features_truncated(r):
    s_full = PRIMK[r["block"]]["series"]
    tmap = {b["t"]: i for i, b in enumerate(s_full)}
    p, cj = tmap[r["t"]], tmap[r["cj_t"]]
    s = s_full[:cj + 1]                     # TRUNCADO: nada depois do bar de entrada
    L = [b["l"] for b in s]; H = [b["h"] for b in s]; C = [b["c"] for b in s]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry = s[cj]["c"]
    out = {}
    lows_prev = [q for q in local_lows(L, p) if p - 96 <= q <= p - 3]
    rsi_p = s[p].get("rsi") or 50
    out["g_rsi_div"] = 0
    if lows_prev:
        q = lows_prev[-1]
        rq = s[q].get("rsi") or 50
        if L[p] < L[q] and rsi_p > rq + 2: out["g_rsi_div"] = 1
    win = [x["atr"] for x in s[max(0, p - 96):p] if x.get("atr")]
    med = sorted(win)[len(win) // 2] if win else atr
    out["g_atr_spike"] = round(atr / med, 2) if med else 1.0
    out["g_sweep_depth"] = round((L[lows_prev[-1]] - L[p]) / atr, 2) if lows_prev else 0.0
    for W in (96, 480):
        lo = min(L[max(0, cj - W):cj + 1]); hi = max(H[max(0, cj - W):cj + 1])
        out[f"g_box{W}"] = round((entry - lo) / ((hi - lo) or atr), 3)
    out["g_rec_speed"] = round((entry - L[p]) / atr / max(1, cj - p), 2)
    run = 0
    for k in range(p, max(0, p - 20), -1):
        if C[k] < C[k - 1]: run += 1
        else: break
    out["g_downrun"] = run
    e21 = ema_at(C, cj, 21); e50 = ema_at(C, cj, 50)
    out["g_ema21_dist"] = round((entry - e21) / atr, 2)
    out["g_ema50_dist"] = round((entry - e50) / atr, 2)
    rng = H[p] - L[p]
    out["g_flush_wick"] = round((min(s[p]["o"], C[p]) - L[p]) / rng, 2) if rng > 0 else 0
    out["g_cj_body"] = round((C[cj] - s[cj]["o"]) / atr, 2)
    # builder fields (lab_entry_candidates.py) recomputados truncados
    lo_p = s[p]["l"]
    out["reclaim_atr"] = round((entry - lo_p) / atr, 2)
    e21b = ema_win([b["c"] for b in s[max(0, cj - 60):cj + 1]], 21)
    out["above_ema21"] = 1 if (e21b and entry > e21b) else 0
    reb = 99
    for x in range(p, cj + 1):
        ee = ema_win([b["c"] for b in s[max(0, x - 60):x + 1]], 21)
        if ee and s[x]["c"] > ee: reb = x - p; break
    out["reclaim_ema_bars"] = reb
    out["up_closes_pc"] = sum(1 for x in range(p + 1, cj + 1) if s[x]["c"] > s[x]["o"])
    seg = [x["c"] for x in s[max(0, p - 20):p + 1]]
    net = abs(seg[-1] - seg[0]); pth = sum(abs(seg[x] - seg[x - 1]) for x in range(1, len(seg)))
    out["downleg_eff"] = round(net / pth, 2) if pth > 0 else .5
    return out

# ---------- Parte B: regime v5h rebuildado com bars t<=cj_t ----------
def regime_truncated(cjt):
    bars = {}
    for pr in PRIM.values():
        for b in pr["series"]:
            if b["t"] <= cjt: bars.setdefault(b["t"], b)
    T15 = sorted(bars)
    Hh = {}
    for t in T15:
        b = bars[t]; hk = t // 3600
        g = Hh.setdefault(hk, {"c": b["c"], "h": b["h"]}); g["h"] = max(g["h"], b["h"]); g["c"] = b["c"]
    HK = sorted(Hh); HC = [Hh[k]["c"] for k in HK]; HH = [Hh[k]["h"] for k in HK]
    days = {}
    for t in T15:
        b = bars[t]; k = t // 86400
        g = days.setdefault(k, {"h": b["h"], "l": b["l"], "c": b["c"]})
        g["h"] = max(g["h"], b["h"]); g["l"] = min(g["l"], b["l"]); g["c"] = b["c"]
    DK = sorted(days); DC = [days[k]["c"] for k in DK]; DH = [days[k]["h"] for k in DK]; DL = [days[k]["l"] for k in DK]
    TR = [0.0]
    for i in range(1, len(DK)): TR.append(max(DH[i] - DL[i], abs(DH[i] - DC[i - 1]), abs(DL[i] - DC[i - 1])))
    def atrd(i, n=14): a = TR[max(1, i - n + 1):i + 1]; return sum(a) / len(a) if a else 1.0
    E50 = [ema_at(DC, i, 50) for i in range(len(DK))]; E100 = [ema_at(DC, i, 100) for i in range(len(DK))]
    N, eff_thr, slope_thr, R_thr, K, Kbear = 15, 0.30, 0.20, 2.0, 5, 5
    def raw_stable(i):
        if i < max(2 * N, 40): return "RANGE"
        a = atrd(i) or 1.0; slope = (E50[i] - E50[i - 5]) / a
        seg = DC[i - N:i + 1]; net = seg[-1] - seg[0]; path = sum(abs(seg[j] - seg[j - 1]) for j in range(1, len(seg))); eff = abs(net) / path if path > 0 else 0
        hh = max(DH[i - N:i]); ll = min(DL[i - N:i]); pos = (DC[i] - ll) / (hh - ll) if hh > ll else .5; s100 = (E100[i] - E100[i - 10]) / a
        tu = eff >= eff_thr and slope > slope_thr; td = eff >= eff_thr and slope < -slope_thr
        sb = E50[i] > E100[i] and s100 > 0; se = E50[i] < E100[i] and s100 < 0
        cont = eff < eff_thr and 0.15 <= pos <= 0.85 and abs(slope) < slope_thr
        peak = max(DH[i - 30:i + 1]); retreat = (peak - DC[i]) / a; lh = max(DH[i - N:i]) < max(DH[i - 2 * N:i - N]); bef = DC[i] < E50[i] and (E50[i] - E50[i - 5]) < 0; bl = DC[i] < min(DL[i - N:i - 2])
        if (bl and bef) or (retreat >= R_thr and lh and bef) or td or (se and pos < 0.6 and not cont): return "BEAR"
        if tu or (sb and pos > 0.55 and not cont): return "BULL"
        return "RANGE"
    rawS = [raw_stable(i) for i in range(len(DK))]
    stable = []; cur = "RANGE"; pend = None; pn = 0
    for v in rawS:
        if v == cur: pend = None; pn = 0
        elif v == pend: pn += 1
        else: pend = v; pn = 1
        need = Kbear if pend == "BEAR" else K
        if pn >= need: cur = pend; pend = None; pn = 0
        stable.append(cur)
    P, mom, dd_intra, Krec_h = 48, 24, 0.06, 120
    ov_hour = []; ov = False; quiet = 0
    for j in range(len(HK)):
        if j < max(P, mom): ov_hour.append(False); continue
        peak = max(HH[j - P:j + 1]); ddp = (peak - HC[j]) / peak if peak > 0 else 0
        fired = ddp >= dd_intra and HC[j] < HC[j - mom]
        if fired: ov = True; quiet = 0
        elif ov:
            quiet += 1
            if quiet >= Krec_h: ov = False
        ov_hour.append(ov)
    dk_today = cjt // 86400
    di = bisect.bisect_left(DK, dk_today) - 1
    stt = "RANGE" if di < 0 else stable[di]
    hi = bisect.bisect_right(HK, (cjt // 3600) - 1) - 1
    ovr = ov_hour[hi] if hi >= 0 else False
    return "BEAR" if (ovr or stt == "BEAR") else stt

if __name__ == "__main__":
    import random
    rng = random.Random(20260703)
    # amostra: todos os candidatos de sysA (críticos) + 60 estratificados por regime/ano
    def fv(r, k, d=0):
        v = r.get(k)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
    def sysA(r):
        return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
                and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
                and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
                and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
                and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
                and r["g_knife"] == 0)
    A = [r for r in U if sysA(r)]
    strat = []
    for reg in ("RANGE", "BULL", "BEAR"):
        for y in (2024, 2025, 2026):
            sub = [r for r in U if r["g_v5h"] == reg and r["yr"] == y]
            if sub: strat += rng.sample(sub, min(7, len(sub)))
    sample = {id(r): r for r in A + strat}.values()
    KEYS = ["g_rsi_div", "g_atr_spike", "g_sweep_depth", "g_box96", "g_box480", "g_rec_speed",
            "g_downrun", "g_ema21_dist", "g_ema50_dist", "g_flush_wick", "g_cj_body",
            "reclaim_atr", "above_ema21", "reclaim_ema_bars", "up_closes_pc", "downleg_eff"]
    mism = 0; checked = 0
    for r in sample:
        rec = recompute_features_truncated(r)
        for k in KEYS:
            checked += 1
            a, b = rec[k], r.get(k)
            if isinstance(a, float) or isinstance(b, float):
                ok = abs((a or 0) - (b or 0)) < 1e-9
            else:
                ok = a == b
            if not ok:
                mism += 1
                print(f"MISMATCH {k}: recomputed(truncated)={a} stored={b} @ {r['block']} cj_t={r['cj_t']}")
    print(f"PARTE A (features truncadas em cj): {len(list(sample))} candidatos x {len(KEYS)} campos = {checked} checks · mismatches = {mism}")

    # Parte B: regime truncado — subset (custo alto): 8 picks de A + 12 estratificados
    sub = list(A[::7])[:8] + list(strat[::5])[:12]
    bad = 0
    for r in sub:
        rt = regime_truncated(r["cj_t"])
        ok = rt == r["g_v5h"]
        if not ok:
            bad += 1
            print(f"REGIME MISMATCH: truncated={rt} stored={r['g_v5h']} @ cj_t={r['cj_t']} ({dt.datetime.utcfromtimestamp(r['cj_t'])})")
    print(f"PARTE B (regime v5h com barras t<=cj_t): {len(sub)} checks · mismatches = {bad}")
