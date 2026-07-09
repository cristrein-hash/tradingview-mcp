# SPEC A2-ANCHOR-ONLY — XAU 15M STRUCTURAL LEG ENGINE (2026-07-09, congelada PRÉ-CÓDIGO)

> Aprovação do Cris: o ciclo pullback/reclaim PODE confirmar uma região-âncora, mas NÃO pode gerar
> entrada no próprio evento de confirmação. Região confirmada = zona FUTURA de interesse; entrada só
> em reteste posterior. Esta spec congela as definições; nada é improvisado no código.
> Autoridades: manifest v1.2 (docs/architecture) · spec engine v1.2 · F15 report (BLOCKED, mecanismo
> placement/escala) · DA F0-F1.5. Escopo: SÓ camada de regiões + guards + gate GT. SEM entry/backtest/
> indicadores/produção.

## 0. Epistemologia (a régua do Cris, escrita)
O pecado da N96/N83 e do zigzag banido era **usar o pivô como se conhecido no tempo do extremo**
(entry retroativa). A2-ANCHOR-ONLY corta isso pela raiz: a confirmação (contra-movimento) cria uma
REGIÃO com `known_at` = fecho da barra de confirmação; a região só é utilizável para barras
**t > known_at**; a barra de confirmação NUNCA conta como reteste nem como entry; o fundo descoberto
NUNCA é comprado retroativamente. Mecanicamente o detector de ciclos é um reversor por threshold —
a diferença TODA está no uso: **região para o futuro, nunca trade no evento.**

## 1. Máquina de ciclos (15M nativo, price-only, simétrica)
Estado `d ∈ {UP, DOWN}` sobre barras 15M FECHADAS (F0):
- em UP: `H1` = running max (high) desde a origem do ciclo; **flip UP→DOWN** quando
  `(H1 − close)/ATR15 ≥ r_cycle` → publica **REGIÃO-TOPO** no fecho dessa barra.
- em DOWN: `L1` = running min (low); **flip DOWN→UP** quando `(close − L1)/ATR15 ≥ r_cycle` →
  publica **REGIÃO-FUNDO** no fecho dessa barra.
- ATR15 = SMA-14 de TR (F1, verbatim). Warmup: primeiras 400 barras não publicam (W congelado).
- Início do pullback = flip UP→DOWN (implícito); fim do pullback/reclaim = flip DOWN→UP. Não há
  outra definição de pullback nesta camada.

### r_cycle — grid pré-registado (ÚNICA constante nova calibrável)
`r_cycle ∈ {4, 6, 8}` ATR15. Justificação declarada (não é fit): drops do GT por família = 2,8 ATR
(BULL) / 7,4 ATR (BEAR); o leg-walk que reproduzia a escada do Cris operava a 6 ATR. Seleção: 3 looks
contra PLT/DM (janela ago-out/2025), fasquia ≥9/10 PLT e ≥10/11 DM; empate → r=6 (centro). Config
escolhida CONGELA antes de qualquer leitura dos 42/50/INVALIDO. Todos os looks no ledger.
`rc` de recuperação: NÃO existe constante separada — a confirmação É o flip (mesmo r_cycle, simétrico).

## 2. Regiões (banda, sem constantes novas — heranças congeladas)
- **REGIÃO-FUNDO** (do flip DOWN→UP): `price_low = L1 − 0,1·ATR@L1` (herança SL V1) ·
  `price_high = L1 + 0,7·ATR@L1` (herança tol_anchor).
- **REGIÃO-TOPO** (do flip UP→DOWN): `price_low = H1 − 0,7·ATR@H1` · `price_high = H1 + 0,1·ATR@H1`.
- Política body/wick: extremo = WICK (low/high da barra do extremo). ATR@extremo = ATR15 da barra do
  extremo. Largura min/max: NENHUMA na v1 — distribuição de larguras REPORTADA;
  `DECISION_REQUIRED` se degenerada.

## 3. known_at e proibições (invioláveis)
- `known_at = t_close` da barra de confirmação (t_open + 900).
- `first_valid_bar_after_known_at` = barra seguinte. **Proibido:** trade/uso no bar de confirmação;
  uso antes de known_at; qualquer uso retroativo; entry nesta fase (não existe camada de entry).
- Região é snapshot IMUTÁVEL no known_at; mudanças de status (retested/invalidated) são EVENTOS
  versionados com known_at próprio, append-only.

## 4. Reteste (registo apenas — entry NÃO implementada)
Barra t com `t ≥ first_valid_bar`: reteste se `low(t) ≤ price_high` E `high(t) ≥ price_low` e status
ativo. Conta-se n_retests; primeiro reteste = evento com known_at = fecho de t.

## 5. Estados
`candidate_region` (interno, durante o ciclo — NUNCA publicado) → `confirmed_anchor` (no known_at)
→ `active_anchor` → `retested_anchor` (≥1 reteste) → `invalidated_anchor`.

## 6. Invalidação
- REGIÃO-FUNDO invalida quando um CLOSE < price_low (quebra através). REGIÃO-TOPO: CLOSE > price_high.
  Evento versionado (known_at = fecho da barra da quebra). Região invalidada não volta.
- Idade máxima: `DECISION_REQUIRED` — v1 sem teto; distribuição de idades reportada.
- Nº máximo de retestes: `DECISION_REQUIRED` — v1 sem teto; distribuição reportada.
- Regime incompatível / lower-low destrutivo: NÃO invalidam na v1 (a quebra por close já captura o
  lower-low destrutivo através da banda); anotados para F2.

## 7. Contexto por região (anotação estrutural, satisfaz structural-first)
`context` = macro_regime v5 hour-causal (F1, porte verbatim) no known_at:
BULL→`BULL_PULLBACK` · RANGE→`RANGE_BOTTOM` · BEAR→`BEAR_CAPITULATION` (regiões-fundo);
regiões-topo → `TOP_<macro>`. Anotações adicionais (report-only): depth_atr do ciclo,
pos96 = posição do extremo no range das 96 barras anteriores (métrica top-buy-trap, congelada:
trap se pos96 > 0,67 em região-fundo).

## 8. Output — ledger append-only
Cada região:
```json
{"region_id": "...", "context": "BULL_PULLBACK|RANGE_BOTTOM|BEAR_CAPITULATION|TOP_*",
 "price_low": 0.0, "price_high": 0.0, "extreme_px": 0.0, "extreme_t": 0,
 "created_from_start_bar": 0, "created_from_end_bar": 0, "known_at": 0,
 "first_valid_bar_after_known_at": 0, "latency_bars": 0, "depth_atr": 0.0, "pos96": 0.0,
 "source": "RAW_HD", "status": "active|retested|invalidated", "n_retests": 0,
 "no_entry_on_confirmation": true}
```
Eventos de status em stream separado, append-only, com known_at próprio.

## 9. Gate GT (regiões, NÃO trades) — ordem que protege a honestidade
1. **Seleção r_cycle vs PLT/DM** (3 looks; marks↔regiões pelo extremo: |Δpx| ≤ 0,7·ATR e |Δt| ≤ 2d,
   matcher verbatim F1.5 para comparabilidade). Fasquia ≥9/10 e ≥10/11; baseline a bater com folga:
   PLT 6/10 · DM 4/11.
2. **FREEZE do r_cycle.**
3. **Leitura ÚNICA (ordem explícita do Cris)** dos 42 VELA DE FUNDO + 50 círculos + 4 INVALIDO:
   - cobertura CAUSAL: no instante da marca, existia região-fundo ATIVA (known_at < t_marca, não
     invalidada) cuja banda contém o preço da marca; regiões criadas pela MESMA queda
     (known_at > t_marca) = "late/reconstrução", contadas à parte, NÃO contam como cobertura;
   - recall por família (contexto da região) · distância temporal região→marca · distância de preço
     à banda dos misses · rejeição dos 4 INVALIDO (nenhuma região ativa a conter o preço) ·
   - precision: % regiões-fundo sem NENHUM GT (42∪50) tocado na vida da região · regiões/semana ·
     FP/dia · top-buy traps (pos96>0,67) · latency (known_at − extreme_t).
   Declaração: esta leitura consome os 13 BULL-2026 antes reservados — POR ORDEM EXPLÍCITA do Cris
   (região-nível); qualquer iteração posterior = looks novos declarados.
4. Falhou → `BLOCKED_A2_GT_GATE`, relatório de falhas SEM maquiagem (miss a miss, causa provável:
   pullback detection / band width / contexto / known_at tarde / invalidation / escala).

## 10. Anti-lookahead (guard obrigatório, FASE 3)
Truncation VERDADEIRO (Data RECONSTRUÍDO na série truncada — exigência do DA F0-F1.5): em amostra de
known_ats, a região existe exatamente a partir do known_at e nunca antes; known_at monotónico no
stream; preços imutáveis pós-publicação; retestes antes de known_at = ignorados (teste explícito);
bar de confirmação nunca é reteste; zero campos de futuro/outcome; zero membership N96/N83; **GT do
Cris NUNCA entra na construção das regiões — só na avaliação** (import-guard no builder).

## 11. Critérios de continuação (para F2, DEPOIS de nova ordem)
PLT/DM com folga vs 6/10+4/11 · FP/dia controlado e reportado · INVALIDO rejeitados ou explicados ·
recall alto NÃO basta com regiões demais · ponte losers ≤10 declarada (C6: o ledger de regiões é
condição necessária, nunca suficiente). STOP obrigatório após o gate.

## 12. DECISION_REQUIRED (Cris)
D1 idade máxima de região · D2 teto de retestes · D3 largura min/max da banda (se distribuição
degenerada) · D4 uso das regiões-topo em F2 — **parcialmente resolvido pelo v1.1 §13.2 (canal
converted_support medido já no gate)**.

## 13. ADENDA v1.1 — edits do DA pré-código (BLOCKED_A2_SPEC_AMBIGUOUS → resolvido; vinculante)

### 13.1 Conflito com o manifest (edit 1)
Manifest patchado (v1.2): a stop-condition "pivô confirmado-por-rally" reescrita na forma
EPISTÉMICA — o proibido é o USO retroativo do pivô (entry no evento de confirmação / backdating);
o reversor por threshold com known_at=fecho da confirmação e uso só-futuro está PERMITIDO por
decisão do Cris (A2-ANCHOR-ONLY, 2026-07-09). r_cycle {4,6,8} + pos96(96; 0,67) adicionados ao grid.

### 13.2 Polaridade — canal CONVERTED_SUPPORT (edit 2, opção a — a tese dos 35 prints)
REGIÃO-TOPO quebrada por CLOSE > price_high **NÃO morre**: evento versionado
`converted_support` (known_at = fecho da barra da quebra). A banda mantém-se; passa a ser suporte
esperado. O gate §9.3 reporta cobertura causal por DOIS canais SEPARADOS: (a) região-FUNDO ativa;
(b) região-TOPO convertida ativa. Probe GT-free do DA: (b) cobre ~40,3% dos fundos da máquina em
r=4 vs ~15,7% de (a) — medir ambos é obrigatório. Região-fundo quebrada por close < price_low fica
invalidada SEM conversão na v1 (programa LONG; conversão para resistência = F2/SHORT, fora de escopo).

### 13.3 Dente do passo 3 (edit 3)
O passo §9.3 é **REPORT-PARA-DECISÃO-DO-CRIS, sem dente automático** (declarado; o ponto de operação
é dele). O dente automático existe SÓ no passo 1 (PLT/DM ≥9/10 e ≥10/11). **Sem contingência de grid
para A2: 0/3 configs a passar = BLOCKED_A2_GT_GATE, sem expansão silenciosa.** Risco declarado: o
drop BULL mediano do GT (2,8 ATR) está ABAIXO do grid inteiro — o modo de reteste curto (lag
1,5-2,2h) é estruturalmente inalcançável pelo canal região-reteste; limitação declarada, não defeito.

### 13.4 Métrica do trap real (edit 4)
Além de pos96: **taxa retested→invalidated por contexto** (o trap dominante do F2: compra o reteste
e a perna fecha através — probe: 92,9-95,8% dos fundos retestados são depois invalidados). Reportar
por família e por canal (fundo vs converted_support).

### 13.5 Resolução das 12 ambiguidades (edit 5 — nada improvisado no código)
1. Origem do ciclo pós-flip: o tracking do novo extremo começa NA BARRA DO EXTREMO anterior
   (extremo-em-diante), não na barra do flip.
2. Estado inicial: d=UP na barra 0; H1/L1 seeded com high/low da barra 0.
3. Warmup: só as primeiras 400 barras do stream (F0 provou fronteiras de bloco contíguas no preço
   ⇒ sem warmup por bloco). Região só publica se extreme_t E known_at estiverem fora do warmup.
4. Mesma barra toca banda E fecha através: INVALIDAÇÃO tem precedência; NÃO conta reteste (conservador).
5. pos96: janela = 96 barras estritamente ANTERIORES à barra do extremo; posição de extreme_px;
   96/0,67 = constantes congeladas report-only, registadas no manifest.
6. Empate no passo 1: score = hitsPLT+hitsDM entre configs que PASSAM a fasquia; escolha r=6 se
   entre os passantes, senão o passante mais próximo de 6.
7. Cobertura §9.3: t_marca = t da shape; preço = price da shape; PRIMÁRIO = preço dentro da banda
   EXATA; near-miss reportado à parte = fora da banda mas ≤0,7·ATR da borda (herança tol_anchor).
8. Marca em warmup = UNSCORABLE; marca antes da 1ª região publicada = MISS contado e listado;
   região invalidada antes da marca = MISS (já definido).
9. "Vida da região" (precision) = [known_at, invalidação] (ou fim do stream); toque GT = t_marca
   dentro da vida E preço dentro da banda exata.
10. `confirmed_anchor` ≡ `active_anchor` (colapsados; publica-se como active).
11. created_from_start_bar = índice da barra do extremo de ORIGEM do ciclo;
    created_from_end_bar = índice da barra de CONFIRMAÇÃO.
12. Truncation TRUE (Data reconstruído): n=60 known_ats amostrados (desvio de 200 declarado —
    custo de reconstrução total do Data por amostra; compensado por checks full-stream de
    monotonicidade/imutabilidade em TODAS as regiões).
Extra (F do DA): campo `no_entry_on_confirmation` deixa de ser boilerplate — é COMPUTADO
(`first_valid_bar_after_known_at > created_from_end_bar`), asserido no guard.
