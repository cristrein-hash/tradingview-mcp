-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260731_bubble_polarity_context_fix
-- ============================================================================
-- Correcao polaridade context-dependente de bubbles nos 2 caminhos vivos + prova viva PASS. 1 row.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260731_bubble_polarity_context_fix:memory_items:fix')::uuid,
  'product', 'internal', 'decision',
  'Polaridade de bubbles CONTEXTO-DEPENDENTE ligada ao live nos 2 caminhos (claude_recheck + e2) — prova viva PASS (Cris 2026-07-31)',
  'BUG re-encontrado 2026-07-31: claude_recheck.py bloqueou um LONG de reversao-em-demanda (4053-4058) por "sem buy-cluster" (BUBBLE_CLUSTER_GATE_LTF), tratando sell-bubbles como bearish. A regra context-dependente EXISTIA (feedback_bubbles_polarity_rule, validada 2026-06-03 n=1163 XAU 4H) mas NUNCA fora ligada aos prompts vivos. Cris: "resgate logica auction de bubbles urgente ... elimina qualquer conteudo desalinhado em qualquer documento". REGRA CANONICA: bubbles=ordens MARKET agressivas; o sinal e se a agressao e ABSORVIDA num nivel (reversao) ou CONTINUA com a perna (pullback); polaridade FLIP pelo contexto — classificar contexto PRIMEIRO. reversal-em-fundo/demanda->SELL-absorvido=BULLISH (BUY=anti-padrao); pullback-uptrend->BUY=bullish; reversal-em-topo->BUY-absorvido=BEARISH. GUARDA absorcao!=faca: exige reclaim/hold>=2 barras fechadas; vertical news-driven (FOMC-spike/high_impact/1o-toque-sem-reclaim) = FACA nao absorcao. Mapeamento cru: BUY=plot_0/2/4, SELL=plot_6/8/10. CORRECAO (desenho + implementacao direta): (1) NOVO alert-bridge/bubble_polarity.py = FONTE UNICA BUBBLE_POLARITY_RULE importada pelos DOIS caminhos vivos (nao podem divergir) + helper classify_bubble_context (--selftest PASS). (2) claude_recheck.py: gate re-escopado ao LADO CORRETO do contexto (nao buy-cluster por defeito), regra injetada no prompt f-string; spawn-por-alerta (sem restart). (3) e2_quality.py: regra anexada ao READ_SYS + linha guia na render AUCTION; selftest+anchors PASS byte-behavior intacto; daemon kickstarted. (4) docs alinhados: SKILL_03_VISUAL_REVIEW_AUCTION_THEORY.md (regra canonica) + E2_READ_CALIBRATION_DESIGN_20260718.md (frase antiga incompleta anotada). PROVA VIVA (claude_recheck no caso real LONG demanda 15M): ANTES bloqueava por BUBBLE_CLUSTER_GATE_LTF; DEPOIS "bubbles SELL absorvidos" reconhecido, "Hard block triggered: NONE", segurado em observacao por motivo legitimo (sem reclaim/CHoCH confirmado + zona 4053-4058 nao e OB real, demanda real=4028-4036). Erro de polaridade eliminado. Commit 62e1260 (fix) + este seed. Alert-only, sem auto-trade.',
  array['seed:memory_delta_20260731_bubble_polarity_context_fix','bubbles-polaridade-context-dependente','claude_recheck+e2-unificados','fonte-unica-bubble_polarity','sell-absorvido-em-demanda-bullish','guarda-absorcao-nao-faca','prova-viva-PASS','bug-recorrente-2026-06-03'],
  'alert-bridge/bubble_polarity.py · claude_recheck.py · e2_quality.py · docs/project_authority/SKILL_03_VISUAL_REVIEW_AUCTION_THEORY.md · docs/architecture/E2_READ_CALIBRATION_DESIGN_20260718.md · feedback_bubbles_polarity_rule · commit 62e1260',
  'active'
)
on conflict (id) do nothing;
commit;
