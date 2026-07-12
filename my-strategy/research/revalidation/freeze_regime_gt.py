#!/usr/bin/env python3
"""CONGELAMENTO DO GROUND-TRUTH DE REGIME 4H (ordem Cris 2026-07-12).
Fonte: results/cris_regime_overlays_20260712.json (lido via MCP do chart — desenhos do Cris).
Regras congeladas AQUI, ANTES de qualquer tuning/contenção (anti-overfit):
  - GT = janelas COLORIDAS do Cris (verde=BULL, vermelho=BEAR, laranja=RANGE).
  - Cinza (CONFUSO) = DESCARTADO do GT (ordem Cris 2026-07-12: redundante — dentro dela ele
    organizou BULL/BEAR/RANGE corretamente com janelas coloridas; não contabilizar).
  - BORDAS = APROXIMADAS (Cris: "não fiz desenhos com precisão de vela nas bordas/transições;
    fiz aproximado"). Tolerância congelada: ±3 dias (±18 barras 4H) em cada borda EXCLUÍDOS
    do scoring de concordância.
  - Fora das janelas coloridas: sem GT (Cris: sem overlay = detecção atual funciona) —
    scoring de concordância definido SÓ dentro das janelas coloridas menos as bordas.
  - Métrica intrínseca = concordância barra-a-barra dentro do escopo acima. NUNCA P&L.
Saída: results/REGIME_GT_CRIS_4H_20260712.json + sha256 (selo)."""
import json, hashlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE/"results/cris_regime_overlays_20260712.json"
OUT = HERE/"results/REGIME_GT_CRIS_4H_20260712.json"
COLOR2REG = {"242, 54, 69": "BEAR", "76, 175, 80": "BULL", "255, 152, 0": "RANGE",
             "184, 184, 184": "CONFUSO"}
BORDER_TOL_S = 3*86400

def main():
    src = json.load(open(SRC))
    wins, notes = [], []
    for r in src["cris"]:
        if r["name"] == "text_note":
            notes.append({"id": r["id"], "text": r["text"]}); continue
        bg = r.get("bg") or ""
        reg = next((v for k, v in COLOR2REG.items() if k in bg), None)
        if reg is None or reg == "CONFUSO": continue   # sólidos = plot do detector; CONFUSO descartado (Cris)
        ts = sorted(p["time"] for p in r["points"])
        px = sorted(p["price"] for p in r["points"])
        wins.append({"id": r["id"], "regime": reg, "t0": ts[0], "t1": ts[1],
                     "d0": dt.datetime.utcfromtimestamp(ts[0]).strftime("%Y-%m-%d"),
                     "d1": dt.datetime.utcfromtimestamp(ts[1]).strftime("%Y-%m-%d"),
                     "px_lo": round(px[0], 2), "px_hi": round(px[1], 2)})
    wins.sort(key=lambda w: w["t0"])
    gt = {"name": "REGIME_GT_CRIS_4H_20260712",
          "status": "FROZEN_GROUND_TRUTH",
          "frozen_at": "2026-07-12",
          "source": "desenhos manuais do Cris no chart 4H XAUUSD, lidos via MCP (commit eda003b)",
          "borders": "APPROXIMATE — tolerância ±3 dias por borda EXCLUÍDA do scoring (congelado)",
          "border_tolerance_s": BORDER_TOL_S,
          "scoring": ("concordância barra-a-barra SÓ dentro das janelas coloridas, excluindo "
                      "±tolerância nas bordas; CONFUSO descartado do GT (redundante, Cris); fora das janelas sem GT; "
                      "métrica intrínseca — NUNCA P&L de trades"),
          "hindsight_caveat": "GT desenhado vendo histórico completo — árbitro de leitura, não de causalidade",
          "n_windows": len(wins), "windows": wins, "notes": notes}
    OUT.write_text(json.dumps(gt, indent=1, ensure_ascii=False))
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"GT congelado: {OUT.name} · janelas {len(wins)} "
          f"({sum(1 for w in wins if w['regime']!='CONFUSO')} coloridas + "
          f"{sum(1 for w in wins if w['regime']=='CONFUSO')} CONFUSO) · sha256 {sha[:16]}…")
    for w in wins: print(f"  {w['d0']}→{w['d1']} {w['regime']}")

if __name__ == "__main__":
    main()
