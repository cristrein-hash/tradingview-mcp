# BEAR-LEG BLOCK v3 — KNOWLEDGE STATE (avanço consolidado)

**2026-06-22. commit 184cdba.** Diagnóstico/calibração nos 62 (ensino). NÃO produção, NÃO 276/OOS, NÃO promover.
Preservação do avanço positivo antes de atacar a microestrutura.

## Regra (sobre o v2)
- **BLOCK_CORRECTIVE_PULLBACK** = `leg==MACRO_CORRECTIVE_PULLBACK AND NOT bottom_turn AND drop20_atr<1.0`.
  Não é bloquear toda corrective leg — é bloquear **corrective pullback RASO** (comprou dip sem flush).
- **Carve-out scope fix**: PRESERVE_BOTTOM_TURN só fora de MACRO_BULL_LEG (corrige misfire T17/T30).

## Separador validado (sem ID-fit)
**drop20_atr** separa corrective raso de flush real, margem larga:
- shallow dip (block): T12=0.12, T25=0.30, T26=0.29, S28=0.00 — todos <0.5
- real flush (preserve): S3=1.69, S27=4.28 — robusto thr [0.5,1.5] idêntico, gap 0.32→1.69.

## Resultado
- **Bloqueados (alvo): T12, T25, T26, S28** ✓
- **Preservados: S3, S27** (flush) · **S15** (bottom-turn carve-out) ✓
- **S7/S8/S13** = blocks bear-markdown corretos (Cris confirmou) — não recuperar.
- **A preserved 23/26**; **ZERO anchor novo-bloqueado** (T34 bloqueio é pré-existente v2, fora de escopo).
- DA general-purpose PASS 17/17; SMOKE PASS (reconstrução v2 == v2 CSV 62/62).

## Frentes que continuam abertas
- **T17/T20**: microestrutura (range-bull micro-topo). Atacada no bloco seguinte → **NÃO capturável** com features
  causais disponíveis (ver `XAU_4H_MICRO_STRUCTURE_LIQUIDITY_ENGINE_REPORT.md`).
- **T23**: classifier-error / bear-as-of-entry / hindsight — não resolvido.
- **T32 / S11**: late-top residual aceitável. **S40**: fatal-skip aceitável (fora dos 62).

Outputs: `results/l2_bpt_bear_leg_block_gate_v3_*.csv`, `bear_leg_block_gate_v3.py`,
`docs/XAU_4H_MACRO_BEAR_LEG_BLOCK_GATE_V3_REPORT.md`.
