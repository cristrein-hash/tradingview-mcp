# PRÉ-REGISTO — CAMADA DE CONTENÇÃO MACRO (CONTAINED) SOBRE O DETECTOR 4H

> Escrito 2026-07-12, ANTES de qualquer contenção rodar. STATUS: `PREREG_DRAFT — X/Y PENDENTES`.
> Ordem Cris: 1 camada nova acima do detector; se NÃO resolver, manter mente aberta para nova
> solução aproximada causal sem lookahead (registrado).

## Hipótese
Um estado lento `CONTAINED` (efficiency ratio com N longo sobre diário — mesma família do ER(15)
já existente no `raw_stable`; código reutilizado, muda o N) gateando o detector por cima
(`CONTAINED → RANGE`) colapsa a fragmentação em macro-range (zona cinza 2021-22: 18 flips,
38/30/30) e limpa as bordas do bear estrutural, SEM destruir os rótulos direcionais de 2024-25.

## Grelha de parâmetros (CONGELADA — lista fechada, não se acrescenta depois)
- `N_long ∈ {90, 120, 180, 250}` dias
- `θ_ER ∈ {0.10, 0.15, 0.20, 0.25}` (ER < θ por M dias consecutivos → CONTAINED)
- `M ∈ {5, 10}` dias de confirmação (anti-flicker)
Total: 32 combinações. Sem outras variantes.

## Critério de aprovação — **X/Y = DECISION_REQUIRED (Cris fixa à cega, antes do run)**
- Benefício: concordância nas janelas RANGE do GT congelado sobe ≥ **X** pp E flips na zona
  cinza caem ≥ **X'** % (baseline: 18 flips; churn RANGE_2021_22 = 1,07/100b).
- Custo: barras BULL nas janelas BULL do GT (2024-25 incl.) não caem mais que **Y** %.
- Aprovação em histórico longo: passar em ≥ **3 de 5** episódios pré-rotulados (abaixo).
- Métrica = intrínseca vs GT congelado `REGIME_GT_CRIS_4H_20260712.json` (sha 87f55af475a17f8e…,
  bordas ±3d excluídas). **NUNCA P&L**; L1/L2 entram UMA vez no fim como confirmação.

## Episódios a priori — histórico longo diário 2010-2026 (rotulados ANTES de rodar)
1. Bear 2011-2015 (teste: não fragmentar em bull falsos)
2. Macro-range 2013-2019 (~1150-1350) — o teste mais duro de contenção
3. Rally 2020 (teste de não-estrago)
4. Chop 2021-2022 (o defeito-alvo)
5. Rally 2024-2025 (teste de não-estrago; janelas BULL do GT)

## Pré-requisito de DADOS — BLOQUEADOR
Diário XAU 2010-2026 NÃO existe no repo (RAW 4H começa 2019-12-31). Fonte a autorizar pelo Cris:
(a) coleta via MCP `data_get_ohlcv` D com paginação from_time/to_time (requer scroll de histórico
no chart), ou (b) outra fonte RAW aprovada. Sem dados longos, o teste roda só 2020-26 = N≈1,5
episódios de range (validação fraca — declarado).

## Proibições
- Não mexer no `raw_stable`/histerese/override (camada validada, causal pós-fix 67bb7ef).
- Não fitar o BEAR de nov/2024 nem o lag de V-turn (1 episódio cada = overfit; limitações declaradas).
- Falhou o critério → falhou; nova hipótese exige NOVO pré-registo (baliza não se move).
