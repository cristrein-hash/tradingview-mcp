# L2/BPT — LEITURA ESTRUTURAL CONVERGENTE TRADE-A-TRADE NOS 62 (canon efaf48a)

**2026-06-22.** Bloco fechado. Diagnóstico/calibração nos 62 (ensino), sob o canon metodológico permanente.
NÃO produção, NÃO 276/OOS, NÃO promoção, NÃO gate. outcome só na calibração (Tarefa 5), nunca predicado.

## 1. Escopo e canon aplicado
Reprocessei os 62 por prioridade causal: (0) causalidade as-of-bar/shift1; (1) D1/weekly macro backbone como
**contexto**; (2) **convergência multifatorial** (9 especialistas + 4 agentes cegos: Macro/MTF, Auction S-D,
Volumetria-SVP, Risk-SL-Exit); (3) risco/SL/exit como **eixo próprio**; (4) calibração por **tipo de saída**.

## 2. Por que isto NÃO é gate/fit/backtest
Não otimizei WR/sumR; não busquei feature/threshold novo; não usei realR capado como árbitro. Produzi uma
**leitura estrutural auditável por trade** (TAKE/REVIEW/SKIP/WATCHLIST + por que + o que invalidaria + o que é
resíduo). A convergência é interpretável (camadas por prioridade), não soma cega de votos.

## 3-4. Resultado da leitura convergente (4 agentes cegos + determinístico)
248 leituras de agentes (62×4 lentes). Distribuição final convergente:
- **TAKE_CANDIDATE 17 · REVIEW 31 · SKIP_STRUCTURAL 10 · WATCHLIST_TRANSFORM 4.**
- Concordância agentes vs leitor determinístico: 42/62 (divergências resolvidas pelo mais conservador estrutural).

## 5-6. Calibração por tipo de saída + convexidade (outcome SÓ aqui)
exitype por política: TAKE {7 HELD,1 RUNNER,4 BE,5 STOP}; REVIEW {14 HELD,7 BE,3 RUNNER,7 STOP};
SKIP {6 HELD,1 RUNNER,1 SCRATCH,2 STOP}; WATCHLIST {3 STOP,1 SCRATCH}.

**ACHADO CRÍTICO (não-mascarado):** `SKIP_STRUCTURAL` contém **7 outcome-winners** (S9,S13,S14,S15,S19,S26,T14,
incl. 1 monumental RUNNER S26 +3.9R). A calibração os separa:
- **OVER-FIRE genuíno: S9 (MACRO_BULL_LEG) + S26 (MACRO_RANGE/BULL, RUNNER +3.9R)** — contexto BULL, NÃO
  deviam ter sido SKIP. A convergência ainda erra para o lado conservador em bull. **Reclassificar → REVIEW/TAKE.**
- **Bear-context: S13/T14 (MACRO_BEAR_LEG)** ganharam mas Cris já os marca skip-aceitável = **beta/sorte**;
  **S14/S15/S19 (range/bear)** = bottom-reversals reais.
- **Lição (re-confirma [[project_l2_bpt_legbear_block]] RETRATADO + [[project_l2_bpt_telegram_bear_flags_FUTURE]]):**
  contexto bear-markdown deve ser **FLAG de veto humano**, NÃO `SKIP_STRUCTURAL` duro — o SL estrutural já
  administra o bear e o hard-block mata as V-reversals (a convexidade).

**Convexidade:** 32 big winners (RUNNER+HELD); **25/32 preservados**, 7 em risco no SKIP (2 over-fire + 5 bear).

**Tipos de trade (calibração):** structural_winner 7 (+1 monumental); good_entry_bad_SL_but_won 12 +
good_entry_bad_SL_stopped 3 (= o eixo risco isola corretamente "skip-que-deveria-ser-winner por gestão/SL");
good_entry_scratch_exit 4 (estrutura boa, saiu BE = falha de exit, não entrada); bad_context_won_beta 7
(beta/sorte); structural_take_stopped 5; review_won 12; review_loser_acceptable 4; acceptable_loser 3;
residual_late_top 4 (T17/T20/T24/T32 — TODOS perderam = resíduo auction-irredutível corretamente aceito).
**Estrutura explica o outcome: 19/62 totalmente, 43/62 parcialmente** (honesto, sem over-claim).

## 7. Camadas anteriores reinterpretadas sob o canon
`results/l2_bpt_prior_layers_reinterpreted_under_canon.csv` (13 camadas). Nenhuma descartada:
- D1-backbone+agents = camada 1 (contexto); Macro Engine v1 9-especialistas = camada 2 (núcleo de convergência);
  has-overhead/clean-sky/capit+rsi = **aspectos/flags** da camada 2 (nunca regra única); Bear-Leg Block v3 =
  reinterpretado como **flag de review humano** (não gate); entry-quality/leg-4H refutados = confirmam "separador
  é a leg + eixo risco, não a localização da entrada"; confluence-exhaustive p=0.167 = exemplo da busca
  superficial proibida; microstructure/target-7 = resíduo aceito.

## 8. O que mudou vs a abordagem superficial anterior
- Antes: gate binário sobre realR capado + sumR agregado como árbitro → matava convexidade e invertia.
- Agora: leitura por convergência + outcome só na calibração por tipo-de-saída → **expõe** que mesmo o SKIP
  "estrutural" mata convexidade (S9/S26) e que o eixo risco/SL isola os good-entry-bad-SL. Nada promovido.

## 9. O que continua irresolvido
- O `SKIP_STRUCTURAL` ainda over-fira em bull (S9/S26) e em bear-context winner-rico — a resolução correta é
  **human-review flag**, não automação (confirma o limite do auto-block).
- Estrutura explica só 19/62 totalmente; o resíduo late-top (T17/T20/T24/T32) permanece irredutível.
- Calibração nos 62 (ensino) NÃO é validação — o teste real é OOS bear (Opção B 2013-2016, já coletada).

## 10. Próximo passo recomendado
Apenas mediante autorização: NÃO criar gate novo; operacionalizar o bear-context como **flag de veto humano**
(telegram-bear-flags FUTURE) e validar o princípio no bear OOS (Opção B), por leitura estrutural, não por sumR.

Outputs: `results/l2_bpt_structural_reading_packets_62.csv`, `..._agent_readings_62.csv`,
`..._convergent_decisions_agents_62.csv`, `..._trade_calibration_62.csv`, `..._convexity_preservation_62.csv`,
`..._prior_layers_reinterpreted_under_canon.csv`, `..._da.csv`.
