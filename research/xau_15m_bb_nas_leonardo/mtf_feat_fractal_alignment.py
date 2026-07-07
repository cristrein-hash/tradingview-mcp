#!/usr/bin/env python3
"""FAMILIA: ALINHAMENTO FRACTAL 15M->4H->1D(->1W) para classificar a FASE do entry XAU 15M.

Ideia (mercado fractal, 4 fases A/B/C/D repetem-se em cada escala):
  - Le a fase de CADA escala HTF pela POSICAO/MATURIDADE da propria perna corrente (ESCALA RELATIVA,
    nao direcao absoluta que so reflete o ano).
  - Constroi features de (des)ALINHAMENTO entre escalas:
      A markup       = 15M-pullback dentro de 4H-up dentro de 1D-up  (both_up, pos moderada)
      B iniciacao    = 15M-flush dentro de 1D-up mas 4H-down         (conflito 4H<->1D, fresco)
      C distribuicao = 15M perto de 4H-top E 1D-top                  (both_up, pos alta)
      D bear         = 15M em 4H-down E 1D-down                      (both_down)

ANTI-LOOKAHEAD (regra dura): SO htf_closed_upto(tf, e['t']) -> barras HTF com END<=t (barra corrente
EXCLUIDA). A ultima barra HTF usada tem sempre end<=t. Zero close do dia/semana corrente.
ESCALA RELATIVA: posicao no range da PROPRIA perna + maturidade em barras HTF desde a origem da perna.
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np
from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, PHASE, oof_mining_null

HERE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
SCALES = ["4H", "1D", "1W"]
ZZ_R = {"4H": 2.0, "1D": 2.0, "1W": 1.5}  # zigzag reversal em ATR-HTF por escala


def leg_read(tf, t):
    """Le a perna HTF corrente RELATIVA a si propria, usando SO barras fechadas (end<=t).
    Devolve dict com: dir(+1/-1), pos(0..1 na traversia da perna), mat(barras desde o pivo=maturidade),
    ext(dist do pivo em ATR, sinalizado), rng(range da perna em ATR), n_closed, last_end.
    Anti-lookahead garantido por htf_closed_upto. Fallback robusto quando ha poucos pivos."""
    bars = htf_closed_upto(tf, t)
    n = len(bars)
    if n < 6:
        return None
    piv, H, L, C, A = htf_swings(bars, ZZ_R[tf])
    last_end = bars[-1]["end"]
    atr = (A[-1] if A and A[-1] else 1.0) or 1.0
    Cn = C[-1]
    if not piv:
        # sem pivo confirmado: perna = do inicio da janela ate agora
        p_idx, p_type, p_price = 0, ("L" if C[-1] >= C[0] else "H"), (L[0] if C[-1] >= C[0] else H[0])
    else:
        p_type, p_idx, p_price = piv[-1]
    seg_H = max(H[p_idx:]) if p_idx < n else H[-1]
    seg_L = min(L[p_idx:]) if p_idx < n else L[-1]
    rng = max(seg_H - seg_L, 1e-9)
    if p_type == "L":            # ultimo pivo = low -> perna UP
        d = 1.0
        pos = (Cn - seg_L) / rng          # 0=fresco off-low, 1=perto do topo
    else:                        # ultimo pivo = high -> perna DOWN
        d = -1.0
        pos = (seg_H - Cn) / rng          # 0=fresco off-top, 1=perto do fundo
    pos = float(min(1.0, max(0.0, pos)))
    mat = float(n - 1 - p_idx)                     # barras HTF desde a origem da perna (maturidade)
    ext = float((Cn - p_price) / atr)              # extensao sinalizada desde o pivo
    rng_atr = float(rng / atr)
    return {"dir": d, "pos": pos, "mat": mat, "ext": ext, "rng": rng_atr,
            "n_closed": n, "last_end": last_end}


def features_for(e):
    t = e["t"]
    R = {s: leg_read(s, t) for s in SCALES}
    f = {}
    # ---- per-escala (relativas a propria perna) ----
    for s in SCALES:
        r = R[s]
        if r is None:
            r = {"dir": 0.0, "pos": 0.5, "mat": 0.0, "ext": 0.0, "rng": 0.0}
        f[f"dir_{s}"] = r["dir"]
        f[f"pos_{s}"] = r["pos"]
        f[f"mat_{s}"] = r["mat"]
        f[f"ext_{s}"] = r["ext"]
        f[f"rng_{s}"] = r["rng"]
    d4, d1, dw = f["dir_4H"], f["dir_1D"], f["dir_1W"]
    p4, p1, pw = f["pos_4H"], f["pos_1D"], f["pos_1W"]
    # ---- ALINHAMENTO fractal entre escalas (o coracao da familia) ----
    f["align_4H_1D"] = d4 * d1                       # +1 alinhado, -1 conflito
    f["align_1D_1W"] = d1 * dw
    f["dir_sum"] = d4 + d1 + dw                       # -3..+3 confluencia direcional
    f["both_up"] = 1.0 if (d4 > 0 and d1 > 0) else 0.0
    f["both_down"] = 1.0 if (d4 < 0 and d1 < 0) else 0.0
    f["conflict_4H_1D"] = 1.0 if (d4 * d1 < 0) else 0.0
    # A markup: both_up + pos NAO no topo (perna 4H fresca/media dentro de 1D-up)
    f["A_markup"] = f["both_up"] * (1.0 - p4)
    # B iniciacao: 1D-up mas 4H-down (flush), fresco (pos4H baixa na perna down = perto do topo antes de virar)
    f["B_init"] = (1.0 if (d1 > 0 and d4 < 0) else 0.0) * (1.0 - p4)
    # C distribuicao: both_up E pos alta em ambas as escalas (perto do topo fractal)
    f["C_distrib"] = f["both_up"] * p4 * p1
    # D bear: both_down + maturidade da queda 1D
    f["D_bear"] = f["both_down"] * min(1.0, f["mat_1D"] / 20.0)
    # confluencia de POSICAO no topo (independe de dir) — quanto ambos estao esticados p/ cima
    f["top_conf"] = (p4 if d4 > 0 else 0.0) * (p1 if d1 > 0 else 0.0)
    f["fresh_conf"] = ((1 - p4) if d4 > 0 else 0.0) * ((1 - p1) if d1 > 0 else 0.0)
    return f, R


def main():
    rows = []
    causal_ok = True
    causal_detail = []
    for e in ENTRIES:
        f, R = features_for(e)
        rows.append({"n": e["n"], **{k: round(float(v), 5) for k, v in f.items()}})
        # prova de causalidade: cada barra HTF usada tem end<=t
        for s in SCALES:
            if R[s] is not None and R[s]["last_end"] > e["t"]:
                causal_ok = False
                causal_detail.append((e["n"], s, R[s]["last_end"], e["t"]))
    feat_names = [k for k in rows[0].keys() if k != "n"]

    # ---- VERIFICA QUE DISPARAM (variancia/min/max) ----
    print("=== FEATURES FIRE-CHECK (var / min / max / n_unique) ===")
    Xcols = []
    dead = []
    for name in feat_names:
        col = np.array([r[name] for r in rows], dtype=float)
        v = col.var(); nu = len(np.unique(np.round(col, 6)))
        flag = "DEAD" if (v < 1e-12 or nu <= 1) else "ok"
        if flag == "DEAD":
            dead.append(name)
        print(f"  {name:16s} var={v:10.5f} min={col.min():9.4f} max={col.max():9.4f} uniq={nu:3d} {flag}")
        Xcols.append(col)
    print("DEAD features:", dead if dead else "NONE")

    # causalidade
    print("\n=== CAUSALIDADE (anti-lookahead) ===")
    print("todas barras HTF usadas com end<=t?", causal_ok)
    if not causal_ok:
        print("VIOLACOES:", causal_detail[:10])
    # amostra explicita das ultimas barras HTF de 3 entries
    for e in [ENTRIES[0], ENTRIES[len(ENTRIES)//2], ENTRIES[-1]]:
        det = []
        for s in SCALES:
            b = htf_closed_upto(s, e["t"])
            det.append(f"{s}:end={b[-1]['end']}<=t={e['t']}:{b[-1]['end']<=e['t']}")
        print(f"  n={e['n']:3d} t={e['t']}  " + "  ".join(det))

    # ---- salva feature_file ----
    fpath = f"{HERE}/mtf_feat_fractal_alignment.json"
    json.dump(rows, open(fpath, "w"), indent=0)
    print(f"\nfeature_file salvo: {fpath}  ({len(rows)} rows x {len(feat_names)} feats)")

    # ---- matriz X (drop dead cols) e OOF mining-null ----
    use_names = [n for n in feat_names if n not in dead]
    X = np.column_stack([np.array([r[n] for r in rows], dtype=float) for n in use_names])
    print(f"\nX shape = {X.shape}  (feats usadas: {use_names})")
    print("\n=== OOF MINING-NULL ===")
    res = oof_mining_null(X)
    for k, v in res.items():
        print(f"  {k}: {v}")
    # dump result p/ leitura estruturada
    json.dump({"oof": res, "feat_names": use_names, "causal_ok": causal_ok},
              open(f"{HERE}/mtf_feat_fractal_alignment_result.json", "w"), indent=2)
    return res


if __name__ == "__main__":
    main()
