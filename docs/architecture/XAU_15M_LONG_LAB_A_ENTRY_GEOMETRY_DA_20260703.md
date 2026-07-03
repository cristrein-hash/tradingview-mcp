# LAB A RODADA 2 — DA ADVERSARIAL (2026-07-03)

> Rodada 1 (DA da execução pós-sinal) no git history (c95d711). Este doc = DA da RODADA 2 (entry redesign P1-P6).

Dois DAs reais: (i) **DA-pré** (perspectiva 5 do discovery `wf_fe1ae2d6-cfe`) — impôs as 14 exigências de protocolo do prereg §5 ANTES da execução; (ii) **DA pós-resultado independente** (subagent real; scripts `_DA_lab_a2_attack{,2,3}.py`, salvos, **não commitados** — regra de governança cumprida, git log verificado).

## Bug MATERIAL encontrado (corrigido e re-executado)
**Null do P1 sem piso de risco:** o null de antecipação aleatória entrava no close de p+1 exigindo só risk>0, enquanto o P1 é obrigado a respeitar piso $6,40/0,35ATR. ~75/127 antecipações do null ficavam abaixo do piso → risco mediano $8,20→$5,27 → R mecanicamente inflado (6 hits no RCAP20 vs 0 na base). As manchetes pré-correção eram **FALSAS nos dois sentidos**: nem "o filtro escolhe piores que aleatório (p=1,000)" nem "confirmação custa ~88R" (artefato de risco-minúsculo; Δcusto do null era até NEGATIVO −30,1). **Null justo** (like-for-like: mesma mistura 53@p+1/74@p+2, piso aplicado, elegíveis 176/246): mediana **+28,8**, p=**0,726** — P1 é indistinguível de antecipação aleatória elegível-com-piso. O null COMBINADO do P6 tinha o mesmo bug (p=0,998→**0,700**). Números publicados = pós-correção.

## Bug de reporte
P5 "streak q95 igual" é **por construção** (pesos>0 preservam o sinal W/L de cada trade — a sequência é idêntica; verificado 435/435). Nota adicionada ao output; nenhum claim de streak do P5 é permitido.

## Ataques dissolvidos (verificados com código)
- **Horizonte ancorado no fill vs cj:** Δ=+0,000R exato; 0 exits por fim de horizonte (HMAX480≫2 barras).
- **SL da antecipação:** `min(low[p..cj])==low[p]` em 0/435 (fractal k3 garante) → SL causal em p+1. cj−p=3 em 4502/4502.
- **EMA aproximada:** 0/435 decisões mudam.
- **P2 same-bar:** 4 casos; sensibilidade total do tratamento 4,3R — imaterial contra déficit de −71R. Kill-pass (misses avgR −0,56) genuíno.
- **P3 1-corte:** implementação correta (q80=164 plausível: universo min0/q50 51/max552). Lente supply passa em 20,1% do universo mas 0,9% dos 435 — **os gates da base já excluem contexto de teto**; ≥3/4 votos = 2,3% até no universo. Achado honesto, não bug.
- **Determinismo:** 2 reruns byte-idênticos (stdout+JSON); null do lab robusto a seeds 7/99/2024.
- **Reconciliação P6:** exata (P6≡P1; skips 0; decomposição fecha).
- **FN-gate:** aritmética reproduzida. **Nota obrigatória: a própria BASE OFICIAL_FN falha o gate em WR_liq≥50 e streak≤6 (4/6)** — as falhas dos variantes nesses eixos são pré-existentes.

## Leituras obrigatórias de escopo (o relatório DEVE carregar)
1. **P1 look-ahead estrutural do universo:** em p+1/p+2 o fractal k3 nunca está confirmado — a LISTA de onde o trigger dispara condiciona em confirmação futura (as condições de disparo em si são causais).
2. **Classe fantasma não-coberta:** o universo só tem fractais CONFIRMADOS. Estimativa DA por varredura bruta (proxy, acc 88,3%): proto-candidatos que falham confirmação = 5,3% (11 vs 209), avg −0,34 NET → drag ≈ **−2,2 a −3R** nas 127 antecipações. Tradeable P1 honesto ≈ **+252 NET (~+19R vs base)**. Estimável e pequeno — não é BLOCKED.
3. **Residual dos gates cj (knife/h1_pos/HTF em p+1/p+2):** declarado mas **NÃO bounded** pelo phantom scan (que cobre população, não deriva temporal dos features).
4. **P5 leitura única honesta = risco-normalizada:** R/unidade-alocada 0,537→0,572 (+7%); DD obs −14,2→−5,9; NET absoluto cai a 49% (importa p/ target de lucro prop).
5. **Multiplicidade:** 7 tentativas no ledger; nada com p<0,05 sob nulls corretos (0,65-0,73 em tudo). O único positivo de painel (P1 +23,5 / ~+19 tradeable) é **timing genérico com piso**, não informação do deslocamento — o valor causal do disp lens é CONTROLE DE FANTASMAS (limita entradas live-only a 147/−2,3R), não seleção de R.

## Veredito DA por hipótese (pós-correção)
**P1** POSITIVO_COM_RESSALVA_GRAVE · **P2** CONFIRMA_NEGATIVO (kill-pass real: misses são losers — física invertida vs limit, mas compressão de R domina) · **P3** CONFIRMA_NEGATIVO (sem poder discriminativo na base) · **P4** CONFIRMA_NEGATIVO (runner-kill 14; não-monotônico) · **P5** POSITIVO_COM_RESSALVA_GRAVE (melhora risco-normalizada ~7%; NET −51%) · **P6** ≡P1.
