# MANIFEST — Lab Cp REFINO (anti-faca + mais entrys corretas)

Aberto 2026-07-17 (Cris aprovou plano + "RODA"). Refino do **Cp = capitulação faca-caindo**
(baseline `CP_ENGINE_PREREG_FORWARD_20260716`, USER_APPROVED_NOT_PRODUCTION 2026-07-16).
NÃO é o Cg (capitulação grind, tasks #23-32 — workstream separado, não tocado).

## Baseline (CONGELADO, §1-§6 imutáveis) — re-verificado da fonte 2026-07-17
- Motor `cp_refined.py` (entry_first 1º-reclaim + SL=fundo−0,1ATR + exit_fixed3R).
- Gates `run()`: legMag(H[hb]−L[p])/atr≥15 · is_leg_bottom L[p]≤min(192) · confluência auction
  (buy_dens≥0,25 OU leg_sell≥180).
- Universo diagnóstico: `cp_plot_window` (4 blocos Ago2025→Jul2026, T_LO Set/2025).
- **26 trades · 10 KNIFE · 9 WIN · 5 GRAB · 2 OPEN** (byte-exato via `cp_knife_diag`).
- Facas fundas: #11 −9,5R · #20 −12,9R · #22 −6,8R · #23 −5,7R.
- 3 clusters cascata: 2025-10-22 (×3) · 2026-03-19 (×5) · 2026-06-23 (×4).
- **GT = 5 janelas hardcoded** `cp_refined.py` L48 (bear2026, marcadas pelo Cris). Refino NÃO pode matar GT.

## RAW_LINEAGE
- Preço/bubbles: RAW 15M `/Volumes/GUTS_ LACIE/.../XAUUSD/15M/*.jsonl.gz` (4 blocos). RAW-first, causal, close-only.
- Leg/regime 4H: `leg_v3`→`leg_refine_harness`→`leg_state_4h` (zigzag R=6)→`gt_pivot_structural_harness`
  (RAW 4H `raw_4h_ohlc.jsonl`, agora VIVO via regime engine até 2026-07-17). Sem primitives, sem SLIM.

## STRUCTURAL_FIRST (Stage-3, ESTE passo)
Tabela causal por candidato Cp: {macro_regime, leg_v3, leg_age, posição-perna, espaço-abaixo, classe faca, GT}.
Mapeamento 15M→4H = bar-close-causal (última 4H fechada, TS4+14400≤etime).
Trava-mãe do protocolo: sem macro_regime+leg_state+family, nenhum gate/indicador vira evidência.

## Hipóteses congeladas (medir, não assumir)
- H1 leg-gate: cortar entrada em IMPULSO_DOWN corrente (faca=impulso a acelerar).
- H2 cooldown-cascata; H3 reclaim-que-segura (=entry_postgrab); H4 espaço-vazio-abaixo.
- H5 pós-grab (recupera GRABs); H6 (só se necessário) afrouxar dentro de regime seguro.

## Critério de sucesso (congelado ANTES de ver, plano aprovado)
ADOTADO só se TODOS: facas 10→≤4 · avgR≥baseline · streak≤prereg · GT 5/5 preservado ·
bate null buy-any-reclaim bear 22% · jackknife não-negativo. Senão baseline fica, refino=estudo.
DA lookahead obrigatório antes de conclusão.
