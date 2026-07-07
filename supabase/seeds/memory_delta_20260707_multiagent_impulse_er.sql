-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_multiagent_impulse_er
-- ============================================================================
-- Bloco: motor multi-agente exaustivo -> router (a)(b)(c) = muro; 1 sobrevivente causal (Kaufman ER perna anterior) (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_multiagent_impulse_er'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_multiagent_impulse_er:memory_items:impulse-er-perna-anterior')::uuid,
  'product', 'internal', 'project',
  'Motor multi-agente exaustivo: router macro-contextual (a)(b)(c) = MURO causal-clean; 1 sobrevivente = Kaufman ER da perna anterior (momentum-de-rutura causal) PROMISSOR-NAO-VALIDADO',
  'Cris pediu explicitamente engine multi-agente exaustivo apos desgaste com lookahead. Workflow wf_2cbffa42 (kit agent_ctx_kit.py com scoring anti-poison; 96 entries = trades #1-#96 causais): 8 hipoteses causais estruturais, cada uma AUDITADA ADVERSARIALMENTE p/ lookahead (default=tem-lookahead) + null (permutacao+rotacao) + poison-ratio + estabilidade por-ano. ROUTER MACRO-CONTEXTUAL (a) maturidade-perna + (b) direcao-HTF + (c) range-demanda, desenhado pelo Cris = MURO causal-clean: 7/8 features falham. HTF-structure BOS/CHoCH (causal, null 0.041, poison ok, MAS 2026=47%<base = instavel entre anos, killed); RANGE-demanda causal (causal MAS null_p=0.128 winner-curse + 2026=50%<base); room-to-prior-high (substituto CAUSAL do supply_above que era lookahead via last_t) = REFUTADO sem separacao; higher-high-seq poison>=1; leg-maturity 57% fraco; bull-in-bear-CHoCH-up poison 0.89 +1.5pp negligivel; RSI/EMA-regime poison 0.97. 1 SOBREVIVENTE (todos 4 gates, confirmado independentemente no kit): impulse_efficiency_prior_leg = Kaufman Efficiency Ratio da PERNA ANTERIOR ao pullback (barras<=j, causal, ER>=0.26) — a perna que precede o pullback foi impulsiva/limpa (eficiencia direcional) vs choppy. E a tese "momentum para romper" do Cris na forma CAUSAL: medida do PASSADO (perna anterior), nao do futuro (por isso nao e lookahead como o r=12 era). Metricas: N52, hit-3R 63.5% (+9.3pp sobre base 54.2%), poison 0.76 (corta 25 losers vs 19 winners = corta MAIS loser que winner), 2025=63.6% e 2026=63.3% (ESTAVEL entre anos, ambos acima da base), null_p 0.038(perm)/0.042(rot) ambos<0.1, lookahead-audit CLEAN (reproduzido byte-a-byte). Corta 9 losers conhecidos do Cris (exaustao-topo #21/23/55/83, perna-bear #89/93/94, falso-fundo #49/50) ao custo de 5 winners (#11/29/44/45/82). Threshold num plateau [0.24-0.26] (nao pico fragil). CAVEATS HONESTOS (auditor+sintese): null_p 0.038 e MARGINAL e NAO-corrigido p/ multiplicidade cross-feature (~7 looks -> sob Bonferroni cruza 0.1); separacao subjacente modesta (ER mediana winners 0.289 vs losers 0.247, delta ~0.04); NAO e o router estrutural desenhado (esse e muro), e um proxy singular de qualidade-de-impulso. VEREDITO = PROMISSOR-NAO-VALIDADO: passa o gate literal mas margem estreita; arbitro limpo = forward/dados virgens; NAO promover como edge isolado. E o PRIMEIRO filtro de toda a saga que e simultaneamente causal-clean (lookahead-auditado), nao-envenenante (poison<1), estavel entre anos e null<0.1 — mais do que tudo antes. Doc XAU15M_ENTRY_CONTEXTUAL_FILTER_STUDY_20260707.md sec 6c. commit dff3805.',
  array['seed:memory_delta_20260707_multiagent_impulse_er','multi-agente-workflow','router-macro-contextual-muro','kaufman-er-perna-anterior','momentum-rutura-causal','promissor-nao-validado','audit-adversarial-lookahead'],
  'docs/architecture/XAU15M_ENTRY_CONTEXTUAL_FILTER_STUDY_20260707.md sec 6c; agent_ctx_kit.py + wf_*.py (workflow wf_2cbffa42, commit dff3805)',
  'active'
)
on conflict (id) do nothing;

commit;
