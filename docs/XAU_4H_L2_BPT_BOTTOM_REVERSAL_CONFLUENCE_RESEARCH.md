# XAU 4H L2/BPT — Bottom/Reversal Confluence: PARTE 0 + TESTE A (resultado)

**Status:** `RESEARCH · CAUSAL · RAW · TESTE-A-ONLY · LEAD (not confirmed) · NO_PRODUCTION` · **Data:** 2026-06-18
Executa SÓ o escopo autorizado: Parte 0 (RAW audit dos componentes) + Teste A (o ESTADO tem edge vs legpos-random?). **NÃO** mediu H-CONV/Test B/H-RETRACE/H-NODIV. Sem tunar K/θ/janelas. RAW, sem look-ahead, sem plotagem. Script: `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/botrev_part0_testA.py`. Foundation: [[XAU_4H_L2_BPT_BOTTOM_REVERSAL_CONFLUENCE_PREREG]] · [[XAU_4H_L2_BPT_ENTRY_DEEP_REFLECTION]].

---

## 1. Correção crítica desta rodada
NAS foi inicialmente (erro) deferido como "não-causal no frozen". **CORRIGIDO:** NAS LONG extraído causalmente por **first-appearance no gz** (detector "NAS TOP BOTTOM DETECTOR"; `nlong>prev` por snapshot; mesmo método de `extract_1d_v3.py`), na **mesma passada do demand/OB**. Ver [[feedback_nas_long_short_never_top_bottom]].

## 2. Parte 0 — RAW audit (universo 9724 barras, todos causais)
| componente | fonte | causal | cobertura |
|---|---|---|---|
| drop20≥4ATR (capitulação) | frozen OHLC | ✓ | 984 (10%) |
| rsi_min_8≤30 (oversold) | frozen RSI Wilder | ✓ | 1033 (11%) |
| ≥2 bubble_SELL/8b | frozen bubbles_recent plot6/8/10 + bars_ago | ✓ | 2214 (23%) |
| demand abaixo ≤5ATR | gz OB Detector as-of-bar | ✓ repaint-auditado | 9386 (97%) |
| legpos90<75 | frozen OHLC | ✓ | 6350 (65%) |
| **NAS LONG novo/8b** | **gz NAS TOP BOTTOM first-appearance** | **✓ (replay bar-a-bar)** | 652 (7%); total nas_new=134 |

## 3. Teste A — o ESTADO tem edge? (vs legpos-random demand-backed, mesma mecânica demand-SL + partial50)
**Unidade canônica = EPISÓDIO** (dedup gap>6; bar-level super-estima por correlação serial).

| variante | unidade | n | avgR | W/S/SC | rand50 | delta | P | veredito |
|---|---|---|---|---|---|---|---|---|
| STATE_5 (sem NAS) | bar | 417 | +0.131 | 139/242/36 | 0.056 | +0.075 | 0.849 | sem edge |
| STATE_6 (+NAS i) | bar | 199 | +0.390 | 76/107/16 | 0.049 | +0.341 | 0.998 | (inflado) |
| STATE_6 (+NAS i-1) | bar | 184 | +0.369 | 70/102/12 | 0.051 | +0.318 | 0.996 | (inflado) |
| **STATE_5 (sem NAS)** | **episódio** | **56** | +0.210 | 22/31/3 | 0.056 | +0.154 | **0.759** | **sem edge** |
| **STATE_6 (+NAS i)** | **episódio** | **34** | +0.437 | 12/16/6 | 0.043 | +0.394 | **0.917** | **sugestivo** |
| **STATE_6 (+NAS i-1)** | **episódio** | **31** | +0.544 | 12/13/6 | 0.040 | +0.504 | **0.951** | **sugestivo** |

Bonferroni rodada (3 variantes) → exige **P≥0.975** p/ EDGE confirmado.

## 4. Leitura honesta
- **O estado SOZINHO (5 sinais) NÃO tem edge** (P 0.76 episódio). Contraria a expectativa "SIM por Caminho B" — a convergência estrutural pura é ~drift.
- **NAS LONG é o discriminador.** Adicioná-lo dobra o delta (+0.39/+0.50) e é **shrinkage-independent** (apertar capitulação sozinho NÃO reproduz +0.34 — DA verificou: drop20≥5.5 vira −0.067). É sinal real, não artefato de n menor.
- **A versão causal i-1 é MAIS forte** (P 0.951 vs 0.917) → remover os 31% de fires da própria barra de entrada AJUDA — afasta o risco de repaint do label de entrada.
- **MAS nenhuma variante clear o gate 0.975.** É **LEAD, não edge confirmado**: 34 episódios, 16/34 negativos, 59% do R em 3 episódios, concentrado em ~67 dias-calendário em 6 anos.
- **P=1.00 bar-level era artefato** de tratar 199 barras correlacionadas como IID (DA: primary concern, confirmado).

## 5. Devil's Advocate (agentId a3b32d7133c5ff511) — verdito
Bar-level P=1.00 = artefato (199 bars = 34 episódios = 67 dias). Episódio P=0.917 < gate 0.975 e < 0.95 naive. NAS lift é genuíno e shrinkage-independent (sobrevive), mas em 34 episódios metade negativos, 59% do R em 3. i-1 causal não destrói (até melhora) → repaint não é o motor, mas os 62 same-bar fires precisam de auditoria de timestamp gz antes de promoção. **Não promover. Lead que exige episódio + NAS-i-1 + split temporal.**

## 6. Recomendação (dentro do escopo)
- **Veredito Teste A:** o estado de convergência **com NAS** é um **LEAD sugestivo** (P 0.92–0.95 episódio, causal i-1), não edge confirmado. Sem NAS = sem edge.
- **NÃO promover, NÃO plotar, NÃO produção.** Não medir H-CONV/Test B sem autorização.
- **Próximo re-teste (se Cris autorizar):** split temporal 2020-22/2023-26 do STATE_6_NAS_i-1 (a edge não pode morar só nos 3 top episódios); auditar timestamp gz dos same-bar fires; e então H-CONV (Test B: o reclaim BOS adiciona sobre o estado, vs random-no-mesmo-estado).

---
*Saídas: `results/l2_bpt_botrev_raw_audit.csv` + `results/l2_bpt_botrev_testA.csv`. Causal ✓, RAW ✓, sem SLIM/look-ahead/plot/produção, nada promovido. DA obrigatório executado.*
