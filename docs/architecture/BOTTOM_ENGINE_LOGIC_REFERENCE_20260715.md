# REFERÊNCIA — Estrutura lógica de engines de FUNDO/CAPITULAÇÃO (resgate 2026-07-15)

Registo permanente da lógica dos engines de bottom anteriores (`research/xau_15m_bb_nas_leonardo/`),
para servir de **template de como construir engines futuros**. Rodados e auditados (DA-lookahead) em
2026-07-15. Fonte da verdade = RAW 15M do HD; NAS = SHIFT1 repintante (usar known_at).

---

## 0. O PRINCÍPIO-MESTRE (ordering breakthrough — `event_stage2_entry_20260706.py`)
> **Selecionar o bottom-EVENTO primeiro (mapeamento ESTRUTURAL), DEPOIS a entrada DENTRO do evento.**
> A entrada só funciona **dentro** de um evento-fundo verdadeiro. Fora dele = null (a faca).

Evidência: no pool estrutural (328 eventos) o 1º-cand dá 26% hit3R (≈null); a MESMA entrada, restrita à
família + `cascade+reclaim+hl`, dá **48-53% hit3R, streak≤2, P(streak>5)≤0,14, todos os anos positivos,
DD −2** (configs E5/E6). O lift vem da ORDEM (estrutura→entrada), não de um indicador isolado.

## 1. CAMADA ESTRUTURA (template CAUSAL LIMPO — `bottom_detector_structural_20260707.py`)
Ordem: **estrutura ANTES de indicadores** (correção Cris: nunca snapshot sem contexto estrutural).
Para CADA pivô-low candidato (zigzag causal r=3, confirmado no travel `r·ATR`, `kt=TS[i]>pt`):
- **Regime multi-escala** (secular E50/E100 · médio E20/E40+slope) no `known_at`.
- **`retr_up`** = retração da perna macro de ALTA (lookback ~126 dias) → **posição TOP/MIDDLE/BOTTOM
  (os terços). Entradas vivem no BOTTOM third.**
- **`is_leg_bottom`** = `LO[pi] ≤ min(LO[pi−192:pi+1])` (o low É o fundo da perna, não intermediário).
- **`choch_up`** = evento CHoCH+ 15M entre o pivô-low e o known_at (a perna de baixa TERMINOU).
- **Classificar:** `BULL_pullback` (reg BULL + is_leg_bottom + retr_up≤0,55) · `BEAR_reversal`
  (reg BEAR/RANGE + choch_up + is_leg_bottom + retr_up≥0,45) · ruído.
- **LIÇÃO empírica:** a classe pura `BEAR_reversal` é ESTREITA (recall 0/42 nos manuais) — **a maioria
  dos fundos do Cris vive em contexto BULL/RANGE (pullback), não bear-reversal puro.** A família é ampla.

## 2. CAMADA ENTRADA (dentro do evento — `event_stage2`)
Config vencedora (FN-compatível): **`cascade≥3-4` + `reclaim` + `higher-low` (+ `oversold` RSI)**.
- E5 cascade4&reclaim: N19 · 53% · streak−2 · P(>5)=0,08 · +19,6 · anos+.
- E6 cascade3&hl&reclaim: N29 · 48% · streak−2 · P(>5)=0,14 · +27,3 · anos+.
- ✅ **Causalidade auditada (DA 2026-07-15): PORTÁVEL.** reclaim/hl/oversold = totalmente causais
  (closed-bar); SL≤entrada; 3R first-touch conservador; os 50 eventos = marcas MANUAIS do Cris (NÃO
  outcome-defined = **não circular**); null-dentro-do-evento isola o timing. Os 48-53% NÃO são lookahead.
- ⚠️ **2 ressalvas:** (1) `cascade` usa SMC (BOS/CHoCH) sem `known_at` → se o label carimba no pivô
  (repaint), infla a cascade → **computar cascade CLOSE-ONLY da estrutura de preço** (não do label).
  (2) O edge é CONDICIONAL a estar DENTRO de um fundo real → **deploy live exige um DETECTOR DE FUNDO
  CAUSAL** (substituir as marcas manuais; o `bottom_detector_structural` é causal mas a classe estreita
  recall só 13/42 = o nó da região a resolver).

## 3. CAMADA INDICADORES (DEPOIS do mapeamento estrutural — `lab_g` + location reader)
Feature-set rico, por regime: `box96/box480` (pos), `atr_spike`, `sweep_depth`, `rsi_min8`/`rsi_div`,
`flush_wick`, `rec_speed`, `ema21/50_dist`, `h1_pos`, `pullback_depth`, `downleg_eff` (=knife),
`reclaim_atr`, booleanos `swept/sellbub/decel/knife/in_demand/htf_dem`. **Location reader:** discount
(`dealing_range_pos≤0,4`), `legpos≤0,5`, HTF-demand-quality (fresh/virgin/coincide-top), clean-sky
(runner-room), supply-overhead, not-knife. **Objetivo = RISK-SHAPE** (subir avgR, cortar DD, evitar
facas) — DOIS objetivos, não um. **Confluência-de-indicadores SOZINHA ≠ forte** (Engine 7: avgR 0,1).

## 4. 🚨 DISCIPLINA DE CAUSALIDADE (lições da auditoria DA 2026-07-15)
**FAZER (padrão limpo do `bottom_detector_structural`):**
- Features diárias/semanais: **recuar um período** (`di = bisect(DT, kt−86400)−1`) — usar só barras
  ESTRITAMENTE fechadas antes da decisão.
- Labels (NAS/SMC/zonas/bubbles): gatear por **`known_at`/`born_t`** (first-appearance), nunca estado final.
- SL/outcome R: só barras dentro do **horizonte do trade** (HMAX), SL âncora ≤ entrada.
- Zigzag/pivôs: confirmados no travel (`kt>pt`), nunca o extremo "conhecido" retroativamente.

**NÃO FAZER (lookahead confirmado no `engine7` — resultados contaminados):**
- ❌ Regime diário com o **close/high do PRÓPRIO dia** da decisão (`DAYREG` de `g["c"]`) → injeta
  futuro-intradia na seleção. **O erro mais grave.**
- ❌ **NAS cru por `t`** sem `known_at` (NAS é SHIFT1 repintante) → o top_block dispara com futuro.

## 5. DISCIPLINA DE VALIDAÇÃO (`event_stage2`)
null-dentro-do-fundo (a entrada bate o acaso DENTRO do evento?) · null-episódio · **distribuição de
streak (q50/q95, P(>5))** não só o obs · por-ano (2024/25/26) · recall dos círculos/GT · densidade.

## 6. TEMPLATE CANÓNICO (ordem para engines futuros)
1. **ESTRUTURA** (pivôs causais → regime + terços/retr_up + is_leg_bottom + choch_up → família).
2. **EVENTO** (select bottom-event first; a entrada só vive dentro).
3. **ENTRADA** (cascade+reclaim+hl+oversold dentro do evento).
4. **INDICADORES** (camada de risk-shape POR CIMA do mapa estrutural — subir avgR/cortar DD/evitar faca).
5. **VALIDAÇÃO** (null-dentro + null-episódio + streak-dist + por-ano + recall).
6. **CAUSALIDADE** (recuar-um-dia diário · known_at/born_t labels · horizonte-trade R · NAS SHIFT1).
