#!/usr/bin/env python3
"""XAU 15M BB+NAS — STAGE-B: DETECTOR CAUSAL DE CANDIDATOS (sem backtest, sem regra, sem otimização).
Lê primitives/*.json (extração RAW exclusiva de build_causal_primitives.py). Candidato = evento NAS (first-appearance)
de polaridade casada dentro de uma zona Custom OB v11 (=BigBeluga proxy) VIVA. Causal: decisão usa info até o close do
bar de confirmação do NAS (j); entrada = close do bar SEGUINTE (j+1, SHIFT1). Calcula features A–D+G do FEATURE_MAP.md
(zona, aceitação/rejeição, NAS, fluxo operacional, contexto). NÃO calcula pós-entrada/outcome (lado-saída = futuro).
Campo não mapeável → UNKNOWN_BLOCKED + para. Verified 2026-06-25."""
import json, csv, math, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = sorted((HERE / "primitives").glob("*.primitives.json"))
W_ARRIVAL, W_FLOW, K_SWING = 8, 60, 2

def load(p): return json.loads(Path(p).read_text())

def swing_flow(S, j):
    """fluxo operacional causal por swings (fractal k): +1 HH&HL, -1 LH&LL, 0 misto. Só usa bars<=j."""
    H = [b["h"] for b in S]; L = [b["l"] for b in S]
    sh, sl = [], []
    lo = max(K_SWING, j - W_FLOW)
    for i in range(lo, j - K_SWING + 1):
        seg_h = H[i - K_SWING:i + K_SWING + 1]; seg_l = L[i - K_SWING:i + K_SWING + 1]
        if H[i] == max(seg_h): sh.append(H[i])
        if L[i] == min(seg_l): sl.append(L[i])
    if len(sh) >= 2 and len(sl) >= 2:
        hh = sh[-1] > sh[-2]; hl = sl[-1] > sl[-2]
        if hh and hl: return 1
        if (not hh) and (not hl): return -1
    return 0

def in_zone(bar, zlo, zhi):  # range do bar intersecta a zona
    return bar["l"] <= zhi and bar["h"] >= zlo

def detect_block(prim):
    S = prim["series"]; n = len(S)
    tidx = {b["t"]: i for i, b in enumerate(S)}
    zones = prim["zones"]
    z_by_pol = {"DEMAND": [], "SUPPLY": []}
    for z in zones:
        pol = "DEMAND" if "DEMAND" in z["text"] else ("SUPPLY" if "SUPPLY" in z["text"] else None)
        if pol: z_by_pol[pol].append(z)
    nas = sorted(prim["nas_events"], key=lambda e: e["t"] if e["t"] else 0)
    smc = sorted(prim["smc_events"], key=lambda e: e["t"] if e["t"] else 0)
    smc_t = [e["t"] for e in smc]
    import bisect
    out = []
    blocked = set()
    for e in nas:
        if e["t"] not in tidx: continue
        j = tidx[e["t"]]
        if j + 1 >= n: continue
        atr = S[j]["atr"]
        if not atr: continue
        D = e["dir"]; pol = "DEMAND" if D == "LONG" else "SUPPLY"
        ref_price = e["price"] if e["price"] is not None else S[j]["c"]
        # zonas vivas casadas contendo o preço do NAS, as-of bar j
        cands = []
        for z in z_by_pol[pol]:
            bt, lt = z["born_t"], z["last_t"]
            if bt is None or lt is None: continue
            if not (bt <= e["t"] <= lt): continue
            zlo, zhi = z["low"], z["high"]
            if zlo is None or zhi is None or zhi <= zlo: continue
            if zlo <= ref_price <= zhi: cands.append((zhi - zlo, z))
        if not cands: continue
        cands.sort(key=lambda x: x[0]); z = cands[0][1]  # zona mais específica (estreita)
        zlo, zhi = z["low"], z["high"]; zmid = (zlo + zhi) / 2; zw = zhi - zlo
        born_i = tidx.get(z["born_t"])
        if born_i is None: born_i = 0
        # episódio in-zone que termina em j (run contíguo)
        rs = j
        while rs - 1 >= 0 and rs - 1 >= born_i and in_zone(S[rs - 1], zlo, zhi): rs -= 1
        run = S[rs:j + 1]
        bars_in_zone = len(run)
        # penetração (aceitação vs rejeição)
        if pol == "DEMAND":
            deepest = min(b["l"] for b in run); pen = (zhi - deepest) / zw
            acc_beyond_mid = any(b["c"] < zmid for b in run)
        else:
            deepest = max(b["h"] for b in run); pen = (deepest - zlo) / zw
            acc_beyond_mid = any(b["c"] > zmid for b in run)
        pen = max(0.0, min(1.5, pen))
        # chegada (velocidade pré-zona)
        a0 = max(0, rs - W_ARRIVAL)
        arrival_atr = abs(S[rs]["c"] - S[a0]["c"]) / atr if rs > a0 else 0.0
        # mitigação/retestes: toques (out->in) de born_i..rs-1 (antes do episódio atual)
        touches_before = 0; prev_in = False
        for i in range(born_i, rs):
            cur_in = in_zone(S[i], zlo, zhi)
            if cur_in and not prev_in: touches_before += 1
            prev_in = cur_in
        virgin = touches_before == 0
        # NAS cluster na zona (dir D, t em [born_t, t_nas], preço na zona)
        clus = [x for x in nas if x["dir"] == D and z["born_t"] <= (x["t"] or 0) <= e["t"]
                and x["price"] is not None and zlo <= x["price"] <= zhi]
        nas_count = len(clus)
        first_clus_i = tidx.get(clus[0]["t"]) if clus else j
        nas_cluster_span = j - (first_clus_i if first_clus_i is not None else j)
        nas_before_touch = any((x["t"] or 0) < S[rs]["t"] for x in clus)
        # SMC/estrutura
        k = bisect.bisect_right(smc_t, e["t"]) - 1
        last_smc = smc[k]["text"] if k >= 0 else None
        bars_since_smc = (j - tidx[smc[k]["t"]]) if (k >= 0 and smc[k]["t"] in tidx) else None
        bc50 = sum(1 for et in smc_t if et and S[max(0, j - 50)]["t"] <= et <= e["t"])
        flow = swing_flow(S, j)
        setup_vs_flow = "continuation" if (flow == (1 if D == "LONG" else -1)) else ("reversal" if flow == (-1 if D == "LONG" else 1) else "neutral")
        # contexto — ⚠️ DA#3: dist_edge_atr/entry_dt/hour_utc/dow derivam do bar j+1 (bar de ENTRADA).
        # São rótulo/contexto, NÃO usar como FILTRO de entrada (descrevem o bar de entrada, não o estado pré-decisão).
        entry = S[j + 1]; entry_close = entry["c"]
        edt = dt.datetime.utcfromtimestamp(entry["t"])
        dist_edge_atr = ((entry_close - zhi) / atr) if pol == "DEMAND" else ((zlo - entry_close) / atr)
        out.append({
            "block": prim["block"].replace("XAUUSD_15m_replay_", "").replace(".jsonl.gz", ""),
            "nas_id": e["id"], "dir": D, "nas_t": e["t"], "entry_t": entry["t"],
            "entry_dt": edt.strftime("%Y-%m-%dT%H:%M"), "entry_close": round(entry_close, 2),
            "zone_id": z["id"], "zone_type": pol, "zone_low": zlo, "zone_high": zhi,
            "zone_width_atr": round(zw / atr, 3), "zone_age_bars": j - born_i, "zone_pre_existing": z["pre_existing"],
            "zone_virgin": virgin, "mitig_count": touches_before,
            "penetration_pct": round(pen, 3), "bars_in_zone": bars_in_zone, "acceptance_beyond_mid": acc_beyond_mid,
            "arrival_atr": round(arrival_atr, 3), "nas_dist_ema_atr": S[j]["nas_dist"], "dist_edge_atr": round(dist_edge_atr, 3),
            "nas_count_in_zone": nas_count, "nas_cluster_span_bars": nas_cluster_span, "nas_before_touch": nas_before_touch,
            "op_flow": flow, "setup_vs_flow": setup_vs_flow, "last_smc": last_smc, "bars_since_smc": bars_since_smc,
            "smc_bos_choch_50": bc50, "rsi": S[j]["rsi"], "hour_utc": edt.hour, "dow": edt.weekday(),
        })
    return out, blocked

def main():
    allc = []; blocked_all = set()
    for p in PRIM:
        c, bl = detect_block(load(p)); allc.extend(c); blocked_all |= bl
        print(f"  {p.name.split('.')[0][-11:]}: {len(c)} candidatos")
    if blocked_all:
        print("UNKNOWN_BLOCKED:", blocked_all, "— PARANDO antes de improvisar."); return
    # ordena por tempo
    allc.sort(key=lambda r: r["entry_t"])
    cols = list(allc[0].keys()) if allc else []
    with open(HERE / "candidates_stageB.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(allc)
    with open(HERE / "candidates_stageB.jsonl", "w") as f:
        for r in allc: f.write(json.dumps(r, default=str) + "\n")
    print(f"\nTOTAL candidatos = {len(allc)} -> candidates_stageB.csv / .jsonl")
    return allc

if __name__ == "__main__":
    main()
