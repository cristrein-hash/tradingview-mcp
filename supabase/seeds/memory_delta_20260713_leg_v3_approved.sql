-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260713_leg_v3_approved
-- ============================================================================
-- Sessao 2026-07-13 (4o bloco): Layer2 LEG v3 (refino AC via engine) = USER_APPROVED.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260713_leg_v3_approved:memory_items:leg-v3')::uuid,
  'product', 'internal', 'project',
  'Layer2 LEG v3 (refino do balde ACUMULACAO via engine multi-agente) = USER_APPROVED (nao producao)',
  'Cris aprovou "SYNTH conservadora como leg v3" — engine multi-agente completo aprovado. Opcao A (reduzir o balde ACUMULACAO do leg 4H) com arbitro B (escala fina + known_at). leg_v3.build_leg_v3() = leg base (macro-independente, zigzag R=6) + RESOLUCAO dos bares AC em direcao SO com alta confianca. Harness determinista leg_refine_harness.py fixa o esqueleto R=6 selado, torna plugavel so os bares AC, e mede contra (i) VERDADE CONVERGENTE RETROSPECTIVA (segmento fino R=3 amplitude>=1 ATR = o GT auto-gerado) e (ii) trava de coerencia (anti-impulso preservado por construcao: baixa-em-bull => PULLBACK). Engine (Workflow, 17 agentes, 0 erros): 8 lentes -> DA causal lookahead-only -> sintese. Descoberta ESTRUTURAL durável (L8): um bar AC e a CONTINUACAO da perna-em-curso (base_dir), NAO uma direcao inventada por escalas finas (fs2/fs3/fs4 isoladas ~51% = moeda-ao-ar; base_dir sozinho 57%). SYNTH = base_dir + momentum confirma(ret10)/persiste(ret5) + aceleracao longa (ret20 mesmo sinal, |ret20|>=2.5) + piso |ret10|>=1.5 (1.3x pernas jovens<24b) + dupla-fina fd3/fd4 nao-contradiz. AUDITADO: precisao 87% / especificidade 93% / recall 6% / AC 42%->39% / frag 260. leg_v3 reproduz o harness+SYNTH byte-a-byte (0 diffs/9797). CAVEAT METODOLOGICO REGISTADO (auditei): o arbitro fino R=3 e MOMENTUM-CORRELACIONADO ("preco andou >=1 ATR" ~ retorno grande), logo a precisao 87 esta PARCIALMENTE EMBUTIDA (base_dir sozinho 57 -> +30pp do momentum e inflado pela tautologia); o ganho ROBUSTO/nao-circular = especificidade (57->93, separar plano de direcional) + a licao estrutural. Ganho pratico MODESTO (recall 6%, AC so 42->39; ponto de mais cobertura L3 daria AC->28 mas precisao 83/espec 65). STATUS research/USER_APPROVED, nao producao. Alternativa futura p/ mais confianca: validar bares resolvidos contra olho visual do Cris (arbitro (a) adiado). Commit 3b2588e.',
  array['seed:memory_delta_20260713_leg_v3_approved','layer2','leg-v3','refino-acumulacao','engine-multiagente','base_dir-continuacao','user-approved','caveat-arbitro-momentum','nao-producao'],
  'my-strategy/research/revalidation/{leg_v3.py,leg_refine_harness.py,legcand_SYNTH.py,legcand_L1..L8.py,leg_macro_coherence_audit.py} · workflow wf_2b0b4b2f-b2a · commit 3b2588e',
  'active'
),
(
  md5('seed:memory_delta_20260713_leg_v3_approved:memory_items:leg-macro-coherence')::uuid,
  'product', 'internal', 'project',
  'Auditoria LEG x MACRO = perna vive COERENTE dentro do macro 1D (0% anti-impulso BULL, 1% BEAR)',
  'Auditoria de compreensao (leg_macro_coherence_audit.py) antes do refino: como a perna 4H (macro-INDEPENDENTE, para nao ser circular) vive nos ciclos do macro 1D (Layer1 aprovado), alinhamento CAUSAL (rotulo 1D conhecido ao fecho <= t). Resultado: HIERARQUIA ALTAMENTE COERENTE — em macro BULL 0% de impulsos-de-baixa; em macro BEAR 1% de impulsos-de-alta; RANGE = ~metade acumulacao + impulsos dos 2 lados (definicional). Ciclos canonicos legiveis: BULL = pb-baixo->impulso-alta; BEAR = pb-alto->impulso-baixo. Unica friccao dentro de macro direcional = o bear-flag de 2026 (1 episodio I-alta dentro de BEAR = a tensao hierarquica desejada pullback-bull-in-bear); zero friccao em BULL. Ponto aberto que motivou o refino = ACUMULACAO alta (37% BULL/32% BEAR/49% RANGE) = granularidade grosseira, NAO incoerencia. Validou as 2 leituras (macro e leg) como convergentes. Commit 3b2588e.',
  array['seed:memory_delta_20260713_leg_v3_approved','auditoria-leg-macro','coerencia','hierarquia','bear-flag-friccao','causal'],
  'my-strategy/research/revalidation/leg_macro_coherence_audit.py · commit 3b2588e',
  'active'
)
on conflict (id) do nothing;
commit;
