# PREREG — PRÓXIMO TESTE MÍNIMO DO CONTEXTUAL READER 15M (2026-07-09, v1.1 pós-DA)

> Pequeno por desenho. NÃO é lab. NÃO roda agora — só com ordem do Cris. Sem entry, sem backtest,
> sem indicadores. RAW HD only. Looks contados. v1.1 aplica as correções do DA do reset
> (`XAU_15M_CONTEXTUAL_READER_RESET_DA.md`): A1 definições congeladas/contínuas · A2 objetivo
> reescrito · A3 medidor não arbitra · A4 visual do Cris no fluxo · A6 reprodutibilidade · A7 cache
> · A8 janela fixa em vez de "perna-mãe" livre.

## Objetivo (reescrito — DA A2)
**DEFINITION-FREEZE CHECK, não verificação de separação.** Os valores D1-D3 dos 20 episódios já são
conhecidos dos dossiês (as 3 leituras foram destiladas DELES — resultado parcialmente garantido por
construção). O que este teste verifica: se as operacionalizações CONGELADAS abaixo reproduzem a
narrativa dos dossiês episódio a episódio, e onde divergem. Calibração de leitura; validação = só em
episódios VIRGENS, BLIND, em rodada futura.

## Amostra (congelada)
20 episódios dos 34 dossiês: 10 winners (A1-A10) vs 10 negativos (B1-B4 + C1-C6). Outcome-contaminada
por construção (declarado).

## Medições congeladas (DA A1/A8 — o script REPORTA CONTÍNUO; não corta, não vota, não decide)
- **D1 — estado da perna-mãe:** barras desde o último novo-low + lista de renovações de low nas
  últimas 192 barras (concentração/ausência). O registo TERMINADA/EXAURINDO/VIVA é do **READER**
  (leitura sobre os números + path), nunca do script.
- **D2 — proporcionalidade (janela FIXA, não "perna-mãe" livre — DA A8):** devolução do episódio em
  ATR ÷ range das 384 barras anteriores em ATR + pos384 do candidato. Limitação declarada: 384 barras
  é proxy de perna-mãe (a definição de perna-mãe operacional não existe ainda — é trabalho do Reader,
  não deste script).
- **D3 — bounces falhados:** bounce = recuperação ≥1,5·ATR desde o low corrente seguida de NOVO low,
  contado desde o high das 384 barras anteriores. **1,5 = constante NOVA congelada aqui, antes do
  run; sensibilidade ±0,5 ATR reportada junto** (não escolhida a ver dados do run).

## Resultado esperado declarado ANTES do run (DA A2 — incluindo falhas esperadas)
- Negativos: B1-B3 e C1-C6 esperados com perna VIVA e/ou dip raso (ratio baixo, pos384 >0,7) e/ou
  D3≥1; B4 esperado ambíguo (ruído de acumulação, não perna bear).
- Winners: A1-A3, A5, A6, A8-A10 esperados limpos; **A4 e A7 esperados AMBÍGUOS (REVIEW)**;
  **C3 esperado FALHAR a separação** (loser de GESTÃO em fim-de-perna-madura, não de entrada —
  padrão nº 9; se D1-D3 o "cortarem", é acerto pelo motivo errado e será dito).

## Procedimento (quando autorizado)
1. Script único determinístico: lê o RAW via loader F0 (que **re-verifica o sha256 do cache contra o
   manifest no arranque** — DA A7); mede D1-D3 nos 20 episódios nos instantes das marcas (dados
   só-passado; marcas retrospetivas = reconstrução causal-no-instante, declarado); **reproduz também
   os números citados nos dossiês** (profundidades, pos96/384, reclaim-barras) para reprodutibilidade
   (DA A6 — as sondas do scratchpad morrem).
2. Tabela 20×(D1,D2,D3) contínua publicada, SEM disjunção booleana e SEM verdicto do script.
3. **READER** (leitura minha, apresentada ao Cris) atribui os registos narrativos por episódio.
4. **Quem decide o caminho: o CRIS** (com DA sobre a leitura) — o medidor NÃO arbitra (DA A3).
   Referência informativa (não gate): esperava-se que as 3 leituras juntas marcassem ≥7/10 negativos
   e ≤2/10 winners; qualquer desvio é reportado episódio a episódio, sem ajuste pós-hoc (ajuste =
   novo prereg).
5. **Passo VISUAL obrigatório (DA A4):** o Cris valida no chart N≥6 episódios à escolha dele
   (plotagem canónica long_position+label SÓ com ordem dele; screenshot é dele) ANTES de qualquer
   rodada 2. Sem visual PASS do Cris, nada avança — é a lição A-BULL.
6. Nulls episódicos + DA sobre o resultado.

## Cache 1:1 (DA A7 — ratificação pendente)
`f0_bars_cache.jsonl` = derivação 1:1 do RAW HD com sha no manifest e verificação ao ler.
`DECISION_REQUIRED (Cris)`: ratificar que cache-1:1-com-linhagem-e-sha ≠ primitive (hoje assumido).

## Ligação à fasquia do Cris (sem inflacionar — DA R5)
Um PASS aqui NÃO é evidência de losers ≤10 — é plausibilidade: os negativos desta amostra são
hand-picked e da mesma espécie dos losers reais; a fasquia decide-se nos AMBÍGUOS (A4/A7/C3/F4) e em
episódios virgens. O caminho continua: mais dossiês → leitura blind em virgens → só então automação.

## O que este teste NÃO é
Não é backtest · não produz R/WR · não seleciona estratégia · não valida nada fora da calibração ·
não autoriza F2 · não transforma leituras em thresholds de treino.
