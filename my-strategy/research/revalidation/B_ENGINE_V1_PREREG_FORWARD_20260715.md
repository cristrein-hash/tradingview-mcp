# PRÉ-REGISTO FORWARD — Engine de B v1.1 (retomada no FUNDO de range plano)

**Congelado em: 2026-07-15.** Documento de compromisso. Regras, métricas, vetor de falha, null e
critério PASS/FAIL abaixo ficam **imutáveis**. Qualquer alteração pós-forward = **novo prereg + novo
forward** (proibido mover a baliza depois de ver resultados). Mesmo formato de A1/A2
([[A1_MB3_ENTRY_PREREG_FORWARD_20260714]]).

Autoria: Claude (desenho) + Cris (aprovação, caminho (a) + refino spring). Status: **DESENHO in-sample
selado; validação = FORWARD.**

---

## 0. Porquê
Camada B = LONG em range. Estudo de caso (2026-07-15) provou: (1) accum-vs-distrib **não** é
discriminável no macro → gate por `RANGE_ORDERLY` (crash-born=SKIP, [[project_b_macro_gate]]); (2) os
fundos B do GT estão **maioritariamente perto do TOPO** do range plano (survivorship) — comprar
continuação aí = **streak-killer** (experiência do Cris). Logo B verdadeiro = **retomada no FUNDO**
(porção baixa do range). N=4 seed (B#1-4). Este prereg congela a regra ANTES de dados novos.

**Canon (Cris):** SEM OOS/held-out. "Dados virgens" = o FUTURO (próximos fundos B reais).

---

## 1. HIPÓTESE ÚNICA (congelada)
> Num range plano ORDERLY, comprar o FUNDO (porção baixa, pos ≤ 40% da banda causal) com gatilho
> **MB3 + SPRING** tem **expectância positiva a 3R** e **bate o null** (buy-any-dip na porção baixa).
> O gate de posição é a contribuição principal (evita o streak-killer do topo); o spring é refinamento.

---

## 2. REGRAS EXATAS (congeladas; implementação-mãe = `b_engine_v1.b_signal`, commit a seguir)
Fonte: **RAW 15M direto do HD**, barras fundidas. Tudo causal close-only.

**2.1 Gate macro:** `b_macro_gate.gate_at(t)` = `RANGE_ORDERLY` (crash-born `RANGE_POST_CRASH` = SKIP).

**2.2 Banda causal:** `support = p10 dos lows`, `resist = p90 dos highs` do **range-so-far** (do onset
1D do RANGE até t). Aterra ~[3245-3450] (frame do Cris) sem hardcode.

**2.3 Gate de posição:** `pos = (anchor_low − support)/(resist − support)`. Entra **só se pos ≤ 40%**
(porção baixa / suporte). Rejeita continuação perto do topo.

**2.4 Gatilho MB3 + SPRING:** MB3 = 1ª barra verde que fecha acima do high anterior após o low-âncora
fractal (a1_causal_entry). **SPRING** obrigatório: `anchor_low < suporte_imediato − 0.1ATR` (varreu o
penúltimo swing-low) **E** `entry > suporte_imediato` (reclaim). Refino testado vs null (spring 45% vs
39%; absorção REJEITADA por piorar 27%).

**2.5 SL e alvo:** `SL = low_real − 0.1·ATR` (low-real do pullback, [[project_a1_a2_entry]]);
`target = entry + 3·(entry − SL)`; outcome **SL-first** barra-a-barra, horizonte 480 barras.

---

## 3. MÉTRICAS (por fundo forward)
hit-3R (WIN/N), LOSS, OPEN · **streak** (máx losses consecutivos, restrição FN) · R/ATR (marcar tight-R
<1,65 = fill otimista) · **expectância líquida** com custo real · null per-fundo · posição na banda.

---

## 4. VETOR DE FALHA DECLARADO
**Distribuição QUIETA** (o range plano quebra para baixo sem crash — o `b_macro_gate` não a apanha, recall
0,20). Invalidação = close decisivo abaixo do suporte / flip macro→BEAR fecha o gate. Medir no forward
quantas entradas morrem por quebra do fundo (não por SL normal).

---

## 5. NULL (declarado)
Buy-any-dip na porção baixa gated (500× entrada aleatória, mesmo SL/3R). In-sample: baseline **39%** ·
spring **45%**. MB3+spring tem de **bater o null** no forward (agregado).

---

## 6. CRITÉRIO PASS / FAIL (congelado AGORA)
**N mínimo:** ≥ **20 fundos B forward** (~meses; ranges planos são raros). Antes = **INCONCLUSIVO**.

**PASS** exige TODAS:
1. hit-3R **≥ 45%** (≥ o spring in-sample; acima do breakeven 3R de 25%).
2. streak **≤ 5** (FN).
3. **bate o null** agregado (buy-any-dip na porção baixa).
4. **Expectância líquida positiva** com custo real.
5. Gate de posição **não deixa passar** entradas de topo (pos > 40%) — auditoria da disciplina.

**FAIL** se: hit-3R ≤ 33%, **ou** streak > 5, **ou** não bate o null, **ou** expectância ≤ 0, **ou**
o gate falha (entradas de topo passam).

**PARCIAL:** se PASS exceto pela distribuição-quieta (vetor §4 explica os losers) → novo prereg com
refino de invalidação.

---

## 7. PROTOCOLO FORWARD
Cada novo fundo B (range plano ORDERLY, identificado pela leitura do Cris/stack) é pontuado por
`b_forward_score.py` (usa `b_engine_v1.b_signal`): gate + posição + spring + MB3 + SL/3R + null.
Sem alterar regras. Acumular até N≥20, então aplicar §6. Árbitro final = ops live/proxy reais do Cris.

---

## 8. REFERÊNCIA IN-SAMPLE (desenho — NÃO validação)
**Seed N=4 (B#1-4), gate KEEP 4/12 (rejeita B#5-12 = topo/rutura = streak-killers):**
- MB3+spring: **3 WIN · 0 LOSS · 1 OPEN** (B#1). Todos os 4 são springs.
- Spring vs null (range plano 2025): **45% vs 39%** (+6pp; absorção rejeitada 27%).
- **Caveats honestos:** N=4 = seed; UM único range; spring modesto (+6pp); o **gate de posição é a
  contribuição principal**, o gatilho não está provado. null alto em B#2/B#3 (88/90%) = buy-any-dip já
  ganha aí. Forward = juiz.

---

*Fim. Congelado 2026-07-15. Não editar §1-§6 após esta data — refinamentos = novo doc.*
