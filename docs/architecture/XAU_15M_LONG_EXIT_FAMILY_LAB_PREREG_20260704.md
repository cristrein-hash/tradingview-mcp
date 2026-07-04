# EXIT FAMILY LAB · PRÉ-REGISTRO (2026-07-04, ANTES da medição formal)

**Bloco:** XAU_15M_LONG_EXIT_FAMILY_LAB · research-only / LONG-only · sem produção/chart/RAW-write. Pergunta: o exit `let-run trail` (componente da stack APROVADA) está suprimindo convexidade? O cruzamento exploratório (`entry_exit_cross_20260704.py`, **1 look de descoberta declarado**) apontou BASE435 +234,3→+316,7 sob trail-pós-3R. Este lab = medição FORMAL dos MESMOS 4 exits — **zero exits novos, zero thresholds novos** (adição = novo look; proibido).

## 1. Scope
Entradas FIXAS (nada muda nelas): **BASE435** (primário — stack aprovada) e **SISTEMA_A_53** (secundário, EXPLORATORY). SL de cada set inalterado. Detector/gates intocados. SB $0,80 obrigatório. **Adoção de qualquer exit = decisão do Cris depois** (exit é stack OFICIAL_FN; este lab só mede).

## 2. Família de exits CONGELADA (4; a mesma do cruzamento)
- **E0 trail padrão** (baseline oficial): trail=SL; após +1R, trail=max(trail, fractal-low[≤k−2, 120b] − 0,1ATR); HMAX480; RCAP20.
- **E1 trail-pós-3R**: idêntico, mas trail só arma após +3R.
- **E2 alvo fixo 3R** first-touch (same-bar ambíguo = −1, conservador); sem trail.
- **E3 alvo fixo 5R** idem.

## 3. Métricas (por exit × set)
Painel duplo bruto+NET (N/WR/sumR/avgR/DD/r-DD/streak) · por-ano · pior mês/semana · runners R≥3/R≥5 · retention vs E0 · FN-proxy (WR≥50 · stk≤6 · DD) · **delta PAREADO por trade vs E0** (soma, IC bootstrap 95% por reamostragem de EPISÓDIOS 1000×, sub-janelas por ano — consistência exigida) · jackknife-episódio e por mês (nenhum mês >35% do delta) · **streak/DD DISTRIBUCIONAIS** (bootstrap por blocos de episódio 1000×, q95) — canon: streak observado nunca é árbitro sozinho.

## 4. Leituras proibidas
Não escolher "melhor exit" por sumR isolado (painel completo sempre; viabilidade operacional/streak = árbitro de 1ª classe) · não recomendar adoção (decisão Cris) · não tocar SL/entradas/detector · não adicionar exits/thresholds · não esconder o trade-off FN (WR/streak pioram nos convexos — reportar em destaque).

## 5. Outputs
`exit_family_lab_20260704.py` · `results/exit_family_lab_{results.csv,summary.json}` · DA independente antes do report · report com veredito ∈ {EXIT_VARIANT_MATERIAL_TRADEOFF, EXIT_VARIANT_DOMINATES, NO_MATERIAL_EXIT_EFFECT} · commit `"Evaluate XAU 15M exit family on approved base"` — sem push sem autorização.
