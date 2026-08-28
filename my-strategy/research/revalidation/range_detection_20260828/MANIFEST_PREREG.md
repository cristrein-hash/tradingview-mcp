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

## ADENDA PÓS-EXECUÇÃO (28/08, DA ad22b196)
- Critério de largura do GT esteve MORTO (w/ATRd máx 3.44 em 10.171 barras; nunca binding) e a aproximação
  ATR-d ≈ 6×TR4h sobrestima ~2.6× — GT efetivo = só net-fraction. GT pisca (761 segmentos crus, mediana 12h).
- Candidata cont⇒RANGE: MORRE DOCUMENTADA. bacc 0.52 = dentro do null (p95 0.52); GT suave 0.540 vs null 0.527
  (marginal); jul/2026 = 0 mudanças porque cont era FALSO nos dias BEAR (a feature não vê os ranges do Cris)
  e o stable-BEAR está em latch (sai só por 5 rawS consecutivos não-BEAR). Override dd6% NÃO é o culpado
  (14% das barras, 0 decisivas).
- Migração no censo: 51 episódios BEAR→RANGE (WR 18%, −25.2R) = re-particionamento que PIORARIA o gate !=BEAR.
- BUG corrigido: side-effect do motor (l1_FINAL_regime_gated.json) contaminado pela ordem de load; reparado
  pelo DA (git limpo), ordem invertida no script.
- Candidata V2 PRINCIPIADA (proposta DA, aguarda ordem Cris): condição de SAÍDA de BEAR simétrica com
  predicados existentes (N dias sem novo low E fecho>=E50 destranca o latch) + GT com duração mínima >=2d
  selada antes de olhar 2026. Zero thresholds novos.
