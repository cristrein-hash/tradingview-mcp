#!/usr/bin/env python3
"""CAUSAL INDICATOR LAYER — evidencia de leitura (NAO decisao) para pacotes cegos futuros.
Refinamento Cluster 2: o pacote cego estava form-only; faltava o layer de indicador que o olho usa.
NAS / RSI-divergence / bubbles / SMC entram como EVIDENCIA que faz PERGUNTAS (capitulacao? absorcao? exaustao?
mudanca de carater? whipsaw?), nunca como TAKE/SKIP/score. Causal: so barras <= entry (SHIFT1 p/ repintantes).
SEM outcome, SEM nomes de lente, SEM rotulo de resultado. Mapping bubble canonico: BUY=plot_0/2/4, SELL=plot_6/8/10.

Uso: import indicator_evidence(bar_idx, F, QP) -> dict pronto p/ embutir no pacote cego.
Demo: python3 l2_bpt_causal_indicator_layer.py  (roda nos 10 bars do cluster 2 e mostra a evidencia)."""
import json

BUY_PLOTS = {"plot_0", "plot_2", "plot_4"}
SELL_PLOTS = {"plot_6", "plot_8", "plot_10"}
SIZE = {"plot_4": "L", "plot_10": "L", "plot_2": "m", "plot_8": "m", "plot_0": "s", "plot_6": "s"}

def _fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def indicator_evidence(b, F, QP, lookback=20):
    """Evidencia causal de indicador no episodio b, framed como PERGUNTAS de leitura. SEM outcome."""
    lo = max(1, b - lookback + 1)
    win = list(range(lo, b + 1))
    H = [F[i]["high"] for i in range(len(F))]; L = [F[i]["low"] for i in range(len(F))]
    C = [F[i]["close"] for i in range(len(F))]; RSI = [F[i].get("rsi") for i in range(len(F))]
    # --- bubbles (aparicao AT bar j: bars_ago==0) na janela ---
    buys, sells = [], []
    for j in win:
        for bub in (F[j].get("bubbles_recent") or []):
            if bub.get("bars_ago") != 0:
                continue
            pid = bub.get("plot_id")
            if pid in BUY_PLOTS: buys.append((j, SIZE.get(pid, "s")))
            elif pid in SELL_PLOTS: sells.append((j, SIZE.get(pid, "s")))
    sell_large = sum(1 for _, s in sells if s in ("m", "L"))
    buy_large = sum(1 for _, s in buys if s in ("m", "L"))
    # sell-bubbles concentradas perto do LOW da janela? (assinatura de clima de capitulacao)
    win_low = min(L[j] for j in win); atrish = (max(H[j] for j in win) - win_low) or 1.0
    sells_near_low = sum(1 for j, _ in sells if (L[j] - win_low) / atrish < 0.25)
    # --- NAS / SMC: no frozen RAW sao STALE (snapshot fixo; precos nao batem com a era do bar) -> UNRELIABLE ---
    # Verificacao de staleness: media dos precos das labels vs close do bar. >15% = stale.
    def _stale(entries):
        ps = [_fn(e.get("price")) for e in (entries or []) if _fn(e.get("price")) is not None]
        if not ps or not C[b]:
            return None
        med = sorted(ps)[len(ps) // 2]
        return abs(med - C[b]) / C[b] > 0.15
    nas_stale = _stale(F[b].get("nas_recent")); smc_stale = _stale(F[b].get("smc_recent"))
    # --- RSI: valor, recente-min, hint de divergencia (heuristico, NAO o indicador do chart) ---
    rsi_now = _fn(RSI[b]); rsi_win = [r for r in (_fn(RSI[j]) for j in win) if r is not None]
    rsi_min = min(rsi_win) if rsi_win else None; rsi_max = max(rsi_win) if rsi_win else None
    q = QP.get(b, {}) if QP else {}
    bear_div = q.get("bear_div")
    # bull-div hint causal: preco faz novo low na 2a metade da janela, mas RSI no low NAO e o minimo
    bull_div_hint = None
    if len(win) >= 8 and rsi_win:
        half = win[len(win) // 2:]
        price_ll = min(L[j] for j in half) <= win_low + 1e-9
        rsi_at_pricelow = _fn(RSI[min(half, key=lambda j: L[j])])
        if price_ll and rsi_at_pricelow is not None and rsi_min is not None:
            bull_div_hint = rsi_at_pricelow > rsi_min + 1.0  # RSI nao confirmou o novo low
    return {
        "_nota": "EVIDENCIA DE LEITURA, nao decisao. Indicador faz PERGUNTAS, nao classifica TAKE/SKIP.",
        "bubbles": {"buy_total": len(buys), "sell_total": len(sells), "buy_m+L": buy_large,
                    "sell_m+L": sell_large, "sell_concentradas_no_low": sells_near_low},
        "nas": {"status": "UNRELIABLE_IN_FROZEN_RAW", "stale_detectado": nas_stale,
                "_nota": "nas_recent e snapshot fixo (precos da era 2018-19); usar fonte pine_labels causal (first-appearance LONG/SHORT) em pacote futuro"},
        "smc": {"status": "UNRELIABLE_IN_FROZEN_RAW", "stale_detectado": smc_stale,
                "_nota": "smc_recent idem stale; BOS/CHoCH causal exige captura pine_labels SHIFT1 em pacote futuro"},
        "rsi": {"agora": rsi_now, "min_janela": rsi_min, "max_janela": rsi_max,
                "bear_div_flag": bear_div, "bull_div_hint_heuristico": bull_div_hint},
        "PERGUNTAS_DE_LEITURA": [
            f"CAPITULACAO? sell-bubbles m/L concentradas no low={sells_near_low} (de {sell_large}) + rsi_min={rsi_min} (oversold?)",
            f"ABSORCAO? buy-bubbles m/L={buy_large} defendendo o low? (NAS indisponivel no RAW)",
            f"EXAUSTAO? rsi_max={rsi_max} + bear_div_flag={bear_div} (topo? NAS/SMC indisponiveis)",
            "MUDANCA DE CARATER? SMC (BOS/CHoCH) UNRELIABLE no frozen RAW — exige fonte pine_labels causal",
            f"WHIPSAW? bull_div_hint={bull_div_hint} com estrutura nao confirmada — tentativa-de-fundo vs reversao confirmada?",
        ],
    }

if __name__ == "__main__":
    RR = "repro_recovery"
    F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
    QP = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
    CLUSTER2 = [5826, 1623, 4401, 3825, 1522, 1873, 5627, 1775, 3949, 3929]
    print("DEMO causal indicator layer — cluster 2 (evidencia, sem outcome):\n")
    for b in CLUSTER2:
        ev = indicator_evidence(b, F, QP)
        bb = ev["bubbles"]; r = ev["rsi"]
        print(f"#{b}: sell-bubbles {bb['sell_total']} (m/L {bb['sell_m+L']}, no_low {bb['sell_concentradas_no_low']}) "
              f"| buy-bubbles {bb['buy_total']} (m/L {bb['buy_m+L']}) | rsi {r['agora']} min{r['min_janela']} "
              f"bull_div_hint={r['bull_div_hint_heuristico']} | NAS/SMC=UNRELIABLE")
    print("\n(NAS/SMC stale no frozen RAW -> pacote futuro precisa de fonte pine_labels causal. Bubbles+RSI sao causais.)")
    print("\nLayer pronto p/ embutir em pacotes cegos futuros. Evidencia faz perguntas; o Reader responde. SEM outcome/nomes-de-lente.")
