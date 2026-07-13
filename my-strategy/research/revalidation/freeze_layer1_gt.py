#!/usr/bin/env python3
"""CONGELAMENTO DO GROUND-TRUTH LAYER 1 (MACRO) — ordem Cris 2026-07-13.
Fonte: 16 retângulos translúcidos desenhados pelo Cris no chart 1D (lidos via MCP, scratchpad
layer1_raw.json). Cor rgba → regime: verde(76,175,80)=BULL · vermelho(242,54,69)=BEAR ·
laranja(255,152,0)=RANGE. DEFINIÇÃO CONGELADA (Cris): Layer 1 = "regime que CONTÉM legs" —
pode ser curto se estruturalmente decisivo (o bloco nov/2024 de 1 semana É macro válido; NÃO há
duração mínima). Bordas APROXIMADAS: tolerância ±5 dias (Layer macro tolera mais que os ±3d do
GT 4H). NESTED: blocos RANGE dentro de BULL (dez/23, mai/24) = sub-regime aninhado — marcados
`nested: true`; para o scoring do detector Layer 1 o rótulo efetivo de uma barra = o bloco MAIS
INTERNO que a contém (o range aninhado manda sobre o bull que o envolve).
Saída: results/REGIME_GT_LAYER1_CRIS_1D_20260713.json + sha256."""
import json, hashlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/"
           "d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/layer1_raw.json")
OUT = HERE/"results/REGIME_GT_LAYER1_CRIS_1D_20260713.json"
COLOR2REG = {"76, 175, 80": "BULL", "242, 54, 69": "BEAR", "255, 152, 0": "RANGE"}
BORDER_TOL_S = 5*86400

def main():
    src = json.load(open(SRC))
    wins = []
    for r in src:
        reg = next((v for k, v in COLOR2REG.items() if k in r["bg"]), None)
        if reg is None or len(r["ts"]) < 2: continue
        wins.append({"id": r["id"], "regime": reg, "t0": r["ts"][0], "t1": r["ts"][1],
                     "d0": dt.datetime.utcfromtimestamp(r["ts"][0]).strftime("%Y-%m-%d"),
                     "d1": dt.datetime.utcfromtimestamp(r["ts"][1]).strftime("%Y-%m-%d"),
                     "px_lo": round(r["px"][0], 1), "px_hi": round(r["px"][1], 1),
                     "dur_dias": round((r["ts"][1]-r["ts"][0])/86400, 0)})
    wins.sort(key=lambda w: (w["t0"], -(w["t1"]-w["t0"])))
    # marcar aninhados: bloco cujo [t0,t1] está DENTRO de outro bloco maior
    for i, w in enumerate(wins):
        w["nested"] = any(j != i and o["t0"] <= w["t0"] and w["t1"] <= o["t1"]
                          and (o["t1"]-o["t0"]) > (w["t1"]-w["t0"]) for j, o in enumerate(wins))
    gt = {"name": "REGIME_GT_LAYER1_CRIS_1D_20260713", "status": "FROZEN_GROUND_TRUTH",
          "layer": "1 (MACRO)", "frozen_at": "2026-07-13",
          "definition": ("Layer 1 = regime que CONTÉM legs (Layer 2 = leg v2 no interior). "
                         "Pode ser curto se estruturalmente decisivo — SEM duração mínima "
                         "(bloco nov/2024 de ~7 dias é macro válido, ordem Cris)."),
          "source": "16 retângulos do Cris no chart 1D, lidos via MCP 2026-07-13",
          "borders": "APROXIMADAS — tolerância ±5 dias por borda excluída do scoring",
          "border_tolerance_s": BORDER_TOL_S,
          "nested_rule": "rótulo efetivo de uma barra = bloco MAIS INTERNO que a contém "
                         "(range aninhado > bull envolvente); usado no scoring do detector Layer 1",
          "scoring": "concordância barra-a-barra (1D ou 4H) vs rótulo efetivo; métrica intrínseca, NUNCA P&L",
          "n_windows": len(wins),
          "n_bull": sum(1 for w in wins if w["regime"] == "BULL"),
          "n_bear": sum(1 for w in wins if w["regime"] == "BEAR"),
          "n_range": sum(1 for w in wins if w["regime"] == "RANGE"),
          "n_nested": sum(1 for w in wins if w["nested"]),
          "windows": wins}
    OUT.write_text(json.dumps(gt, indent=1, ensure_ascii=False))
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"GT Layer 1 congelado: {OUT.name} · {len(wins)} janelas "
          f"(BULL {gt['n_bull']} · BEAR {gt['n_bear']} · RANGE {gt['n_range']} · "
          f"aninhados {gt['n_nested']}) · sha256 {sha[:16]}…")
    for w in wins:
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6} {w['dur_dias']:>4.0f}d"
              f"{'  [ANINHADO]' if w['nested'] else ''}")

if __name__ == "__main__":
    main()
