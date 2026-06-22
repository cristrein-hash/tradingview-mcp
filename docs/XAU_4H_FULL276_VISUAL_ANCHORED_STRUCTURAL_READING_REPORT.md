# FULL 276 — VISUAL-ANCHORED STRUCTURAL READING (predicados causais congelados)

**2026-06-22.** Bloco fechado sob canon efaf48a. Diagnóstico na POPULAÇÃO completa 276. NÃO produção, NÃO OOS,
NÃO backtest bruto 2019-2026, NÃO promoção. outcome só na avaliação. Labels Cris NÃO usados como predicado nos 276.

## 1-3. Escopo, canon, por que 276 agora (não backtest bruto)
A leitura visual-ancorada dos 62 conserta o gargalo de regime, MAS é HUMANA e carrega hindsight (timeline macro
+ verdicts) — não-aplicável direto aos 276. Este bloco testa se o **APRENDIZADO CAUSAL** dessa leitura (supply-
lens corrigida, regimeB-não-autoridade, risk-axis, bear genuíno causal) se sustenta na população, **marcando
HUMAN_VISUAL_REQUIRED onde o julgamento visual não é reproduzível causalmente**. É verificação estrutural, não
backtest bruto (que viria depois, fora de escopo).

## 4. População 276 auditada
n=**276** (confirmado, não 267), datas 2020-01-14→2026-05-06, ts ordenados, 0 duplicados, 276 bar_idx únicos.

## 5. Predicados causais congelados (manifesto)
`results/l2_bpt_full276_visual_anchored_predicate_manifest.csv` — 12 predicados. CAUSAIS: D1 backbone, bear
genuíno (MACRO_BEAR_LEG), corrective-raso (drop<1.0), bear-confluence (broken+combined<0+weekly≤0), supply-lens
condicionada (bull=markup não-veta / bear=risco), regimeB-não-autoridade (não sobrepõe bull-leg), risk-axis
(sl>4 ou too-short→review), bottom-turn. HUMAN: ambiguous-bear (broken mas weekly subindo = T9-like),
micro-top-residual (range+legpos alto). clean-sky = flag.

## 6. Resultado cronológico (realR CAPADO = diagnóstico, não árbitro)
Distribuição: **TAKE 82 · REVIEW 92 · SKIP_STRUCTURAL 58 · HUMAN_VISUAL_REQUIRED 36 · UNKNOWN 8.**
Por bucket (hit-target = WIN_HELD+RUNNER):
- TAKE: hit 24, runners 5, WR 42.7%, sumR +24.5, PF 1.49, **45 STOP_LOSS**.
- REVIEW: hit 23, runners 7, WR 55.4%, sumR +44.4, **PF 2.08** (melhor que TAKE).
- SKIP_STRUCTURAL: hit 10, runners 3, PF 1.28 — bloqueia 10 big winners (3 runners).
- HUMAN_VISUAL_REQUIRED: PF 1.12 (≈ aleatório — corretamente o bucket ambíguo).
TAKE cronológico: maxDD 15.7, lose-streak 6, win-streak 4. baseline no-gate (276) sumR +84.2.

## 7. Comparação contra leituras anteriores
| sistema | n take/allow | big winners captados | runners captados | human_visual |
|---|---|---|---|---|
| baseline no-gate | 276 | 65 | 16 | — |
| Bear-Leg Block v3 (ALLOW) | 195 | 51 | 13 | — |
| **Visual-Anchored TAKE** | 82 | **24** | **5** | 36 |
**O visual-anchored TAKE captura MENOS convexidade que o bear_leg_v3** (5/16 runners vs 13/16; 24/65 vs 51/65) —
porque é conservador e empurra os bons winners para REVIEW (92) e HUMAN_VISUAL (36).

## 8. Confluência exaustiva (auditoria 2ª)
Sinais pré-especificados (clean-sky, no-near-supply, sup_cat) **TODOS NULOS** (lift ~0). Melhor 3-way
(bub_ratio≤1 & BULL & supply≥1, 20/21 losers, p=0.020) **REJEITADA**: null_max +0.503 > real +0.455, 18/21
ratio==0 (1 termo tick-volume), re-descobre volume×1D-bear RETRATADO. ⇒ **NO_PROMOTABLE_CONFLUENCE_FOUND.**

## 9. Error analysis
winners bloqueados em SKIP: 10 (incl. 3 runners). stops preservados em TAKE: **45**. O TAKE bucket carrega
muitos stops e poucos runners = seleção fraca pelos predicados causais.

## 10. Limitações (declaradas)
- **Humano visual AINDA necessário:** 36 HUMAN_VISUAL_REQUIRED + 92 REVIEW = 128/276 (46%) NÃO auto-decididos.
- **Predicados causais NÃO reproduzem a leitura visual** (confirma 62: ~32% non-reproducible). O TAKE causal é
  conservador; os bons winners caem em REVIEW (WR 55.4% > TAKE 42.7%).
- **realR capado +3.9R** → magnitudes = hit-rate, não expectancy.
- Thresholds do risk-axis (sl>4 / <0.7 ATR) = constantes de calibração dos 62 (não validadas indep.).
- 62 = ensino, não validação; OOS bear não no escopo.

## 11. Conclusão
**PARTIAL_HOLD / HUMAN_VISUAL_REQUIRED.** O aprendizado CAUSAL (supply-lens corrigida, bear-leg SKIP, bottom-turn)
**sustenta-se** parcialmente, mas a parte de REGIME/SELEÇÃO que distingue bull-run-bom de bear-junk/range
**NÃO é reproduzível causalmente** na população — ela depende do input VISUAL humano. O TAKE causal é conservador
e defere 46% a review/humano. Confirma o enquadramento já aprovado: **REGIME = input humano discricionário,
ENGINE = convergência auction/risco/exit por cima.** Nenhuma confluência promovível.

## 12. Próximo passo recomendado
NÃO promover. NÃO criar gate. O sistema operável que emerge é **human-in-the-loop**: o humano lê o regime
(visual), o engine faz auction/risco/exit nos casos causalmente claros (bull-leg TAKE, bear-leg SKIP, bottom-turn)
e marca HUMAN_VISUAL_REQUIRED no resíduo. Diagnóstico apenas; aguardo direção.

DA = PASS. Outputs: `results/l2_bpt_full276_population_audit.csv`, `..._visual_anchored_predicate_manifest.csv`,
`..._visual_anchored_reading.csv`, `..._summary.csv`, `..._equity_curve.csv`, `..._error_analysis.csv`,
`..._vs_prior.csv`, `..._confluence_audit_*`, `..._visual_anchored_da.csv`.
