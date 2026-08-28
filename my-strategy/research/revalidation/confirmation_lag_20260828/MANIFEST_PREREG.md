# LAG DE CONFIRMAÇÃO — m=3 vs m=2 vs m=1 vs REJEIÇÃO-NA-VELA (prereg selado 28/08, ordem Cris)
PERGUNTA: qual janela de confirmação de fundo produz MELHOR resultado real no ouro 15M — e quanto lag
custa? O m=3 atual nunca foi validado como ótimo (é conserto de lookahead + heurística v0 no mapa).

## Braços testados (mesma base, só muda o TIMING do gatilho; tudo o resto do A1/A2 igual)
- m3: swing-low fractal m=3 (ATUAL) — low[p] menor de [p-3,p+3], confirmado em p+3
- m2: fractal m=2 — confirma em p+2 (1 barra mais cedo)
- m1: fractal m=1 — confirma em p+1 (2 barras mais cedo)
- rej: REJEIÇÃO-NA-VELA (o método do Cris) — sem esperar swing: barra cujo LOW fura o low anterior
  (>=1) E fecha de volta acima do open E no terço SUPERIOR do range da própria barra = fundo na própria
  vela (lag 0). Entrada = fecho dessa vela; SL = low dela −0.1ATR.
Contexto uptrend + guarda de escala IGUAIS aos 4 braços (só o timing muda). Alvo 3R fixo (comparável).

## Métricas seladas
Por braço: N, WR, sumR, avgR, maxDD, streak, por-semestre, LAG mediano (barras entre fundo real e
gatilho), preço-de-entrada vs fundo (quanto pior por chegar tarde). Custo 0/0.2/0.35R.
Unidade = episódio (gap 8). RAW 15M canónico 2 anos. Null block-shuffle sobre o gap avgR do melhor
braço vs m3. Jackknife semestral. DA adversarial OBRIGATÓRIO (foco: rej-na-vela tem lookahead? o
fecho-no-terço-superior é causal? m1/m2 repintam?). Gates = referência; veredito = Cris.
