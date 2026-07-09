# F1 — STRUCTURAL LEG MACHINE REPORT (2026-07-09) — STATUS: BUILT, TRUNCATION-PASS; SEED DEGENERADO

Script: `f1_structural_leg_machine.py` · Result: `results/f1_structural_leg_machine_result.json`.

## O que foi construído (spec v1.2)
- `macro_regime`: porte VERBATIM do v5 hour-causal (diário estável N15/K5 + override 1H P48/mom24/
  dd6%/rec120) sobre agregação price-only do RAW (paridade de LÓGICA C1: mesmo código, funções
  idênticas linha a linha; zero primitives).
- `leg_dir`: `raw_stable()` VERBATIM com barra=bucket 1H (E50/E100, slope lb5, s100 lb10, pos sobre
  M, peak 30, cutoffs congelados) + histerese K_up/K_down + flush override 15M (D_flush·ATR15 do
  running-peak do run, rec=5×mom).
- `leg_phase` 15M nativo (PROVISÓRIO mid-grid, REPORT-ONLY) · `retr_fam` com UNDEFINED pré-1ª perna
  (C8) · âncoras publicadas no flip com t_known · estados por barra com flag warmup (W=400).
- Causal por construção: leg_dir da barra t usa último bucket 1H FECHADO < hora de t; extremos =
  running extremes; ZERO conf_i/pivô-por-rally (grep-clean); nenhuma feature de outcome.

## Verificação (escopo honesto — DA F0-F1.5 correção 3)
- **Truncation test: PASS 12/12**, MAS com escopo LIMITADO: o `Data` pré-computado é partilhado
  entre os dois lados, logo o teste certifica apenas a causalidade do LOOP do walk (runs/flush/
  phase/retr_fam) — NÃO certifica as camadas pré-computadas (rawleg 1H, macro, EMAs). Essas foram
  verificadas por INSPEÇÃO DE ÍNDICES (DA confirmou: rawleg[j] usa índices ≤ j; bucket 1H estritamente
  anterior à hora da barra; macro usa dia/hora estritamente anteriores; flush usa max_px pré-update).
- **Desvio declarado da spec §9.1** (200 timestamps + todos os known_at): corridos 12. Antes de F2 é
  obrigatório o truncation test VERDADEIRO (Data reconstruído na série truncada) nos known_at.
- Barras de entrada = 49.804 CLOSED do F0 (nunca a barra em formação).
- t_known das âncoras corrigido para o FECHO da barra do flip (t+900; era open = antedate de 15 min).

## Achado material: SEED DEGENERADO (flush override não transfere de escala)
Config seed (M15/K5/K5/D_flush2.0/mom24): **99,7% do tempo em LEG_DOWN, 11 pernas em 26 meses.**
Causa: D_flush em unidades ATR15 (2·ATR15 ≈ 0,25% do preço) dispara em QUALQUER pullback normal e
re-arma continuamente — o análogo v5 usa 6% do pico (≈30-60 ATR15). **Defeito da CLASSE apontada
pelo critical review (R1) e pelo DA da auditoria (ataque 6: thresholds não transferem entre escalas);
o defeito exato ATR15-vs-% não tinha sido previsto por ninguém — correção de citação exigida pelo DA
F0-F1.5 (correção 7).** Encaminhado ao estágio-1 do F1.5
(bounds GT-free) — ver F15 report e AMENDMENT A1. Nenhum ajuste silencioso foi feito.

## Confirmação negativa
Sem eventos como decisão · sem entry · sem indicadores · sem backtest · sem produção/Telegram/broker
· sem chart. leg_phase/retr_fam = REPORT-ONLY (defaults mid-grid declarados, não calibrados).
