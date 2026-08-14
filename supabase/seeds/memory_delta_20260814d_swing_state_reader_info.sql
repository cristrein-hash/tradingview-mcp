-- memory_delta 20260814d — swing-state LH/LL por TF como INFORMACAO pura no reader (consome market_context.json) + conclusoes faca/dip
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('swing_state_reader_info_20260814')::uuid, 'private', 'internal', 'project',
  'ESTADO DA PERNA (swings LH/LL 1H-4H-15M) como INFORMACAO pura no reader (nao gate)',
  'Cris 14/08: adicionada seccao "# ESTADO DA PERNA (swings LH/LL, prioridade 1H->4H->15M)" ao briefing do '
  'reader (e2_quality.render_composite, funcao _swing_state). Por TF: estado DOWN(LH+LL)/UP(HH+HL)/RANGE + '
  'sequencia explicita (LOWER-HIGH/LOWER-LOW vs anterior) + niveis de quebra (fechar>last_high=quebra; perder '
  'last_low=continua). CONSOME o dossie E0 market_context.json axes.mtf.swings (do context_structure) — zero '
  'medicao inventada, nao reconstroi reader. INFORMACAO PURA: nao bloqueia, nao muda emissao, fail-safe. '
  'candle-reader+e2-quality recarregados, LIVE. Motivo: o reader ancorava no rotulo de perna 1H (que ATRASA) e '
  'recebia os swings como valores soltos, sem a sequencia LH/LL explicita nem prioridade 1H->4H->15M.',
  array['seed:memory_delta_20260814d_swing_state_reader_info','reader','swing-state','mtf','structure','e2_quality'],
  'alert-bridge/e2_quality.py::_swing_state', 'active'),
 (md5('faca_dip_investigation_conclusions_20260814')::uuid, 'private', 'internal', 'feedback',
  'Investigacao faca-vs-dip 14/08: nenhum GATE mecanico separa na barra de entrada; so o EVENTO sweep-reject 4H',
  'Investigacao longa (dados replay reais 15M/1H/4H toda a semana; indicadores REAIS OB/SMC/NAS/Bubbles as-of-bar; '
  'consome market_context.json). CONCLUSOES: (1) Na barra de entrada do long, faca e dip PARECEM-SE em tudo o que '
  'foi medido — estrutura, convergencia multifatorial (14 votos MTF), velocidade, localizacao vs OB, swing-state '
  '(fractal m=2 E ZigZag-ATR). AUC ~0.34-0.5 em tudo. (2) Swing-state causal ATRASA o crash: durante o crash de '
  '13/08 TODOS os TFs liam UP (a estrutura confirmada reflete o uptrend anterior ate varios swings confirmarem). '
  '(3) O UNICO sinal que apanhou as facas a tempo foi o EVENTO sweep-reject 4H (vela fechada: sweep de high + '
  'upper-wick grande + rejeicao) — bloqueou 8/10 facas de 13/08 a partir do fecho 02:00; invalidacao "reclaim do '
  'high" e TOSCA (bloquearia longs ate 4450); invalidacao melhor = quebra do ultimo lower-high, mas tambem atrasa. '
  '(4) DECISAO: nao construir gate deterministico (nao existe separador fiavel na entrada); dar a estrutura ao '
  'reader como INFORMACAO. ERROS MEUS recorrentes na sessao: leitura SNAPSHOT em vez de CONTEXTUAL/trajetoria; '
  'hand-roll da polaridade de bubbles (invertida) em vez de consumir bubble_polarity.BUBBLE_POLARITY_RULE; ler a '
  'vela 4H em formacao (degenerada h=l) em vez da fechada; sobre-complicar num soup de 14 votos que diluiu o sinal.',
  array['seed:memory_delta_20260814d_swing_state_reader_info','faca-dip','sweep-reject','swing-state','snapshot-vs-contextual','xau'],
  'research/xau_15m_short/engine_mtf_convergence_20260814.py', 'active')
on conflict (id) do nothing;
