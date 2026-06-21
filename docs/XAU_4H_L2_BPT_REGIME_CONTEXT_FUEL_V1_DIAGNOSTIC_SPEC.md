# BLOCO REGIME/CONTEXT/FUEL v1 — DIAGNOSTIC SPEC (consolidado + aprovado)

**2026-06-21.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. **Diagnóstico causal apenas.** Consolida o plano pré-execução
aprovado pelo Cris (9 decisões) + 8 ajustes obrigatórios. Sucessor do regime_diag_v0 (univariado, primeira
passada, commit c89ba8c — NÃO é conclusão final; entra só como baseline a superar). **Objetivo = estrutura
causal AUDITÁVEL e PROFUNDA**, não threshold rápido.

---

## 0. Natureza da sessão (aprovado)
- **Diagnóstico causal / reverse-engineering.** NÃO é engine multiagente rodando. NÃO é aggregator rule. NÃO é validação.
- **Ground-truth:** `visual matrix v0 + veredictos Cris = CALIBRATION ground-truth, sujeito a DA anti-hindsight e validação posterior` (NÃO "a verdade"; NÃO validação final).
- **Resultado:** hipótese causal **calibrada**, não feature validada/promovida.

## Travas (invioláveis)
Não rodar v2 · não promover feature/gate/regra · **não transformar o diagnóstico em v2/gate/rule/promoted-feature/
engine-change** · não alterar engine/decisions_merged/registry/library/produção/Telegram/chart-MCP/SLIM ·
**nenhuma regra candidata usa outcome/realR/exit_type/MFE/candle-futuro** · não confiar em Stage A / macro_leg /
regime_B_v3 / regime_l1_v4 pelo NOME — testar comportamento real.

---

## 1. Como o engine é aplicado (componentes — aprovado)
| Componente | Uso |
|---|---|
| visual matrix v0 + veredictos Cris | **LABELS** (calibration ground-truth, sujeito a DA anti-hindsight) |
| 84-factor packet | **FONTE de features** causais |
| externas (regime_B_v3, l1_v4, daily/weekly) | **FONTE adicional** — testadas por comportamento, com provenance |
| scripts estatísticos | **MÉTODO de descoberta** |
| Stage A | só **feature sob teste** (nunca label/verdade) |
| especialistas/evidence/aggregator/DA-agent/multiagente | ❌ NÃO re-rodados (já produziram A/B upstream, congelado) |

O *produto* (se emergir leitura de contexto) alimentaria o engine **DEPOIS** como camada de medição — **bloco futuro, não este**.

## 2. Representação macro/contextual — 7 EIXOS CAUSAIS (contextos são SAÍDAS, não inputs)
| Eixo | Features candidatas (conhecíveis na entrada) | Distingue |
|---|---|---|
| **A. Frame macro D1** | dist_d1_supply/demand_atr, has_d1_*, rsi_1d, regime_B_v3/l1_v4 (SHIFTadas) | macro bull/bear; pre-bullrun vs corrective |
| **B. Frame local 4H** | dist_4h_supply/demand_atr, legpos30/60/90, dist_sma50 | continuation vs bounce; posição na perna |
| **C. Momentum/trend** | trend_30/90_atr, slope20, rsi, rsi_1d_sub_ma | markup forte vs bounce fraco |
| **D. Qualidade de supply (overhead)** | has_4h_supply_overhead, supply_blocks_2/3ATR, supply_broken_before, supply_rejected_before | ⭐ no-overhead-bullish vs supply_colada-bearish |
| **E. Qualidade de demanda** | demand_age/width/origin_of_leg/touched_on_retest, dist_demand | reclaim legítimo vs frágil |
| **F. Fuel/convexidade (gradiente)** | room-to-next-supply, dist_d1_supply, va_width | big winner vs dispensável |
| **G. Timing/reclaim + risk_sl (eixos C-set)** | reclaim_body/dist, sl_atr, sl_type | entrada cedo/tarde; SL curto |

**Modelo multiplicativo:** contexto = combinação de eixos. O mesmo `dist_supply` baixo é bullish ou bearish conforme o eixo D.

## 3. Anti-erros (condicionais/interacionais — aprovado)
- **legpos** nunca monótono "alto=ruim" → interação `legpos × momentum × eixo D`.
- **dist_supply** nunca monótono "baixo=fuel fraco" → combinado com D (`has_overhead`/`broken_before`): resolve no-overhead-bullish vs supply_colada.
- Stage A / macro_leg / regime_B_v3 / l1_v4: testados por comportamento (separa A/B?), nunca pelo nome.
- reclaim_body sempre com reclaim_dist + estrutura de demanda, nunca isolado.

---

## 4. Conjuntos A/B/C (aprovado — C fora do fit)
- **A** (~26): bull-run / bull_pullback / demand_reclaim CORTADOS errado (fatal-SKIP marcado PROTECT). S1,S3-8,S12,S13,S15-17,S20,S24-32,S34-38.
- **B** (~18): bear/corrective/late-top ACEITOS errado (novo-TAKE marcado BLOCK). T2-4,T9,T11,T12,T15-18,T20,T23-26,T30,T40,T42.
- **C** (separado, NÃO contamina fit A-vs-B): ambíguos/fuel/risk_sl/timing/dispensáveis. T34(risk_sl), T36(fuel), S39(fuel), S19(bear-skip ok), T27/S14/T40(timing). Reportado à parte.

## 5. Trades-âncora — critério QUALITATIVO, não overfit por ID (ajuste 2)
- **Must-preserve:** T34/T35/T37, S20, S24-S27, S29-S32, T39, T41, S35-S38.
- **Must-block:** T40, S40 (+ bear-pullback/late-top/corrective similares).
- **Formulação correta:** "preservar big winners **SALVO se o DA demonstrar que a preservação exige predicado não causal ou overfit**." A regra NÃO pode ser fitada aos IDs específicos — tem que ser interpretável (eixo de mercado) e generalizar.

## 6. Onde a leitura humana do Cris entra (planilha curta, anti-retrabalho)
Tags 1-por-trade onde os eixos conflitam: (1) no-overhead-bullish vs supply_colada (eixo D); (2) legpos alto saudável vs esticado; (3) range macro bull vs bear bounce; (4) pullback saudável vs corrective bear leg; (5) big winner vs dispensável (eixo F). Só nos casos conflitantes — não re-rotular tudo.

---

## 7. Metodologia (camadas — provenance ANTES de tudo)
**Camada 1 — Feature provenance (ajustes 5+6): PRIMEIRO, antes de qualquer scan.** Tabela por feature →
`fonte · timestamp · causal-no-bar-i? · exige-shift? · risco-look-ahead · derivada-de-visual/outcome? · 84-packet/externa`.
**Nenhuma feature entra sem isto. Nenhuma externa entra sem timestamp + shift causal + checagem look-ahead.**
Inclui: confirmar schema/timestamps de regime_B_v3/l1_v4/daily/weekly; provar empiricamente se macro_leg está morto.

**Camada 2 — Context taxonomy (curta, controlada; adaptar nomes canônicos do repo):**
bull_run_continuation · bull_pullback_continuation · demand_reclaim · bottom_reversal · capitulation_reclaim ·
range_macro_bull · bear_bounce · bear_continuation · late_top_exhaustion · corrective_bear_leg · mid_range_noise.
**São SAÍDAS dos 7 eixos**, não inputs.

**Camada 3 — A/B/C** (não contaminar; fit binário só A-vs-B).

**Camada 4 — Diagnostics:** univariado baseline → pairwise → multivariado simples → árvore/threshold com
**limite de complexidade (prof ≤3, folha ≥5)** → split temporal/held-out → shuffle-null → DA anti-overfit.

**Camada 5 — Engine interpretation (mercado, não "feature X separa"):** por que = bull-run legítimo? por que
bloqueia o trap? onde falha? quais big winners preserva? quais traps bloqueia? quais ficam ambíguos?
contextual/confluente ou threshold frágil?

## 8. Split temporal (ajuste 3)
Baseline: **2020-2023 (descoberta) / 2024-2026 (held-out)**. Também reportar **split reverso** e/ou
**sensibilidade por blocos** se viável. **Declarar explicitamente se n ficar pequeno demais** por bloco
(provável, dado n≈44 total) → nesse caso marcar "calibração sem held-out robusto".

## 9. Fuel (ajuste 4)
Nesta sessão fuel pode gerar **diagnóstico/tier** (gradiente). **NÃO criar política de position sizing ainda.**

---

## 10. Critérios de sucesso
Preserva big winners nomeados (salvo DA-overfit, §5) · bloqueia T40/S40-like · não penaliza legpos alto cego ·
não lê supply próxima como ruim cego · distingue no-overhead-bullish de supply_colada · distingue range-macro-bull
de bear-bounce · zero outcome/futuro · zero Stage A cego · zero regime-antigo-pelo-nome · sobrevive minimamente a
held-out/shuffle-null · melhora lucro esperado **sem matar convexidade**.

## 11. Riscos metodológicos (honestos)
n minúsculo (26/18, mesmo com held-out ~44) → pattern-matching: mitigar com interpretabilidade + shuffle-null +
"hipótese, não feature" · circularidade âncoras → split temporal · look-ahead externas → shift + Camada 1 ·
overfit árvore → limite complexidade · labels humanos → ground-truth sujeito a DA + held-out.

## 12. Outputs (quando autorizado — NÃO agora)
`results/l2_bpt_regime_v1_{provenance,feature_separation_full,pairwise,tree_rules,heldout,shuffle_null,setA,setB,setC,da}.csv`
+ relatório curto (baseline vs multivariado vs held-out; externas agregam ou não; candidato ou "precisa features novas").
Commit isolado **só após autorização + preflight**. Sem tocar engine/produção/decisions/registry.

## 13. Decisões aprovadas pelo Cris (2026-06-21)
9 pontos aprovados (natureza diagnóstica; ground-truth calibração; suspeitos por comportamento; contextos=saídas;
legpos/dist_supply condicionais; A/B/C; risk_sl separado; fuel gradiente; resultado=hipótese). 8 ajustes obrigatórios
incorporados (ground-truth ≠ verdade; âncoras qualitativas não-overfit; split temporal + reverso + sensibilidade;
fuel sem sizing; provenance antes do scan; externas com timestamp/shift/look-ahead; sem outcome em regra; sem virar v2).

**PRÓXIMO:** aguardar autorização explícita do Cris para EXECUTAR (Camadas 1→5). Este bloco entrega só o spec.
