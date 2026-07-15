# PRÉ-REGISTO FORWARD — Engine Cp (capitulação em bear) — BASELINE APROVADO

**Congelado em: 2026-07-16.** Documento de compromisso. Regras, métricas, null e PASS/FAIL abaixo ficam
**imutáveis**. Alteração pós-forward = **novo prereg + novo forward** (proibido mover a baliza).
Aprovado por Cris ("baseline como o engine Cp, é bom por si"). Mesmo formato de A1/A2/B. RAW-only, sem
primitives. Ver [[BOTTOM_ENGINE_LOGIC_REFERENCE]], [[project_cp_capitulation]].

---

## 0. Porquê
Cp = reversão de capitulação em BEAR (não continuação-em-bull). GT = 5 velas capitulação marcadas pelo
Cris (chart). Cris validou visualmente: **"o melhor entry por construção que já fizemos"** — entradas
todas em fundos legítimos. A leitura auction-theory (intensidade de leilão cumulativa na perna) é o que
mistura indicadores+estrutura. Refinos (pós-grab, trailing, trail-após-3R) NÃO melhoraram o baseline →
o baseline é o engine mecânico ótimo; extensão de exit = camada discricionária do Cris.

## 1. HIPÓTESE ÚNICA (congelada)
> Numa capitulação (fundo de perna de baixa SIGNIFICATIVA, com leilão intenso), o gatilho 1º-reclaim
> tem expectância positiva a 3R e bate o null (buy-any-reclaim no bear = 22%, a faca).

## 2. REGRAS EXATAS (congeladas; implementação-mãe = cp_refined.entry_first/exit_fixed3R + confluência)
Fonte: RAW 15M do HD. Causal close-only.
**2.1 ESTRUTURA (fundo-de-perna-significativa):** swing-low fractal (m=3) que é o fundo de uma perna de
  baixa com **legMag = (max high em [j−480,j] − L[j])/ATR ≥ 15** E **is_leg_bottom** (L[j] ≤ min low
  em [j−192, j]). O regime detector + leg dão a estrutura; o flush-de-vela-única NÃO (foi erro).
**2.2 CONFLUÊNCIA AUCTION (intensidade do leilão na perna):** ativação cumulativa de order-flow do
  leg-high ao low: **buy_dens = Σ buy-bubbles/barra ≥ 0.25** OU **leg_sell = Σ sell-bubbles ≥ 180**.
  (Duas assinaturas: absorção-compradora pesada OU NAS+venda pesada — ambas = leilão intenso.)
**2.3 GATILHO (1º-reclaim):** 1ª barra `k` após o low com `close[k] > high[k−1]` E `close[k] > open[k]`.
  Guarda: risco > 0.05·ATR. Se `low` for varrido (L[k] ≤ SL) antes do reclaim = NO-TRADE.
**2.4 SL e alvo:** `SL = flush_low − 0.1·ATR`; `target = entry + 3·(entry−SL)`; outcome SL-first no RAW
  15M, horizonte 480 barras. Exit fixo 3R (refinos não melhoraram).

## 3. MÉTRICAS (por trade forward)
avgR · WR (R>0) · NET-R · streak (máx losses consecutivos, FN) · maxDD-R · GT vs extra · null.

## 4. VETOR DE FALHA DECLARADO
**Grabs de liquidez:** ~5/12 dos LOSS in-sample são grabs (SL varrido, depois reverte a 3R) = região
certa, entrada precipitada. Medir no forward quantos LOSS são grabs vs erro de região. (Fix causal não
encontrado — pós-grab/trailing pioram; a gestão fica discricionária.)

## 5. NULL (declarado)
buy-any-reclaim no bear = **22%** (a faca a cair). O engine tem de bater isto (in-sample avgR +0.60,
WR 43% > breakeven 3R de 25%).

## 6. CRITÉRIO PASS / FAIL (congelado AGORA)
**N mínimo:** ≥ **15 capitulações forward** (raras). Antes = INCONCLUSIVO.
**PASS** exige TODAS: avgR > 0 (bate o breakeven) · WR ≥ 33% (> breakeven 25%) · **streak ≤ 5** (FN) ·
bate o null 22% · expectância líquida positiva com custo real.
**FAIL** se: avgR ≤ 0, ou streak > 5, ou não bate o null, ou expectância ≤ 0.

## 7. PROTOCOLO FORWARD
Cada nova capitulação (bear, identificada pela leitura do Cris/stack) é pontuada pelo engine (estrutura
+ confluência + 1º-reclaim + SL/3R + null). Sem alterar regras. Acumular até N≥15, então §6.

## 8. REFERÊNCIA IN-SAMPLE (bear 2026 — desenho, NÃO validação)
N=21 · **WR 43% · avgR +0.60R · NET +12.6R · streak −4 · maxDD −4R · GT 5/5** (+ acha extras 3R).
**Caveats:** só bear 2026; N=21; limiares (legMag/confluência) informados pelos 5 GT = overfit-risk;
bubbles sem known_at (protegido por buffer ≥3 barras, não provado); MFE 6R não capturável (path choppy).
Forward = árbitro.

---
*Fim. Congelado 2026-07-16. §1-§6 imutáveis — refinamentos = novo doc.*
