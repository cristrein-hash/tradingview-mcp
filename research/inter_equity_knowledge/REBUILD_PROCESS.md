# RECONSTRUÇÃO DO READER SOBRE O LIQUIDITY METHOD — PROCESSO DISCIPLINADO (28/08)
Ordem Cris: auditar os erros cometidos + processo limpo passo-a-passo para NÃO inventar/errar de novo.

## A. AUDITORIA DOS MEUS ERROS (hoje, 28/08 — padrão e antídoto)
| Erro cometido | Padrão-raiz | Antídoto no processo |
|---|---|---|
| L2 lido errado 3× (exit-only→interno→afinal envia) | Concluir de MEIA leitura de código | Regra: seguir a cadeia até ao emissor final ANTES de afirmar; mostrar a linha de código na afirmação |
| "Impossível juntar verdict↔reasoning" (estava num ficheiro só) | Declarar impossível sem busca exaustiva | Proibido afirmar negativo sem mostrar o comando de busca corrido |
| Zona 4563-86 funda demais (mercado virou em 4582) | Ancorar em extremos, não no nível raso operável | O LIQUIDITY METHOD manda: nível = pool COM sweep, entrada no stab, não no miolo |
| distrib V15 tautológica; pool-sweep-12b sem validade de construto (0/11 nos teus trades) | Mecanizar por palpite sem calibrar no ground truth | TODO detetor novo valida-se PRIMEIRO contra trades reais teus/do método (construct validity) antes de backtest |
| −229R do sweep_reclaim (dedup errado, não-causal, TF misturado) | Medir à pressa sem selar unidade/causalidade | Prereg sela unidade (bar_time), causalidade e split por TF ANTES de correr; DA sempre |
| E1 R8 armado no topo de zona larga (SL 83pt) | Não distinguir pavio de zona | Regra do método: entrada no FUNDO com pavio; SL curto atrás (já corrigido) |
| Textos longos/validações apesar de ordens repetidas | — | Guard reforçado (frases banidas); factos e decisão apenas |

## B. PROCESSO DE RECONSTRUÇÃO (passo-a-passo, cada passo com gate de saída)
REGRA GERAL: um passo de cada vez; nenhum passo seguinte sem o gate do anterior PASS; cada passo =
prereg selado + implementação mínima + selftest + DA + validação contra ground truth; Cris aprova a
passagem de cada gate. NADA live sem forward.

**P0 — GROUND TRUTH (primeiro, porque tudo valida contra isto)**
Construir o dossiê de casos: (a) os teus trades reais (journal + drawings + declared_log, consolidados
hoje); (b) os trades dos vídeos dele (níveis/datas citados nos breakdowns). Cada caso: instante, nível,
direção, SL, alvo, resultado. GATE: tu confirmas a lista.

**P1 — DETETOR DE INDUCEMENT (a peça que falta; núcleo do método)**
Mecanizar: último BOS que induziu retail (extremo rompido) + o lado induzido. Fontes: smc_labels
(BOS/CHoCH) + context_structure — consumir, não reconstruir. GATE: nos casos P0, o detetor marca o
inducement que o método marcaria em ≥80% (medido, não afirmado) + DA.

**P2 — POOLS VÁLIDOS (liquidez real vs falsa)**
Refinar liquidity_map com as regras dele: pool = nível RESPEITADO à esquerda (reação impressa) —
"liquidez da esquerda" prioritária; extremo só-sweep ≠ alvo. GATE: pools do mapa cobrem os níveis dos
casos P0 (medido) + DA.

**P3 — GATILHO LB (sweep+trap → entrada no stab)**
Compor: pool válido (P2) + inducement do lado oposto (P1) + sweep do extremo induzido + LB impresso
(stab→reversão→afastamento; reclaim_hold já aproxima) → candidato de ENTRADA no stab, SL atrás do LB,
alvo = próximo pool oposto do roadmap (não 3R fixo). GATE: replay nos casos P0 reproduz as entradas
dele/tuas (timing e nível) + DA.

**P4 — READER = JUIZ DA NARRATIVA**
O reader (Opus) julga só o que o método diz ser discricionário: bias narrativo (Asia/London/NY, news,
inside-day), LB-operável vs só-reação, "no man's land". Prompt reescrito do LIQUIDITY_METHOD.md —
substituindo as camadas herdadas que conflitam. GATE: nos casos P0, aprova os bons e recusa os maus
(medido) + DA.

**P5 — SHADOW FORWARD**
Tudo em shadow no teu pessoal (padrão pool-limit), scoreboard automático, critérios de sucesso selados
ANTES. GATE: N mínimo + leitura, veredito Cris. Só depois: Telegram/grupo.

**OBSOLESCÊNCIA (a confirmar no P3):** o forward de medição do E1 atual e rules antigas do E1 ficam
provavelmente obsoletos — o pipeline novo substitui candidatos por inducement→sweep→LB. Decisão formal
no gate do P3, não antes (não desligar nada até o novo provar nos casos P0).

## C. DISCIPLINA DE EXECUÇÃO (aplica-se a todos os passos)
- Nada de "acho": toda afirmação sobre código vem com ficheiro:linha; toda medição com script commitado.
- "NÃO ESPECIFICADO" do método nunca é preenchido por palpite meu — ou deriva dos casos P0, ou pergunta.
- Um passo por sessão de trabalho; relatório curto por gate; Cris decide a passagem.
