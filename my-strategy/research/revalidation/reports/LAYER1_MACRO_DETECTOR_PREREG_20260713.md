# PRÉ-REGISTO — DETECTOR LAYER 1 (MACRO) · spec da máquina ANTES de codar

> Escrito 2026-07-13. STATUS: `PREREG_DRAFT` (aguarda validação do Cris antes de codar).
> GT: `REGIME_GT_LAYER1_CRIS_1D_20260713.json` (sha 3132690cfafee7e8; 16 janelas, ±5d, regra
> nested = bloco mais interno). Definição congelada: Layer 1 = regime que CONTÉM legs; SEM
> duração mínima (choque estrutural curto é macro válido). Métrica intrínseca, NUNCA P&L.

## Objetivo e o que Layer 1 NÃO é
Produzir, por barra, um rótulo MACRO {BULL, BEAR, RANGE} que persiste meses e CONTÉM as pernas
do leg v2 no interior. NÃO é o macro_at atual (curto ~15d = já é quase Layer 2). NÃO substitui o
leg v2. O detector 4H atual fica intocado; Layer 1 passa a ser a âncora macro que o leg v2 hoje
pega (mal) do detector 4H.

## Substrato de dados (RAW only, HD)
- 1D nativo `raw_1d_ohlc.jsonl` (2012-2026). Semanal = resample causal do 1D.
- Causalidade: rótulo do dia D conhecido a partir do fecho de D (convenção D_KNOWN já auditada);
  exposto no grid 4H por forward-fill (macro de D vale a partir de D+1). DA lookahead-only ANTES
  de medir. Zero repaint (máquina forward-only).

## Arquitetura da máquina (3 componentes; hipótese a validar)
A máquina é ela própria em camadas — reflete a estrutura que o GT mostrou (trend longo + range
aninhado + choque curto):

**(A) NÚCLEO DE TENDÊNCIA MACRO** — swings de ESCALA MACRO (meses):
- pivots por zigzag causal (máquina de ciclos já auditada) mas com reversão em ESCALA MACRO:
  `R_macro` medido em % do preço (não ATR curto) — ex.: reversão ≥ `p_rev`% confirma pivot.
- estrutura macro = HH/HL vs LH/LL sobre os últimos 2 pivots macro → BULL / BEAR.
- histerese FORTE (macro segura meses): confirmação `H_macro` (dias) antes de trocar.

**(B) OVERLAY DE CONTENÇÃO** — captura RANGE (inclui os aninhados dentro de BULL):
- Donchian longo (janela `W_don` dias): largura relativa ≤ `w_thr`·(preço) E posição do close no
  meio da banda → CONTAINED → rótulo RANGE, mesmo que o núcleo diga BULL/BEAR.
- resolve os 2 RANGE aninhados de 2024 dentro do BULL macro sem quebrar o BULL envolvente.

**(C) OVERRIDE DE CHOQUE ESTRUTURAL** — captura o macro curto (nov/2024, 7d):
- gatilho estrutural: drawdown/rally ≥ `s_thr`% em ≤ `s_days` dias no 1D (quebra decisiva).
- **confirmação exógena OBRIGATÓRIA** (a sonda de ontem separou nov/24 3×): só arma se o
  contexto exógeno concorda (DXY e US10Y na direção do choque, features causais já construídas).
  Sem exógeno, o choque curto NÃO vira macro (evita falsos choques em ruído de preço).
- este é o único caminho pelo qual um bloco de dias vira Layer 1 — coerente com "estrutural,
  não duração".

Prioridade de resolução por barra: **override de choque (C) > contenção (B) > núcleo (A)**.

## Grelha de parâmetros (FECHADA — lista pequena, anti-overfit)
- Núcleo: `p_rev ∈ {8, 12, 18}` % · `H_macro ∈ {10, 20}` dias
- Contenção: `W_don ∈ {60, 120}` dias · `w_thr ∈ {0.10, 0.15}`
- Choque: `s_thr ∈ {8, 12}` % · `s_days ∈ {8, 15}` · exógeno = ON (fixo, não varia)
Total = 3×2×2×2×2×2 = 96 combos. Nenhuma variante adicionada depois.

## Critério de sucesso (a fixar À CEGA antes de rodar — DECISION_REQUIRED)
1. concordância barra-a-barra vs GT Layer 1 (rótulo efetivo nested) — reportar agregado + por janela;
2. **os 5 BEAR** (incl. nov/24) detectados > `X`% cada — a SHORT depende disto;
3. não regredir: RANGE macro (incl. aninhados) recall ≥ `Y`%;
4. validação = k-fold purged/embargoed JUSTO (não split cronológico) + sonda-de-separação por
   componente ANTES de ligar cada um.
`X`, `Y` = Cris fixa à cega.

## Limitações declaradas (honestidade obrigatória)
- 16 janelas · 5 BEAR · nov/24 = 7 dias (n minúsculo). Poder estatístico BAIXO — igual ao aviso
  de ontem. O árbitro é concordância intrínseca + k-fold justo + não-regressão; P&L nunca entra.
- O override exógeno herda o limite do próprio exógeno (US10Y só desde 2003; features 20d).
- Alavanca opcional (Cris): marcar GT Layer 1 em 2012-2019 (1D nativo já extraído) para dobrar
  episódios BEAR e dar poder real ao critério 2.

## Proibições
Não tocar no detector 4H nem no leg v2. Nada commitado/adotado sem ordem. Falhou o critério →
falhou; nova variante = novo pré-registo.
