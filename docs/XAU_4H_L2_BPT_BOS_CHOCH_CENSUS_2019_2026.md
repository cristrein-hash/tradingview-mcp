# XAU 4H L2/BPT BOS-CHoCH — Mechanical Census 2019-2026

> 🚨 **CENSO NULO — recall não verificado antes (erro 2026-06-17).** O detector v1 recaptura só **2/17** dos GT BOM_HIGH (e esses 2 viraram losers). O resultado net-negativo abaixo **NÃO testa o conceito** — testa um detector que descarta os winners-alvo. Ordem correta era recall-gate vs Ground Truth ANTES do backtest (ver `feedback_recall_gate_before_backtest`). **Tratar tudo abaixo como nulo até o detector recapturar a maioria dos 16 BOM.**


**Data:** 2026-06-17 · **Tipo:** censo/reconstrução mecânica · **RECONSTRUCTION_CENSUS / MECHANICAL_BASELINE / HYPOTHESES_ONLY (NÃO validação final).**
**Fonte:** RAW replay `.gz` ONLY (extractor auditado in-memory; **zero slim**). Gross R, **sem custos**. Sem MCP/plot/Telegram/produção. Nenhum ajuste humano nas métricas mecânicas.

---

## 1. Executive summary

Censo mecânico puro da entrada estrutural L2/BPT (CHoCH → polaridade → retest → reclaim → SL estrutural → +2/3/4R) em 2019-2026, RAW. Após corrigir o engine (fix do DA: SL ancorado no **low do retest**, não no PL profundo da origem da perna — o manifesto §1.9 tinha o termo "low recente" que o código v1 havia omitido), o funil produziu uma **população real (53 entries)**.

**Resultado honesto: net-NEGATIVO gross.** R3: n=53, WR 26%, **sumR −9.7R, PF 0.75, DD −21.3R, streak 11** (R2/R4 igualmente negativos). Positivo só em **2023-2025** (bull recente); negativo 2019-2022 + 2026. **A entrada estrutural pura, mecânica, NÃO mostra edge** — consistente com o conhecimento preservado L2 ("o que separa good/bad é gestão/contexto, não o filtro de entrada").

**Onde as perdas concentram (tags, small-n):** **inside_supply 12/12 losers (−12R)** e **nas_short_recent 44 (−10.4R)** — entrar com supply overhead / em contexto de topo (NAS SHORT recente) mata. Removendo inside_supply, o resto (41) fica **~breakeven (+2.3R, PF 1.09)**. Isso aponta a camada de **contexto/overlay** (supply, at_D1_demand, Reason Atlas, exhaustion) como onde a separação pode estar — a ser medida **separadamente** (não misturada no mecânico). **DA: engine causalmente SOUND; resultado inconclusivo-negativo; n e detector com caveats.**

---

## 2. Gate manifest
`my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/gate_manifest.md` (estrutura SMC congelada; overlays = tags).

## 3. RAW mapping
`.../v1/raw_field_mapping.md` (RAW-only; at_D1_demand DEFERIDO no census v1 = `tag_pending`).

## 4. Universo
XAUUSD 4H LONG, 2019-01-01 → 2026-05-22, **11.182 barras** (RAW, audited extractor in-memory).

## 5. Candidate funnel
| Etapa | n |
|---|--:|
| CHoCH detectados | 240 |
| BOS detectados (tag, não-entry em v1) | 211 |
| episódios com retest | 186 |
| episódios com reclaim | 136 |
| **entries** | **53** |
| no-trade: R_ceiling_abort (>1.5ATR) | 83 |
| no-trade: no_retest | 54 |
| no-trade: no_reclaim | 22 |
| no-trade: invalidation (close<leg-origin low) | 28 |

## 6. Métricas (gross, no-overlap por episódio)
| Target | n | WR | sumR | avgR | medR | PF | maxDD | streak | tgt/stop/time |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| R2 | 53 | 30.2% | −9.7 | −0.18 | — | 0.74 | −14.3 | 9 | 13/37/3 |
| R3 | 53 | 26.4% | −9.7 | −0.18 | −0.40 | 0.75 | −21.3 | 11 | 9/39/5 |
| R4 | 53 | 26.4% | −8.8 | −0.17 | −0.40 | 0.78 | −22.5 | 11 | 6/39/8 |

**Net-negativo em todos os targets.** Sem BE neste census.

## 7. Year breakdown (R3, sumR)
2019 −1.0 · 2020 −7.0 · 2021 −4.3 · 2022 −4.0 · **2023 +1.0 · 2024 +5.2 · 2025 +2.4** · 2026 −2.0. → negativo nos anos bear/chop, positivo só no bull recente (2023-2025).

## 8. Target comparison +2R/+3R/+4R
Todos negativos; R4 levemente menos ruim (PF 0.78) por capturar runners raros. Nenhum target salva a baseline.

## 9. Tag breakdown (R3, TAGS — small-n, hypotheses-only)
| Tag | n | WR | sumR | PF |
|---|--:|--:|--:|--:|
| inside_supply | 12 | 0% | −12.0 | 0.0 |
| not_inside_supply | 41 | 34% | +2.3 | 1.09 |
| inside_demand | 4 | 0% | −4.0 | 0.0 |
| nas_short_recent | 44 | 25% | −10.4 | 0.69 |
| nas_long_recent | 32 | 31% | +0.9 | 1.04 |
| bubble_large_buy | 3 | 0% | −3.0 | 0.0 |
| rsi_div_bearish | 1 | 100% | +3.0 | — |

**Sinal direcional (não-conclusivo):** supply overhead e NAS-short-recent (topo) concentram as perdas; sem eles a baseline ~breakeven. **at_D1_demand não medido (deferido).**

## 10. Mechanical vs visual-review (separados — métrica mecânica NÃO ajustada por humano)
`results/l2_bpt_census_review_queue.csv`: **9 mechanical_winner · 5 mechanical_small_win · 39 mechanical_loser_coherent** (todos losers saem por stop = coerentes; 0 incoerentes). A camada visual/contexto fica **separada**, a ser medida depois — não entra na métrica mecânica (anti-hindsight).

## 11. Main winners/losers
9 winners (R3≥+3R via target) concentrados em 2024-2025; 39 losers coerentes (stop), concentrados em supply-overhead/NAS-short. Listas em `results/l2_bpt_census_trades.jsonl` + `review_queue.csv`.

## 12. O que é promissor
- O funil agora é saudável (53 entries, fix do SL aplicado).
- **Camada de contexto** (excluir supply-overhead / NAS-short-topo) leva a baseline de net-negativo → ~breakeven — candidato a overlay (a medir separadamente, n pequeno).
- 2023-2025 (bull) positivo — possível dependência de regime.
- at_D1_demand / Reason Atlas / S2-S3 BOS-path ainda **não testados** (potencial não explorado).

## 13. O que NÃO está provado
- **Nenhum edge** (baseline net-negativa gross). n=53 pequeno.
- Tags (supply/NAS) são small-n (12/44) — não conclusivas.
- Detector v1 = aproximação (contexto bearish frouxo; **BOS-path S2/S3 não usado**; R_ceiling ainda aborta 83 retests profundos).
- Gross/sem custos/sem OOS. Census ≠ validação.

## 14. Plot sets recomendados (NÃO plotados)
- 9 mechanical winners; 39 coherent losers (supply/NAS contexto); review_queue; os 83 R_ceiling-aborts (ver por que o stop estrutural fica fundo).

## 15. Devil's Advocate (spawn incorporado)
DA auditou o engine nesta sessão: **causalmente SOUND** (pivots SHIFT5 confirmados só em j+5; protected_LH/polaridade/CHoCH/BOS de pivots confirmados; entry reclaim-close; sim i+1; RAW-only). Achou o colapso do funil (6 entries) = **mismatch manifesto-vs-código** (SL omitiu o termo "low recente") → **fix aplicado** (SL=retest low) → 53 entries. Caveats remanescentes: contexto bearish frouxo (infla CHoCH), BOS-path S2/S3 não-usado (suprime entries com SL mais viável), n=53 pequeno, gross/sem custos, tags small-n.
- ✅ Sem SLIM · CHoCH/BOS causal · Williams SHIFT5 · protected_LH causal · retest/reclaim sem futuro · SL R-bounded · **nenhuma visual review alterou a métrica** (camada separada) · métricas NÃO chamadas de validação (census/negative) · nenhum threshold otimizado (fix foi correção de definição vs manifesto, não tuning) · sem MCP/chart · produção intacta · L1 intacta · Caminho B não recomendado.

**DA verdict: PASS — census mecânico executado, engine causalmente sólido, resultado net-negativo/inconclusivo (hypotheses-only); edge da entrada pura NÃO demonstrado; contexto/overlay e BOS-path são as frentes não exploradas.**

---

*Read-only. RAW-only (zero slim). Gross, sem custos, sem OOS. Outputs: `results/l2_bpt_census_{summary.json, review_queue.csv}` (tracked); `{trades.jsonl, plot_ready.csv}` (gitignored, regeneráveis). Nenhuma plotagem. Census ≠ validação final (esta exige regra congelada + OOS/forward).*
