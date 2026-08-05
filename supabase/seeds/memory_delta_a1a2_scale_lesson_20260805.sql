insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('a1a2_scale_and_entry_lesson_20260805')::uuid, 'private', 'private', 'feedback',
  'Licao A1/A2 live 05/08: guarda de ESCALA (risco<=2.5xATR) + guarda de LOCALIZACAO em todo detetor novo',
  '1o sinal live do A1/A2 (12:16): entry 4170.69 SL 4076.75 alvo 4452.51 R=94pts. Cris apanhou: SL gigantesco = 4H mascarado de 15M; e a compra saiu NO TOPO de onde ia comecar o pullback (bounce 78% corrido; entrada ideal ~4155). Causas: (1) fundo do pullback = min-low 24b cego caia em barra do RALLY vertical; (2) ancora do SL olhava j-16 barras e agarrou o low 4077 do rally das 02:00; (3) MB3 dispara tarde em bounces grandes. Fixes deployados: fundo = min low POS-topo da perna, serie fatiada a j-3 para ancora prender ao fundo real, TRAVA risco<=2.5xATR (cenario real 12:00 agora rejeitado). Cancelamento enviado ao grupo. REGRA GERAL: backtest nao contem todos os regimes - um rally vertical quebrou 2 pressupostos silenciosos; todo detetor novo em live exige guarda de escala (risco coerente com o TF) e guarda de localizacao (nao perseguir gatilho com retrace corrido/colado a resistencia); sinal deve reportar % do bounce corrido + nivel de retest ideal para entrada limite. 1a semana live = caca a pressupostos quebrados; Cris = melhor sensor.',
  array['seed:memory_delta_a1a2_scale_lesson_20260805','a1a2','licao','escala','entrada','guardas'],
  'memory/feedback_a1a2_scale_and_entry_lesson.md · continuation_A1A2/a1a2_runtime.py', 'active')
on conflict (id) do nothing;
