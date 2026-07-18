# PREREG — F-A2: Mapa de Ímanes (FVG + clusters de liquidez), congelado 2026-07-18

Frente A-2 da calibração do E2 (segue `E2_READ_CALIBRATION_DESIGN_20260718.md`). Escreve-se ANTES de
codificar (Cris aprovou o enquadramento; escopo = os 2 fatores LuxAlgo-derivados). **Grelha e critério
congelados aqui — não se afinam ao dado (princípio vs fit).**

## 0. Enquadramento (o que É e o que NÃO é)
- **É** uma VOZ de contexto no dossiê E0 — "que ímanes puxam o preço acima/abaixo, e estão testados?"
  Serve o **fator 3** que faltou na inversão de 2026-07-17 (OB + 3 SVPs acima, não-testados, invisíveis
  ao read). FVG acrescenta um objeto ORTOGONAL (vazio de continuação) que o sistema não tinha.
- **NÃO é** sinal/seta, NÃO entra na aritmética do E1, NÃO é gate. Geometria isolada = ruído recorrente
  ([[project_cp_antifaca_no_discriminator]]). Vive só na IMAGEM do read E2. Árbitro = forward/GT, não crença.
- **Fator 2 (maturidade/ordinalidade do pullback) INCLUÍDO** (Cris 2026-07-18): também voz descritiva.

## 1. Definições causais (close-only, forward-only)
### 1.1 FVG (Fair Value Gap) — regra das 3 velas
- Em barra `i` FECHADA: **bullish** se `low[i] > high[i-2]` (zona vazia `[high[i-2], low[i]]`); **bearish**
  se `high[i] < low[i-2]` (zona `[low[i], high[i-2]]`). Definido só no fecho de `i`, nunca reescrito → causal.
- **Mitigação (a armadilha):** só barras `j ≥ i+1` JÁ FECHADAS. FVG **não-mitigado** = nenhuma barra fechada
  `j>i` entrou na zona (bull: `low[j] ≤ high[i-2]` marca entrada). "Totalmente preenchido" = fecho além da
  borda distante. Testar fill com a barra em formação = reintroduz o leak do `ovr_at` → PROIBIDO (DA verifica).
### 1.2 Clusters de liquidez — equal highs/lows
- **Swing** fractal confirmado com `k` barras à direita fechadas (lag k, sem repaint — como a histerese K=5).
- **Cluster**: swings do mesmo tipo dentro de tolerância `tol·ATR`, com ≥`N` toques = nível de liquidez.
- **Testado**: preço tocou o nível após a formação (barra fechada). "Sweep-and-revert" = sinal composto,
  FORA da 1ª passagem.
### 1.2b Ordinalidade do pullback (fator 2) — "1º pullback raramente reverte"
- Sobre swings fractais confirmados (k=3): **up-leg** = cauda de higher-lows consecutivos; **down-leg** =
  cauda de lower-highs consecutivos. **ordinal** = nº desses consecutivos na cauda (1 = 1º pullback).
- Voz: `{leg_dir, ordinal, maturity}` — ordinal 1 = "continuação provável"; ≥3 = "maduro, reversão mais
  provável". Causal (swings com lag k, sem repaint). NÃO é sinal — contextualiza um SHORT no 1º pullback
  de up-leg (= baixa probabilidade, o caso de 6ª) vs num 3º (= maduro).

### 1.3 Consolidação (o mapa único)
Dossiê funde numa só lista acima/abaixo: **FVG-não-mitigado + cluster-liquidez + OB (pine_boxes) + SVP-node**,
cada um com `{tipo, dist_atr, size_atr, idade, densidade_toques, testado:bool}`.

## 2. GRELHA CONGELADA (escolhida por princípio, ANTES de ver dado)
| Param | Valor | Razão (princípio, não fit) |
|---|---|---|
| FVG min size | ≥ 0,25·ATR14 | filtra micro-gaps = ruído; mesmo 0,25 do resto do stack |
| FVG mitigação | entrada de qualquer barra fechada na zona | conservador; sem lookahead |
| FVG lookback | 480 barras (5 dias 15M) | = LEGWIN do Cp; janela de relevância |
| Cluster k (swing) | 3 | = M_FRAC do Cp (consistência) |
| Cluster tol | 0,25·ATR14 | mesma unidade de "igual" do stack |
| Cluster N toques | ≥ 2 | equal-highs = 2; densidade reportada à parte |
| Cluster lookback | 480 barras | idem |
Qualquer mudança destes = novo prereg.

## 3. Onde vive (forma correta, padrão F-A1)
1. **Reader store-backed** `context_magnets.py` (novo): lê barras FECHADAS do bar-store 15M, computa FVGs +
   clusters, funde com OB/SVP já no dossiê. Zero MCP novo, zero fonte nova.
2. **Render** no dossiê como bloco `magnets: {above:[...], below:[...]}` — descritivo. **Nenhuma seta.**
3. **Consumo:** só a IMAGEM do read E2 (`render_composite`). **NÃO** o score do E1. **NÃO** gate.
4. F-B (o read PASSAR a usar o mapa no juízo) = espera o GT de segunda; aqui só se ENRIQUECE a imagem (shadow).

## 4. Plano DA (lookahead — obrigatório antes de qualquer conclusão)
- FVG definido no fecho de `i`; mitigação só varre `j≥i+1` fechadas; swing com lag `k`. DA verifica byte-a-byte
  que nenhuma função lê barra em formação nem futura. Reproduz o rigor do `ovr_at` corrigido.
- **Null de recorrência:** medir se "dist ao íman não-testado na direção do candidato" SEPARA os casos GT ou é
  plano (geometria recorrente). Se plano → fica SÓ descritivo (não pesa), nunca inflaciona.

## 5. Critério de aprovação (congelado; não é sinal → não é WR/R)
- **Shadow primeiro (F-A3):** nos casos GT (os 2 SHORTs de 6ª + futuros), o bloco `magnets` MOSTRA o íman
  não-testado que o Cris citou? Binário por caso: surgiu / não surgiu.
- **Forward (árbitro):** sobre N≥15 casos GT futuros, o dossiê enriquecido alinha melhor o read com as calls
  do Cris do que o dossiê pré-F-A2? Medido em shadow, sem mudar prompt (isso é F-B).
- **Kill:** se o mapa dispara em todo o lado e não discrimina no GT → permanece OFF do peso do read (só
  descritivo). Não se "salva" afinando a grelha.

## 6. O que este prereg NÃO promete
Não gera trades. Não é seta. Não melhora WR mecanicamente. Melhora a QUALIDADE da leitura contextual
(o mapa de ímanes que faltou na 6ª). Se o forward não mostrar alinhamento com o GT, morre como descritivo.
