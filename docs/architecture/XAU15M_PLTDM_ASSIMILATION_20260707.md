# XAU 15M LONG — Assimilação PLT/DM (guia manual do Cris) + Detector de Polaridade Causal

**Data:** 2026-07-07 · **Autor:** Claude (sessão continuada) · **Estado:** ASSIMILADO, detector construído, fronteira recall×N mapeada.

## 1. O que o Cris marcou (extraído via MCP)
Cris plotou `text_note` no chart PEPPERSTONE:XAUUSD/15 para me guiar a "zona de demanda criada no retest do topo rompido anterior":
- **10 PLT** (polaridade de topo) — ago→out/2025, níveis 3386→3394→3408→3423→3509→3580→3625→3707→3792→4178.
- **11 DM** (demanda) — 3466, 3525, 3536, 3574, 3613, 3635, 3713, 3723, 3940, 4090, 4180.

Coordenadas salvas: `research/xau_15m_bb_nas_leonardo/results/manual_shapes_pltdm_20260707.json`.

## 2. Padrão assimilado (caracterização causal)
- **PLT = topos SUCESSIVOS ASCENDENTES da escada de markup (higher-highs), rompidos.** 10/10 rompidos-depois; 8/10 são swing-high; **0/10 são EQH** (matou a hipótese EQH). Casam com zigzag-high **r=3** em **9/10** (r=2 10/10, r=4 8/10) → escala confirmada r≈3.
- **DM = zona de demanda fresca = origem de perna que ROMPE estrutura (BOS+ subsequente).** Geradas causalmente como zigzag-low r=3 seguido de close acima do swing-high anterior em ≤384 barras.
- **Fundo BULL** = pullback que retesta o ÚLTIMO higher-high rompido (PLT) OU sen ta numa DM fresca acima do topo antigo.

## 3. Achado central (primeiro discriminador de polaridade na direção CERTA)
Todas as 4 implementações genéricas anteriores de "retest de topo rompido" (BOS+/EQH/fractal/suporte-qualquer) **ANTI-discriminavam** (fundos retestavam MENOS que não-fundos). A escada de markup corrige isso:

| feature (BULL) | fund | não-fund | direção |
|---|---|---|---|
| suporte genérico | 21% | 31% | anti (errado) |
| **PLT-escada (higher-high markup)** | **15%** | **8%** | **pró (~2×)** ✅ |
| DM-demanda | 38% | 28% | pró |
| **PLT ∪ DM (confluência)** | **44%** | **33%** | **pró** ✅ |

RANGE/BEAR: ladder inerte (0%) — coerente (BEAR está em novo mínimo, não retesta topo; usa retr alto = end-of-fall).

## 4. Fronteira recall × N (meta: N≤100 incluindo ao máximo os ~42 eventos)
Universo pivô = 954 (zigzag r=1.5/3/6/9). Regra por regime: BULL/RANGE = polaridade; BEAR = end-of-fall (retr alto).

| config | N | recall (eventos/42) | fundos-pivô |
|---|---|---|---|
| **confluência dupla (lad & dm) BULL/RANGE · BEAR retr≥0.5** | **101** | **14** | **22** |
| pltdm & sweep>0 (BULL)… | 157 | 21 | 26 |
| pltdm & drop≥6 (BULL) · BEAR retr≥0.55&drop≥6 | 228 | 26 | 38 |
| pltdm união (sem aperto BULL) | 313 | 26 | 42 |

**N=101 (confluência dupla) = ponto de operação na meta N≤100**, recuperando 14/42 eventos / 22 fundos-pivô a ~2× densidade-precisão vs base.

## 5. Limite honesto (DA)
Empurrar recall acima de ~26/42 exige N>200. Os ~16 fundos MISSED são pullbacks BULL rasos (medianas fund BULL: drop 11 ATR mas **retr 0.17, sweep −0.8** = queda local grande, retração macro rasa, NÃO varre mínimos) — **estatisticamente indistinguíveis de pullbacks não-marcados em TODAS as features 15M medidas** (confirmado através de: score linear, CART out-of-fold, enriquecimento de fluxo, 4 impl. de polaridade, escada, DM, confluência). O resíduo é **discricionário** — que é exatamente por que o Cris teve de marcar PLT/DM à mão. O separador que falta não está no snapshot 15M; candidatos não-cobertos: micro-forma/sequência da reversão (shape bar-a-bar), qualidade da perna HTF (4H/1D), inter-mercado.

## 6. Artefatos
- `assimilate_pltdm_20260707.py` — extração + caracterização PLT/DM.
- `bottom_polarity_scalev2_20260707.py` — escala do topo (PLT casam r=3 9/10).
- `bottom_polarity_ladder_20260707.py` — escada ascendente por regime (achado 15/8).
- `bottom_pltdm_confluence_20260707.py` — detector confluência + fronteira. Saída: `results/pltdm_confluence_20260707.json`.

## 6b. CORREÇÃO DE MIOPIA + REFUTAÇÃO DA HIPÓTESE "SIGNIFICÂNCIA" (2026-07-07, pós-rejeição do Cris)
Cris rejeitou a fronteira recall×N: *"ainda estás a achar fundos de forma míope, não por evento contextual… não me sugiras mais seguimentos indutivos."* Diagnóstico aceito: zigzag r=3 = **local** (poucas barras); os PLT/DM abrangem **semanas**. O erro é tratar 954 pivôs/145 zonas como pool e filtrar — num markup de 2 anos quase todo topo é rompido (78/90), densidade é inevitável.

Tentativas de escala macro (não aceitáveis, registradas p/ não repetir):
- `bottom_macro_event_20260707.py` (swing diário + retorno a qualquer zona macro): N177 dens 11:1.
- `bottom_active_demand_20260707.py` (máquina de UMA demanda ativa = último higher-low): N58-105, dens 6-9:1, MAS **MISSED inclui os próprios fundos PLT/DM do Cris** (09-02/04/11/30, 10-14/15/17) → "último higher-low" ≠ a DM dele.

**REFUTAÇÃO CENTRAL** (`plt_significance_20260707.py`): medida a história de largo-contexto dos 10 PLT do Cris ANTES do rompimento. **Os PLT NÃO são resistências significativas** — mediana **1 reação** (vários com 0; 09-11@3625 e 10-14@4178 = topos frescos, span 0d). Topos genéricos rompidos têm **MAIS** história (mediana 4 reações). 31% dos genéricos já batem a fasquia de significância dos PLT → significância **não seleciona**. **CONCLUSÃO: o que define um PLT não é atributo estático da barra; é a POSIÇÃO SEQUENCIAL no markup — a referência da perna corrente, marcada ao CAMINHAR a estrutura perna-a-perna.** A diferença N926→N54 existe, mas vive no **processo sequencial (caminhada das pernas)**, não numa feature de snapshot. Todo filtro por-barra/pool bate no muro por procurar propriedade onde há processo. → Paradigma proposto ao Cris (aguarda decisão): (1) autômato de caminhada de pernas [1 referência/perna]; (2) Cris marca as pernas macro e eu ancoro; (3) leitura evento-a-evento 1-a-1 sem produzir N/densidade até o critério estar claro.

## 7. Próximo (fork p/ Cris decidir — regras são guias, não leis)
1. Aceitar N101 (alta-precisão) OU N228 (recall 26/42) como set de eventos → seguir para **entry 3×1** e **famílias**.
2. OU marcar mais PLT/DM em janelas fora ago-out/2025 para estender o guia.
3. OU engenheirar features de micro-sequência da reversão / perna-HTF (única casa não-exaurida do separador).
