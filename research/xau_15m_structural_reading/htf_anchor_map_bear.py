#!/usr/bin/env python3
"""MEDIDOR A — MAPA DE ÂNCORAS HTF, família BEAR (prereg XAU_15M_HTF_ANCHOR_OB_PREREG.md).
Leitura DINÂMICA multi-fatorial de contexto superior (episódios de regime v5 + profundidade 1D +
estrutura acima) — não snapshot de eixo único. MEDIDOR contínuo: sem cortes, sem votos; leitura =
READER; caminho = CRIS. Sem entry/backtest.

Âncoras: episódios = runs do macro v5 hour-causal (Data.macro_at, já vivo/verbatim) sobre as barras
15M CLOSED (F0, sha verificado). Uma âncora só é utilizável DEPOIS do fecho do episódio (causal).
Por marca do BEAR-set (12 FUNDO ≥2026-03-01 + 3 INVALIDO mar/2026; counts fail-loud 26/4/12):
  dist_prior_episode_bottom_atr (assinada; negativa = marca ABAIXO do bottom anterior)
  dist_prior_range_bottom_atr   (último episódio RANGE fechado)
  px_vs_ema1d_atr               (feature do filtro capitulation VIVO; price-agg 1D interna, D-1)
  lh_staircase_0_3              (máximos de janelas 96/192/288/384 em escada descendente)
Referência informativa: as mesmas medidas nos 26 BULL (contexto, sem leitura de decisão)."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]/"xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
GT = HERE.parents[0]/"xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
RANGE_DATES = {"2025-08-01", "2025-08-20", "2025-11-18", "2025-11-21"}

def main():
    D = Data()
    n = len(D.TS)
    # ---- episódios de regime (macro v5 por barra; runs; âncoras publicadas no fecho) ----
    epis = []
    cur = None
    for i in range(n):
        m = D.macro_at(D.TS[i])
        if cur is None or m != cur["regime"]:
            if cur is not None:
                cur["t_end"] = D.TS[i]
                epis.append(cur)
            cur = {"regime": m, "t_start": D.TS[i], "bot": D.L[i], "top": D.H[i]}
        else:
            cur["bot"] = min(cur["bot"], D.L[i]); cur["top"] = max(cur["top"], D.H[i])
    # episódio corrente fica aberto (não é âncora)
    # ---- EMA21 do 1D price-agg interna (dias FECHADOS) ----
    dk = D.DK; dc = D.DC
    ema = []
    k = 2/(21+1); e = dc[0]
    for v in dc:
        e = v*k + e*(1-k); ema.append(e)
    def px_vs_ema1d(t, px, a15):
        di = bisect.bisect_left(dk, t//86400)-1   # último dia FECHADO
        return (px-ema[di])/(a15 or 5) if di >= 0 else None
    # ---- GT: conjuntos fail-loud ----
    cat = json.load(open(GT))
    fundos = cat["notes"]["FUNDO"]
    bear = [x for x in fundos if x["date"] >= "2026-03-01"]
    rng = [x for x in fundos if x["date"][:10] in RANGE_DATES]
    bull = [x for x in fundos if x["date"] < "2026-03-01" and x["date"][:10] not in RANGE_DATES]
    inval = [x for x in cat["notes"]["INVALIDO"] if x["date"] >= "2026-03-01"]
    assert (len(bull), len(rng), len(bear)) == (26, 4, 12), f"counts {len(bull)}/{len(rng)}/{len(bear)} != 26/4/12"
    assert len(inval) == 3, f"INVALIDO mar/2026 = {len(inval)} != 3"
    def measure(x, tag):
        t, px = x["t"], x["price"]
        i = bisect.bisect_right(D.TS, t)-1
        a = D.ATR[i] or 5.0
        closed = [e for e in epis if e["t_end"] <= t]
        prev = closed[-1] if closed else None
        prev_rng = next((e for e in reversed(closed) if e["regime"] == "RANGE"), None)
        # estrutura acima: escada de máximos
        stair = 0
        hs = []
        for w in range(4):
            lo_i = max(0, i-96*(w+1)); hi_i = i-96*w
            if hi_i > lo_i: hs.append(max(D.H[lo_i:hi_i]))
        for w in range(len(hs)-1):
            if hs[w] < hs[w+1]: stair += 1
            else: break
        return {"tag": tag, "date": x["date"], "px": round(px, 1),
                "macro_at_mark": D.macro_at(t),
                "prev_episode": (prev["regime"] if prev else None),
                "dist_prior_episode_bottom_atr": round((px-prev["bot"])/a, 1) if prev else None,
                "dist_prior_range_bottom_atr": round((px-prev_rng["bot"])/a, 1) if prev_rng else None,
                "px_vs_ema1d_atr": round(px_vs_ema1d(t, px, a), 1),
                "lh_staircase_0_3": stair}
    rows = ([measure(x, "FUNDO_BEAR") for x in bear] + [measure(x, "INVALIDO") for x in inval])
    ref_bull = [measure(x, "FUNDO_BULL_ref") for x in bull]
    ref_rng = [measure(x, "FUNDO_RANGE_ref") for x in rng]
    out = {"prereg": "XAU_15M_HTF_ANCHOR_OB_PREREG.md",
           "n_episodios_regime": len(epis),
           "episodios_2026": [{"regime": e["regime"],
                               "start": dt.datetime.utcfromtimestamp(e["t_start"]).strftime("%Y-%m-%d"),
                               "end": dt.datetime.utcfromtimestamp(e["t_end"]).strftime("%Y-%m-%d"),
                               "bot": round(e["bot"], 0), "top": round(e["top"], 0)}
                              for e in epis if e["t_end"] >= dt.datetime(2025, 10, 1).timestamp()],
           "bear_set": rows, "ref_bull": ref_bull, "ref_range": ref_rng,
           "note": "MEDIDOR contínuo — sem cortes; leitura = READER; caminho = CRIS"}
    (HERE/"results/htf_anchor_map_bear_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        print(f"{r['tag']:>11} {r['date']}  prev={r['prev_episode']:<5} distEpBot {r['dist_prior_episode_bottom_atr']:>7} "
              f"distRngBot {r['dist_prior_range_bottom_atr']:>7} 1D {r['px_vs_ema1d_atr']:>6} LH {r['lh_staircase_0_3']}")
    print("episodios 2026:", json.dumps(out["episodios_2026"]))
    print("MEASURED_OK")

if __name__ == "__main__":
    main()
