# XAU 4H L2/BPT — Visual Discrimination Taxonomy (mecanismo, não presença)

**Status:** `VOCABULARY · MECHANICAL_FIRST_PASS · NOT_STRATEGY · NOT_VALIDATION · VISUAL_CONFIRM_PENDING` · **Data:** 2026-06-17
**RAW-only · sem backtest/PnL/filtro final/Caminho B/SHORT/SLIM.**

> **Honestidade de escopo:** eu **não inspecionei os 41 episódios um a um** (não tenho o gráfico, só os prints do Cris). O que segue NÃO é "classificação visual minha" — é uma **operacionalização mecânica** do mecanismo que o Cris leu nos prints, com **uma primeira-passada de categoria por episódio marcada `visual_confirm=PENDING`** para o Cris confirmar/corrigir no chart. A categoria de verdade é o olho do Cris; aqui só meço proxies causais que apoiam essa leitura.

---

## 1. A tese (leitura do Cris)

Não basta haver supply/demand. O que separa é **como o preço interage com a supply/demand depois do BOS/retest**: **aceitação vs rejeição**.
- **BOM provável:** rompe → **aceita** acima/na supply → retesta sem perder estrutura → continua.
- **NAO provável:** rompe no topo → **rejeita** na supply → perde reclaim/polaridade → vira bear leg.
- Supply perto **não** é veto bruto (perto + absorção pode ser bom; perto + rejeição é perigoso).
- O maior perigo não é "supply perto" — é **comprar repique dentro de bear leg**.
- O discriminador medível que faltava: **`acceptance_after_reclaim`**.

## 2. `acceptance_after_reclaim` (a métrica nova, agora medida)

Definição operacional (causal, sem futuro além da janela de avaliação): após fechar acima da polaridade,
- **held:** nos próximos 2–4 candles **não fecha abaixo** da polaridade; **OU**
- **HH/HL:** faz higher-high mantendo low ≥ polaridade.
`acceptance = held OR hh`. É o eixo central das categorias abaixo.

## 3. Taxonomia (9 categorias por MECANISMO)

| categoria | definição | confirma entrada | invalida entrada | seems |
|---|---|---|---|---|
| **ACCEPTED_SUPPLY_BREAK** | rompe supply e aceita acima | fecha e segura acima da supply rompida; HH/HL | volta a fechar abaixo | BOM |
| **POLARITY_DEFENDED** | retorno à polaridade e segura | 2–4 closes acima da polaridade | close abaixo da polaridade | BOM |
| **DEMAND_SUPPORTED_RECLAIM** | reclaim apoiado por demanda útil | retest toca demanda e defende; reclaim verde aceito | perde a demanda | BOM |
| **BEAR_LEG_RECLAIM_TRAP** | compra repique dentro de bear leg | (sem confirmação válida) | continua a perna de baixa / LL | NAO |
| **TOP_SWEEP_REJECTION** | varre topo e rejeita | (invalida) | reverte após o sweep | NAO |
| **SUPPLY_REJECTION** | bate em supply e falha | (invalida) | rejeição confirma topo | NAO |
| **LATE_EXTENDED_ENTRY** | entrada tarde, perna madura | precisaria pullback/retest | reverte sem retest | ambíguo |
| **GENERIC_BULL_DRIFT** | sobe por drift, não por setup | só vale com estrutura real | perde estrutura quando o drift para | ambíguo |
| **NEEDS_SECOND_REVIEW** | ambíguo | olho humano | — | ambíguo |

## 4. Perguntas obrigatórias (por episódio, no CSV)

O preço aceitou acima da supply ou rejeitou? · A polaridade foi defendida? · O reclaim segurou ou falhou? · Bull leg ou bear leg? · Valor ou tardia? · Há TOP cluster de exaustão? · Supply bloqueia ou foi absorvida? · Demanda apoia ou está longe?

## 5. Primeira-passada mecânica (`results/l2_bpt_visual_episode_labels.csv`)

Distribuição (41 episódios, `visual_confirm=PENDING`):

| categoria | n |
|---|--:|
| DEMAND_SUPPORTED_RECLAIM | 15 |
| POLARITY_DEFENDED | 10 |
| TOP_SWEEP_REJECTION | 6 |
| BEAR_LEG_RECLAIM_TRAP | 6 |
| ACCEPTED_SUPPLY_BREAK | 3 |
| SUPPLY_REJECTION | 1 |

**seems:** 28 BOM_real_candidato · 13 NAO_real. O eixo `acceptance` separa: os 13 "NAO_real" são exatamente os de **rejeição/sem aceitação** (BEAR_LEG_RECLAIM_TRAP + TOP_SWEEP_REJECTION + SUPPLY_REJECTION).

## 6. Caveats da primeira-passada (a confirmar no olho)

- **`bear_leg` é um proxy cru** (close<SMA20 OU first_retomada/bear_flag): dispara demais em 2020 (ex.: E1 = fundo do crash COVID marcado bear_leg+demand) — o Cris é o árbitro de "bear leg real" vs "pullback em bull".
- `acceptance` usa janela 2–4 candles; casos de aceitação lenta/atrasada podem ser mal-classificados.
- `TOP cluster` = NAS-short≥6 recente (proxy de exaustão), não leitura de absorção vs distribuição — que exige o que vem **depois** (aceitação).
- E40 (que o Cris anotou "desperdício de BIG WINNER / SL estrutural mais largo") saiu DEMAND_SUPPORTED_RECLAIM — consistente com setup real cujo problema é gestão de SL, não a entrada.
- Tudo small-n e mono-regime (34/41 em 2020) — **vocabulário**, não regra.

## 7. Como usar

1. Cris abre o CSV e, episódio a episódio no chart, confirma/corrige `visual_category` (preenche `visual_confirm`).
2. Com os labels confirmados, a próxima medição cruza **categoria × outcome real** (stop estrutural + R, por episódio, lift vs base rate) — para ver se as categorias de mecanismo separam o que as métricas genéricas não separaram.
3. Só então (bloco separado, autorizado) considerar uma camada de qualidade baseada em `acceptance_after_reclaim` + `bear_leg` real.

## 8. DA appendix

- Não rodou backtest / PnL? ✅ (só classificação + acceptance medido, sem outcome simulado aqui).
- Não criou filtro/regra final? ✅ vocabulário, PENDING.
- Não fingiu leitura visual? ✅ explicitado: primeira-passada mecânica, `visual_confirm=PENDING`.
- Não promoveu como estratégia? ✅. SLIM/Caminho B/SHORT? ❌ nenhum.
- Produção intacta? ✅.

**DA verdict: PASS — taxonomia de mecanismo formalizada; `acceptance_after_reclaim` medido (eixo que faltava); primeira-passada mecânica entregue como PENDING para confirmação visual do Cris, sem fabricar leituras; nada promovido.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_visual_episode_labels.csv` (41 episódios, 9 categorias, perguntas, `visual_confirm=PENDING`). Script: `visual_taxonomy.py`.*
