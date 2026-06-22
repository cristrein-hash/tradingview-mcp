# FULL 276 — MACRO ENGINE REAL RERUN (9 especialistas) + INDICADORES EM TODA POTÊNCIA × ENGINE

**2026-06-22.** Rerun COMPLETO de verdade sob canon efaf48a, em resposta ao incidente 367c2e8 (gate superficial).
Engine de 9 especialistas REAIS (`macro_structural_specialists.py` portado verbatim ao 276) + confluência de
indicadores em toda potência cruzada por cima. DIAGNÓSTICO. Scripts SALVOS (reproduzível). 2 DAs executados.
realR CAPADO +3.9R = hit-rate. Sem produção, sem OOS, sem promoção.

## 0. O que foi feito (vs 367c2e8)
- `full276_macro_engine.py` — 9 especialistas REAIS invocados (supply/demand/volume/mtf/regime/momentum/capit/
  fuel/risk) + confluência interpretável → policy derivada da CONFLUÊNCIA multifatorial, não de feature isolada.
- `full276_indicator_confluence_cross.py` (v1) + `full276_indicator_confluence_v2_contextaware.py` (v2 corrigido).
- Validações: ablation (drop-1-specialist), null/permutation (N=2000), jackknife (leave-1-year-out), sub-janelas,
  drought-17. Tudo DENTRO dos 276. Scripts salvos e commitados.

## 1. Engine de 9 especialistas (sozinho) — NÃO SEPARA
| bucket | n | WR | PF | sumR | DD | Lstk | runners | big |
|---|---|---|---|---|---|---|---|---|
| ENGINE_TAKE | 141 | 24.8% | 1.58 | +44.3 | 18.1 | 14 | 8/16 | 35/65 |
| ENGINE_SKIP | 78 | **29.5%** | 1.95 | +36.8 | 6.6 | 14 | 5/16 | 23/65 |
| BASELINE no-gate | 276 | 23.6% | 1.58 | +84.2 | 18.7 | 28 | 16 | 65 |

**ENGINE_TAKE WR 24.8% ≈ baseline 23.6%. NULL/permutation p(WR)=0.374, p(PF)=0.493 = SEM separação de um
subset aleatório do mesmo tamanho.** ENGINE_SKIP tem WR MAIOR que TAKE = winners caindo no SKIP (o gargalo
recorrente persiste). **Ablation:** nenhum especialista carrega separação positiva; dropar `risk` AUMENTA big
winners 35→42 (o risk-axis remove winners); dropar `momentum` aumenta n 141→164. **Jackknife:** WR estável
~24-26% (estavelmente medíocre). **A leitura estrutural pura não distingue winner de loser neste alvo.**

## 2. Indicadores em toda potência × engine — v1 tinha BUG de polaridade
v1 codificou bub_sell e SMC_CHoCH como bear context-free. DA (afec87b) provou: 88% dos SKIP_CONFIRMED carregavam
BUBBLE_SELL + 77% CHoCH = a assinatura de **reversão-bull rotulada como bear** (viola `feedback_bubbles_polarity_rule`).
Os "winners no SKIP" da v1 eram artefato disso (n=48 WR 35.4% p=0.029 — separação na direção ERRADA).

## 3. v2 context-aware (polaridade corrigida) — artefato sumiu, mas SEM separação real
Polaridade condicionada ao contexto (TOP→distribuição bear; BOTTOM/PULLBACK→sell-bubble=clímax bull, CHoCH=gatilho bull).
| bucket | n | WR | PF | runners | null p(WR) |
|---|---|---|---|---|---|
| TAKE_CONFIRMED | 119 | 25.2% | 1.69 | 7/16 | **0.332** |
| +UPGRADE_TAKE | 126 | 26.2% | 1.79 | 8/16 | 0.138 |
| UPGRADE_TAKE only | 5 | 60.0% | 8.58 | 1 | 0.083 (n=5 ruído) |
| SKIP_CONFIRMED | 65 | 27.7% | 1.90 | 4 | 0.129 |
| DOWNGRADE_REVIEW | **0** | — | — | — | — |

- O fix **eliminou o artefato espúrio**: DOWNGRADE n→0, SKIP_CONFIRMED p 0.029→0.129. Confirma que era bug de polaridade.
- **MAS nenhum bucket TAKE separa**: TAKE_CONFIRMED p=0.332 falha nominal 0.05 E Bonferroni (m=5, α=0.010). Nenhum bucket sobrevive.
- **Correção honesta do DA:** SKIP_CONFIRMED ainda contém **18 winners (4 runners)** a WR 27.7% > baseline — o gargalo "winners no SKIP" é REAL e persiste; só o p-value espúrio morreu.
- **Sub-janelas:** P1 2020-22 WR 22.9% PF 1.35 vs P2 2023-26 WR 28.2% PF 2.12 = toda a aparência de edge é **beta-long-gold 2023-26** (não-estacionário, documentado).

## 4. Limitações vinculantes (DA — 2 confounds)
1. **Alvo capado +3.9R = hit-rate, NÃO expectancy.** Colapsa os 16 runners todos em +3.9R. Para uma estratégia
   runner-heavy (R:R alto justifica WR baixo) WR-sobre-R-capado é o objetivo ERRADO — não enxerga o valor do runner.
   Medir expectancy real exige **re-simulação de saídas com R não-capado** (bloco separado autorizado; o dataset
   atual não tem uncapped R).
2. **A polaridade dos indicadores é derivada do engine** (context_of lê macro_state/momentum/capit/family). Crosstab:
   TOP→73/74 SKIP, PULLBACK→135 TAKE. ⇒ a camada de indicadores é **parcialmente redundante com o engine**, não
   ortogonal — não pode adicionar informação independente quando sua polaridade é chaveada pela mesma leitura que
   deveria cruzar. Isso TETA o ganho possível do cross.

## 5. Conclusão honesta
**CONFIRMED_NO_SEPARATION.** Com o feature-set atual, o engine de 9 especialistas + confluência de indicadores em
toda potência (context-aware) **NÃO produz separação TAKE/SKIP automatizável** no alvo capado. Não é falha de
execução desta vez (engine real rodado, scripts salvos, DA 2x) — é um **achado real**: a edge não está na
confluência estrutural+indicadores sobre este alvo; o que parece edge é beta 2023-26.

**Isto NÃO conclui "parar no humano".** Conclui o que falta para AUTOMATIZAR a medição:
- **(a)** alvo de expectancy real (uncapped R), porque o valor de uma estratégia runner-heavy é invisível no hit-rate capado;
- **(b)** uma confluência de indicadores **ortogonal** ao engine (não derivada dele), senão o cross é redundante;
- **(c)** isolar P1 vs P2 sempre (nunca média agregada que esconde o beta 2023-26).

**Lead fraco (não promovido):** UPGRADE_TAKE = 5 SKIPs em contexto BOTTOM resgatados pela confluência de fundo
(3W/1scratch/1stop). n=5 = semente de hipótese para um teste de recall BOTTOM-context, não filtro.

## 6. Próximo passo de maior alavanca (DA)
Re-simulação UNCAPPED dos buckets existentes (TAKE_CONFIRMED, SKIP_CONFIRMED, UPGRADE_TAKE) com R de runner
completo, para testar se expectancy/valor-de-runner separa onde o hit-rate provadamente não separa — reportado
**por sub-janela P1 vs P2**. Requer autorização (gera outcomes novos). Não perseguir UPGRADE_TAKE (n=5) isolado.

DA = CONFIRMED_NO_SEPARATION (2 agentes: afec87b verdict + a3f87ff verificação v2). Outputs:
`results/l2_bpt_full276_macro_engine_*.csv` (confluence/specialist_evidence/policy_eval/ablation/null/jackknife/
subwindows/drought) + `..._indicator_engine_{cross,eval,null}.csv` (v1) + `..._{cross,eval,null}_v2.csv` (v2).
