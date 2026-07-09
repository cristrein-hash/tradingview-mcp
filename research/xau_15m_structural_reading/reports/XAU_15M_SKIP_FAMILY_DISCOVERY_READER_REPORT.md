# SKIP FAMILY DISCOVERY — LEITURA DO READER (2026-07-09)

> **STATUS (Cris 2026-07-09):** `SKIP_FAMILY_LEDGER = CALIBRATION_DISCOVERY_NOT_STRATEGY` ·
> `S2a_1D_DEPTH = VALIDATED_CALIBRATION_SIGNAL` · `S3_STRUCTURE_ABOVE = NEW_PROMISING_SKIP_AXIS` ·
> `S2b_HTF_ANCHOR = REDUNDANT_WITH_1D_DEPTH_IN_THIS_SAMPLE` ·
> `S1_POS384_RAW = STERILE_WITHOUT_CONTEXT` · `S4_REGION_AUTHORITY = NOT_MEASURABLE_AS_CONTAINMENT`
> · `S5_RANGE_THIRD = FAILED_AS_OPERATIONALIZED` · `NO_COMPOSITE_APPROVED` · `NO_ENTRY` ·
> `NO_BACKTEST` · `NO_PRODUCTION`.
> Direção do Cris: próximo = **Fase 3A, BEAR-only composite prereg (S2a+S3)** — sem BULL/RANGE
> (continuam em descoberta separada); S2b não entra como eixo principal; S1 talvez só em contexto
> range/topo/exaustão; S4 re-operacionalizar como "região abaixo/distância a região defendida".

> Fase 2 do prereg executada (GO do Cris). Base causal live-fireable n=166 (120L/46W; sha16
> 6d1d8cb1e731adce; base rates: BULL 56% L · BEAR 78% L · RANGE 79% L). Medidores contínuos +
> marcações DESCRITIVAS declaradas (nunca regra). Ledger candidato×família em
> `results/skip_family_discovery_ledger.csv`. Null estratificado por macro (2000×). CALIBRAÇÃO
> (base estudada); janela virgem 2024-25 intocada. Sem composto (Fase 3 = prereg futuro).

## Resposta às 4 perguntas do prereg, família a família

| família | corta losers? | mata winners? | veredito do reader |
|---|---|---|---|
| **S2a** 1D (cláusula do filtro VALIDADO) | **21L / 1W · p=0,016** | quase não | **CONFIRMA — replica o filtro na variante price-agg** |
| **S2b** âncora HTF (quartil descritivo) | 18L / 2W · p=0,12 | quase não | **REDUNDANTE com S2a** (ver baixo) |
| **S3** estrutura acima (≥2 bounce-peaks descendentes, BEAR) | **40L / 6W · p=0,025** | pouco | **O "próximo ouro" TEM SINAL — e é eixo INDEPENDENTE** |
| **S1** pos384>0,70 (sem contexto) | 45L / 20W · **p=0,53** | SIM (20W) | **ESTÉRIL nesta base sem contexto** |
| **S4** autoridade da região | — | — | **NÃO-MENSURÁVEL como operacionalizado** (0/166 dentro de região ativa) |
| **S5** range fora do terço inferior | 31L / 8W · **p=0,62** | sim | **SEM SINAL como operacionalizado** |

## Os 3 achados que importam

**1. A TUA PERGUNTA CENTRAL RESPONDIDA — a âncora HTF é redundante com o 1D neste substrato.**
Losers marcados: S2a∩S2b = 17 · só-S2a = 4 · só-S2b = 1 (Jaccard 0,68). **A âncora está a medir o
mesmo "já caiu muito" que a profundidade 1D — acrescenta 1 loser e perde 4.** No mapa-BEAR das tuas
marcas ela parecia especial; nos trades reais, não acrescenta. Registado sem drama: o carregador da
família S2 é o 1D (que já é o filtro validado).

**2. S3 — estrutura acima — é o eixo NOVO real (REFORÇADO pelo DA).**
40L/6W total; valor incremental sob o COMPARADOR CORRETO (DA edit 2): o pool relevante é
BEAR∖S2a = 56 candidatos com 71,4% de losers (não os 78% da base) → **S3-only = 30/35 (86%) =
lift +14pp, p hipergeométrico = 0,0032**. Marca losers que o 1D NÃO marca (Jaccard 0,19).
Os bounce-peaks DESCENDENTES capturam a "perna viva por cima" dos teus prints — onde o D1 falhava.
**Declarações do DA (edit 1):** "≥2" e "BEAR-only" foram especificações DESCRITIVAS pós-prereg
(o prereg declarava a contagem contínua): sensibilidade ndesc ≥1/≥2/≥3 = 81/87/84% e
K 1,25/1,5/1,75/2,0 = 83/87/84/73% — direção robusta em todo o miolo, degrada só em K=2,0;
K=1,5 herdado do D3 = calibrado nesta MESMA base (contaminação suave declarada). Em BULL o ndesc≥2
é ANTI-sinal (4L/5W) — a restrição BEAR é economicamente certa mas foi decidida na execução.
**Look queimado (DA edit 3): a observação S2a∪S3 = 51L/6W É um olhar de composto sobre esta base —
o árbitro do composto é a janela virgem 2024-25, NUNCA este número.**

**3. S1 sem contexto NÃO transfere — o teu aviso confirmado empiricamente.**
Na base real (reclaims causais), pos384>0,70 marca 45L/20W (p=0,53 = acaso); em BULL marca 17L em
28 (61% ≈ base 56%). **"Nem todo preço alto é loser; em BULL forte, alto continua"** — a cláusula
que era perfeita nos C-losers (entries 6-ATR pós-confirmação, população diferente) é cega aqui.
S1 não está morto: está SUB-ESPECIFICADO — precisa do contexto que listaste (topo-de-range vs
perna-impulsiva vs fim-de-perna). Trabalho de lapidação futuro, com as tuas 4 sub-classes.

## Honestidades (com os edits do DA)
- **S4 quantificado (edit 6): TODOS os 166 entries têm região ativa ABAIXO — mínimo 0,89 ATR acima
  do topo da banda, mediana 5,1 ATR, ZERO dentro de 0,5 ATR.** Containment nunca dispararia em
  reclaims; re-operacionalizar como "região-ABAIXO mais próxima + autoridade".
- **S2b (edit 5):** comparação assimétrica declarada — S2a = cláusula FIXA validada; S2b = quartil
  MÓVEL ajustado a esta base (e ainda assim perdeu ⇒ a redundância é conservadora);
  `dist_prev_rng_bot` nunca foi flagado (não avaliado). Reconciliação com o mapa-BEAR: populações
  diferentes (marcas de fundo genuíno vs trades de reclaim) — nas marcas a âncora brilhava porque o
  contraste era fundo-vs-bounce; nos trades o 1D já carrega essa informação.
- **Medidas do prereg NÃO computadas (edit 4):** S3 fração-de-recuperação e tempo-desde-high-
  reclaimed; S4 direção-da-perna-no-nascimento; S1 idade-da-perna — computar antes da Fase 3 ou
  re-declarar fora.
- **Contagem de looks do bloco (edit 3):** 6 flags descritivos + 2 grelhas de sensibilidade S3
  (3 ndesc × 4 K, corridas pelo DA) + 1 look de união S2a∪S3 (QUEIMADO) ≈ 19 looks, todos nesta
  base de calibração.
- **S5**: bounds running do episódio macro-RANGE podem não corresponder ao "range real" que lês no
  chart; sem sinal AQUI não enterra a tua régua 4H — enterra esta operacionalização.
- Nulls com autocorrelação serial (trades concorrentes) — p's descritivos.
- S2a = variante price-agg do filtro (21L/1W vs 22L/0W do validado; 2 casos borderline ±0,5 ATR) —
  coerente.

## O que a Fase 3 (composto, prereg futuro) herda deste ledger
Carregadores reais: **S2a (1D) + S3 (estrutura acima)** — independentes, ambos BEAR.
Descartados/adiados: S2b (redundante) · S1 e S5 (sub-especificados — lapidação com contexto) ·
S4 (re-operacionalizar). O composto BEAR candidato nasce de S2a+S3; a família BULL continua SEM
proteção validada (o maior buraco aberto — 25 losers em 45).

## Confirmação negativa
Sem entry · sem backtest novo (outcomes pré-existentes da base) · sem thresholds-regra · sem
composto · calibração declarada · janela virgem intocada.
