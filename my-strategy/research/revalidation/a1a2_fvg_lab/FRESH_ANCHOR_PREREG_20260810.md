# PRÉ-REGISTO — Fix do anchor-lag do A1/A2 (fundo fresco) · 2026-08-10

**Congelado ANTES de correr.** Origem: 10/08, A1/A2 perdeu bounce em V (4316→4349) por dessincronização
do anchor (argmax-global da perna instabiliza; fundo fresco reconhecido tarde → MB3 já antigo). Detalhe:
[[feedback_a1a2_leg_anchor_lag_limitation]]. Plano: Plan agent (design + protocolo).

## Causa-raiz (congelada)
`detect()`: `hh_i=argmax H[i-96..i-9]` (degrau) → `j=argmin L(hh_i,i]` salta com hh_i → gate `i-j>24`
("fundo velho") e gate `ei==N-1` ("MB3 corrente") tornam-se **não-simultaneamente satisfazíveis** num
bounce rápido. Instabilidade do ANCHOR, não threshold.

## Candidatos (princípio escolhido ANTES do gráfico de hoje: "ancorar a perna a estrutura local recente,
## não a extremo global de 96 barras")
- **A (recomendado):** `hh_i` = swing-high FRACTAL confirmado mais recente (m=3, tudo ≤ i), não argmax global.
- **C:** `j` = swing-low fractal mais recente ≤ PB_WIN; depth vs high local (desacopla j de hh_i).
- **B (só comparação):** alargar `ei==N-1` para `N-1-W≤ei≤N-1`. Trata sintoma, compra tarde → não primário.
Régua-mãe (`causal_entry`: MB3, fractal, SL low-real−0.1ATR, 3R) e thresholds (PB_WIN, depth, escala 2.5ATR)
**congelados** — só muda a definição do anchor.

## Protocolo (harness de hoje, read-only)
`fresh_anchor_study_v4.py`: baseline = `detect_at` de v2 (verbatim); + `detect_at_A/C/B`. Varre cada barra,
cataloga em `ei==i`, outcome SL-first HORIZON na série completa. Gate BULL causal (v3, Layer1). Mede:
(1) **recovery** = firings do candidato que o baseline rejeitou por "fundo velho" com fundo fresco (o
4316→4349 tem de estar lá); (2) **GT kills** nos 32 fundos A (A1=14+A2=18); (3) **painel false-signal
BULL-gated** baseline vs candidato (N·WR·sumR·avgR·DD·ret/DD·streak + bandas bounce% + NULL).

## REGRA DE DECISÃO (congelada — APROVA sse TODAS, na população BULL)
- **R1 Recovery:** recupera ≥70% do conjunto desync-rejeitado (e inclui o move de hoje).
- **R2 Sem kills:** mata 0 dos winners GT (32 A).
- **R3 Agregado não pior:** `sumR ≥ base` E `avgR ≥ base` E `ret/DD ≥ base`.
- **R4 Firings extra pagam:** WR dos firings incrementais ≥ WR_base − 5pp E share com bounce%>60 ≤ 25%.
- **R5 NULL morto:** null random-entry continua sem edge.
REJEITA se falha qualquer R1–R5. Empate → maior ret/DD, menor late-band; estrutural (A/C) > timing (B).
PASS autoriza **só forward pré-registado**, NUNCA edição live direta. Daemon intocado até forward confirmar.

## NÃO TOCAR
`a1a2_runtime.py` (detect/constantes/scale-guard/ei==N-1/dedup/macro-gate/Telegram) · `a1_causal_entry.py`
(mecânica) · GT JSON · RAW · baseline `detect_at` de v2 (copiar, não mutar). Zero tuning ao move de hoje.
