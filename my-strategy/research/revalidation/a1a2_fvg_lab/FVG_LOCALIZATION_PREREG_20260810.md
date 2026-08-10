# PRÉ-REGISTO — Filtro de LOCALIZAÇÃO por FVG-fill no A1/A2 PULLBACK 15M

**Data:** 2026-08-10 · **Autor:** Claude (co-piloto) sob ordem do Cris · **Estatuto:** congelado ANTES de correr.
**Origem:** Cris 10/08 — o sinal A1/A2 dispara às vezes a meio-perna (ex. sexta 08/08 @4355, bounce 63%);
outras vezes entra num bom fundo pós-FVG-fill (ex. hoje 03:30, bounce 30%). Hipótese: um filtro de
FVG-fill/fundo melhora a localização de entry **sem matar os fundos genuínos**.

> ⚠️ Os dois trades motivadores (sexta 08/08, hoje 10/08) **NÃO estão** na amostra GT nem nos blocos RAW
> (terminam 2026-07-04). São **anedota held-out**, NÃO usados para escolher limiares. A medição vive
> inteira dentro dos 32 fundos GT. Isto elimina por construção o overfit-aos-dois-trades.

## 1. Amostra e motor (chão de verdade — não reinventar)
- **Amostra:** `results/REGIME_GT_FUNDOS_UNIFIED_20260714.json`, subclasses `A1_pullback_fundo` (N=14) +
  `A2_pullback_raso` (N=18) = **32 fundos**. Cada fundo = `{t, price, macro, leg, subclasse}`.
- **Motor de entry:** `a1_causal_entry.causal_entry(S, j, "MB3")` — MB3 + SL low-real, causal, SL-first,
  HORIZON=480. **Read-only, não modificado.** Baseline = correr este motor tal-qual nos 32 fundos.
- **RAW:** blocos 2025-02-25 → 2026-07-04 (`load_series`), merge max-high/min-low/last-close. RAW-first.

## 2. Feature FVG (causal, das barras RAW, congelada)
- **FVG bullish** no triplo `(b-1, b, b+1)`: `high[b-1] < low[b+1]`. Zona do gap = `[glo=high[b-1], ghi=low[b+1]]`.
  Confirmado (formado) na barra `b+1`.
- **Leg do pullback:** `hh` = `max(high[jf-96 : jf])` (topo da perna antes do pullback); `pb_low` = low do
  fundo GT (barra `jf`). `bounce_pct = 100·(ent − pb_low)/(hh − pb_low)` (idêntico ao runtime).
- **`fvg_below_filled`** (True/False) no instante do sinal `ei`, **só barras ≤ ei**:
  existe FVG bullish formado em `b+1 ≤ jf`, com `ghi ≤ ent` (abaixo da entrada) E `pb_low ≤ ghi` (o pullback
  desceu para dentro do gap = preencheu). Causal por construção (usa barras ≤ jf < ei).
- **Sem lookahead:** o gap fecha o seu triplo em `b+1 ≤ jf`; `bounce_pct` e `fvg_below_filled` não tocam `i>ei`.

## 3. As 3 operacionalizações (todas medidas)
- **C — ETIQUETA (risco zero):** `location = early (bounce≤40) / mid (40–60) / late (>60)` + flag `fvg`.
  Não muda mecânica. Só reporta distribuição e correlação com WIN/LOSS.
- **A — GATE DURO:** emite sinal só se `bounce_pct ≤ 50` **OU** `fvg_below_filled`. Conta winners mortos.
- **B — REFINAR ENTRY (limite no FVG):** quando `fvg_below_filled`, coloca entrada-LIMITE em `ghi` (topo do
  FVG) em vez de mercado; preenche só se, após `ei`, alguma barra na janela de fill (TRIG_WIN=48) negoceia
  `low ≤ ghi` ANTES de bater alvo; senão **expira (0R, não-fill)**. SL mantém-se (low-real). Novo
  `R = ghi − sl`, novo alvo `ghi + 3R`, re-resolvido SL-first. Sem FVG → entrada mercado baseline (B não altera).

## 4. REGRA DE DECISÃO PRÉ-REGISTADA (limiares fixos ANTES de correr — aceites pelo Cris 10/08)
Medido nos 32 fundos, variante vs baseline. **APROVA para forward** só se **TODAS**:
1. **Retenção:** mata/expira **≤ 1** dos WINs SL-first atuais.
2. **Localização:** mediana de `bounce_pct` das entradas sobreviventes cai **≥ 15 pontos** E entradas com
   `bounce_pct > 60` ficam **≤ 1**.
3. **Agregado não pior:** `sumR` não reduz E `return/DD` não reduz vs baseline (para B, não-fills contam 0R,
   não como perda).
4. **Sem novos losers:** não converte nenhum WIN atual em LOSS.

**REPROVA** se matar > 1 winner, OU falhar qualquer alvo de localização, OU reduzir `sumR`/`return/DD`.

Sexta/hoje = inspeção anedótica **só depois** do painel dos 32; nunca para escolher 50%/60%/15-pts.

## 5. Painel obrigatório (baseline + A + B + C)
Por variante e por camada (A1/A2) e por ano: **N · WR · sumR · avgR · DD · return/DD · streak · med barras-a-3R ·
(B) fill-rate · winners-killed · mediana bounce_pct antes/depois.** Tabela per-fundo do que mudou.
Check null: entrada aleatória em `[low+1, low+48]` para confirmar que a variante bate o acaso.

## 6. NÃO TOCAR (congelado)
`continuation_A1A2/a1a2_runtime.py` (daemon live) · `a1_causal_entry.py` (mecânica) · forward log/score ·
Telegram · env-locks `A1A2_*` · prereg 14/07 · GT JSON · dataset RAW (read-only). Deliverable = **relatório +
veredito PASS/FAIL**, NÃO edição live. Se PASS → novo prereg forward; live fica congelado até forward confirmar.
