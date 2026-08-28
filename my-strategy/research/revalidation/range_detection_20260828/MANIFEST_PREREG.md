# RANGE DETECTION FIX — PREREG (selado 2026-08-28, aprovado Cris "APLICA OS DOIS")
Problema: v5-4H e Layer1 falharam 2 ranges comprovados (constatação Cris, tarefa em memória). No censo
A1/A2, RANGE v5 = positivo-fraco (+0.08 raw) — rotulagem tardia/ausente dilui qualquer uso do rótulo.
ARMADILHA DECLARADA: calibrar nos 2 ranges conhecidos = fit n=2 (proibido, feedback_principio_vs_fit).

## Desenho selado
1. GT INDEPENDENTE mecânico sobre TODO o 4H 2024-26 (não só os 2 casos): segmentação por critério único
   selado — janela K=30 barras 4H; RANGE se (max(H)-min(L))/ATR14 <= 4.0 E |fecho_fim - fecho_início| <=
   40% da largura. Gera dezenas de segmentos sem olhar para os 2 casos. Params fixados AGORA, zero sweep.
2. Matriz de confusão v5 e Layer1 vs GT (onde erram, com que atraso, que fase do range).
3. Ajuste PRINCIPIADO único por detetor (sem varrer thresholds): candidata única declarada = condição
   explícita de "sem progresso líquido" (fecho da janela dentro de X do início) que o v5 hoje não tem.
4. Validação: jackknife por semestre; null (rotulador aleatório com mesma fração RANGE); os 2 ranges do
   Cris = DESCRITIVOS (relatados, nunca alvo de calibração).
5. Saída: versão candidata roda SHADOW lado-a-lado no forward_labeler (campo v5_new) — decisão de troca
   só por comparação em mercado real + ordem Cris. Nada muda nos detetores LIVE neste estudo.
DA obrigatório pós-execução. Gates = referência; veredito = Cris (adenda 28/08 em vigor).
