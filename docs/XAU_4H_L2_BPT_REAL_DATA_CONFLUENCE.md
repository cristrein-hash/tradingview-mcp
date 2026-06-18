# XAU 4H L2/BPT — Confluência com DADOS REAIS (volume Session VP + VP + RSI-div)

**Status:** `DIAGNOSTIC · REAL_DATA · BREAKTHROUGH_RETRACTED · HONEST` · **Data:** 2026-06-18
Cris aprovou volumetria real + RSI-div real. Extraí do gz SVP: volume REAL, Session VP (POC/VAH/VAL), RSI por barra 4H. Sem outcome/produção/SLIM.

---

## 1. A correção crítica de dados

O "breakthrough" volume×1D-bear era **artefato do tick-volume do frozen** (`raw_features_2020_2026.jsonl`). Com **volume REAL (Session VP gz)**:

**1D-bear subset, volume-climax REAL:**
| | E1(W) | E17(W) | E6(T) | E7(T) | E11(T) | E36(T) | E37(T) |
|---|--:|--:|--:|--:|--:|--:|--:|
| tick-vol (errado) | 0.78 | 1.34 | 1.79 | 1.9 | 1.82 | 1.64 | 1.95 |
| **vol REAL** | **4.88** | 1.01 | 1.64 | **6.8** | 1.64 | **6.32** | 2.01 |

Com volume real os grupos **interleaveiam** (1.01·W, 1.64·T, 1.64·T, 2.01·T, 4.88·W, 6.32·T, 6.8·T) — **sem gap, não separa**. E1 (fundo COVID) é capitulação real (4.88), não "volume baixo" (0.78). **O gate está retratado.**

**Lição:** volume do frozen = tick-volume NÃO-confiável. Usar SEMPRE o volume real do Session VP gz (`/tmp/svp_bars.jsonl`).

## 2. Outros sinais reais — também não separam limpo

- **Session VP** (POC/VAH/VAL): `dist_above_VAL` WIN med 0.67 vs REM-loser 0.20 (winners + acima do VAL, fraco); `inside_VA` 3/9 win vs 3/7 loser (nada); `above_VAH` 5/9 vs 3/7 (nada).
- **RSI bullish divergence (real):** presente só em E27, E30 (winners) — confirmação POSITIVA rara (2/9), mas ausente em 7/9 winners → não serve de gate (não dá pra bloquear pela ausência).
- **NAS short / bubbles:** já vistos, não separam.

Nenhum indicador isolado separa, **agora confirmado com dados reais** (não tick-volume).

## 3. O que isto consolida (honesto)

O subconjunto reversão-de-fundo (E1/E17/E27/E30/E40) × bounce-em-bear (E6/E7/E11/E39) é **indistinguível na entrada** — confirmado com volume real, Session VP e RSI-div real. A diferença é o caminho forward (outcome). O achado estrutural anterior estava certo; o "breakthrough" foi um falso positivo de dados ruins que a insistência do Cris por dados reais corrigiu.

## 4. Subproduto valioso

Dataset real extraído e reutilizável: `/tmp/svp_bars.jsonl` — por barra 4H: volume REAL, Session VP (POC/VAH/VAL), RSI. Para todas as próximas análises de volume/VP usar este, nunca o tick-volume do frozen.

## 5. Caminho (inalterado, agora firmemente justificado)

Sem filtro de entrada limpo para esse subconjunto. Edge = **SL estrutural (3-4 ATR sem teto) + aceitar understood-losers + extreme-top E24 como único filtro de topo** → **medir outcome real por episódio (lift vs base rate), recall-gate primeiro.** É a pergunta que decide se há edge.

## 6. DA appendix
- Validou com dados REAIS (não tick-volume)? ✅. Retratou o falso lead na hora? ✅ (memória + doc corrigidos).
- Não defendeu o resultado anterior? ✅. RSI-div/VP reais testados? ✅. Produção intacta? ✅.

**DA verdict: PASS — breakthrough retratado (artefato de tick-volume); com volume REAL + Session VP + RSI-div real NENHUM indicador separa o subconjunto; achado estrutural confirmado; dataset real salvo; caminho = outcome real com SL estrutural. Memória corrigida no mesmo dia (governança).**

---
*Scripts: extract_svp.py, deep_confluence.py, revolume.py. Dataset: /tmp/svp_bars.jsonl. Sem outcome/produção.*
