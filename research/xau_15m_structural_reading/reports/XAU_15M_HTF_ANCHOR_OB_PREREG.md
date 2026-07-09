# PREREG — MAPA HTF (família BEAR) + VERIFICAÇÃO CAUSAL OB DETECTOR (2026-07-09)

> Autorizado pelo Cris. MEDIDOR contínuo; sem cortes/votos; leitura = READER; caminho = CRIS.
> Sem entry, sem backtest. RAW HD only (15M + 30M + 1H diretos; 1D = price-agg interna declarada).
> Calibração declarada (GT conhecido/queimado); validação futura = episódios virgens/bear seguinte.

## Conjuntos (do catálogo, fail-loud nos counts)
- **BEAR-set (mapa HTF + OB):** 12 FUNDO ≥2026-03-01 + 3 INVALIDO "perna bear" (mar/2026). n=15.
- **BULL-set (OB-H1):** 26 FUNDO <2026-03-01 excl. RANGE vs **6 losers C** (A-BULL, timestamps dos
  dossiês). Pergunta: presença/proximidade de zona demand OB-H1 discrimina fundo real de compra-de-topo?
- **RANGE-set (OB-30M):** 4 FUNDO {2025-08-01, 08-20, 11-18, 11-21}. n=4 ⇒ SEMPRE EXPLORATORY, descritivo.

## Medições congeladas (contínuas)
**Mapa HTF (BEAR-set):**
- `dist_prior_episode_bottom_atr` — episódios = runs do macro v5 hour-causal (já vivo); âncora =
  mínimo do episódio ANTERIOR FECHADO (conhecido no fecho, causal); distância assinada em ATR15.
- `dist_prior_range_bottom_atr` — idem, último episódio RANGE fechado.
- `px_vs_ema1d_atr` — feature do filtro capitulation VIVO, recomputada de price-agg 1D interna
  (dias FECHADOS D-1; variante declarada da nativa).
- `lh_staircase_0_3` — nº de descidas consecutivas dos máximos das janelas [96],[192-96],[288-192],
  [384-288] barras 15M (estrutura ACIMA, congelado).
**OB causal (todos os sets):** no último snapshot RAW HTF com replay ≤ t da marca (semântica alive-at-T
nativa do snapshot, sem reconstrução): `n_zonas_OB` · `inside_OB_below (0/1)` · `dist_atr_zona_OB
mais próxima abaixo` (normalização ATR15 na marca). 1H para BULL/BEAR; 30M para RANGE/BEAR.

## Scorabilidade declarada
30M/1H congelam 2026-05-25 ⇒ marcas 06-10/06-24/06-30 = **UNSCORABLE para OB** (3 do BEAR-set);
1D price-agg cobre até 2026-07-03 ⇒ mapa HTF scorable em todos.

## Resultado esperado declarado ANTES do run
- BEAR: A6 e fundos reais mais FUNDOS no mapa (dist ao bottom anterior pequena/negativa; 1D bem
  negativo) que B1/B2/B3 (bounces no meio: dist grande, 1D menos profundo). B3 é o teste duro
  (flush fundo mas intermédio) — pode NÃO separar pelo mapa e exigir estrutura-acima/LH.
- BULL: hipótese ABERTA (verificação pedida pelo Cris) — sem expectativa forte; se OB-H1 não
  discriminar 26 vs C6, reporta-se estéril sem drama.
- RANGE: descritivo (as 4 bases tocam zona OB-30M?).

## Looks e disciplina
1 run por medidor; zero tuning; tudo no ledger do bloco; null episódico (permutação de rótulos) só
para separações observadas; DA obrigatório; commit só com autorização.
