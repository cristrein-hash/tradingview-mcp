-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260714_a1_entry_approved
-- ============================================================================
-- Sessao 2026-07-14: A1 ENTRY (XAU 15M LONG) = USER_APPROVED; gatilho MB3 pinado + prereg forward + coletor.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260714_a1_entry_approved:memory_items:a1-entry')::uuid,
  'product', 'internal', 'project',
  'A1 ENTRY (XAU 15M LONG) = USER_APPROVED — gatilho MB3 (micro-BOS) pinado + prereg forward selado + coletor',
  'Cris "APROVO A1 ENTRY - XAU 15M LONG". Primeira camada de entry do GT de fundos (A1=pullback-reteste-corretivo em macro BULL, 14 fundos in-sample). METODO (leitura contextual ampla, nao mecanizacao a priori): substrato causal RAW 15M direto do HD (a1_context_build.py, 14 dossies, AUDITADO byte-identico a extracao canonica; bubbles conhecidas 1 barra apos fecho=canonico) -> engine multi-agente de LEITURA (5 lentes: estrutura/order-flow/momentum/HTF/holistica) -> as 5 lentes CONVERGEM no mesmo evento (micro-turno +1..3b apos o low, comprado em desconto em demanda HTF apos capitulacao) nomeado 5x. GATILHO PINADO = MB3: fecho da 1a vela 15M apos o low-ancora que fecha VERDE e fecha acima do HIGH da barra IMEDIATAMENTE ANTERIOR (1o micro-higher-high, break ROLANTE = robusto a candle largo; resolve A1_01 e A1_03 que MB1/MB2 falhavam). SL=low-0.1ATR (low REAL do candle, ancora robusta janela[-16,+8]), target=3R. VERIFICADO barra-a-barra SL-first (a1_microbos_verify/pin.py): MB3 14W/0L vs reclaim 12W/1L(A1_10 R60)/1OPEN(A1_11 R41) -> MB3 bate reclaim por CONTROLO-DE-R/convexidade nos fundos ATR-alto. CORRECOES DE METODO desta sessao: (1) o "reclaim 14/14" anterior era ERRADO (bug bar-loader: 1a captura=barra em formacao flat; corrigido para merge max-high/min-low/ultimo-close) + low de fonte ambiguo (gt_price ate 16pt acima do low real) = era load-bearing e inflava o reclaim; (2) o "seletor V-agudo precisa entrar cedo" era artefato do low errado. CAVEATS SELADOS: N14=desenho nao validacao; NULL(entrada aleatoria)=76pct agregado (edge concentrado nos ATR-alto null 10-38pct); 5/14 tight-R(R/ATR<1.65) otimista (15M nao resolve intrabar); supply-overhead imediato NAO testado (vetor de falha forward). PREREG FORWARD congelado (A1_MB3_ENTRY_PREREG_FORWARD_20260714.md): hipotese unica, regras exatas, metricas, null, supply-vector, PASS/FAIL selado (N>=20 RESOLVED, hit-3R>=50, streak<=5, bate null q95, >=reclaim+domina ATR-alto, expectancia liquida>0); SEM OOS historico, forward=ops live/proxy do Cris. COLETOR a1_forward_score.py automatiza (recebe fundo->pontua MB3 vs reclaim->log a1_forward/forward_log.jsonl, estado PENDING; --status progresso N/20; --resolve). Commits 3bb7d27/1109b53. PROXIMO: coletar forward ate N>=20; depois camadas A2/B/Cp/Cg (mesmo metodo).',
  array['seed:memory_delta_20260714_a1_entry_approved','a1-entry','xau-15m-long','mb3-microbos','user-approved','prereg-forward','coletor-forward','n14-desenho','null-76','tight-r-otimista','supply-overhead-vetor'],
  'my-strategy/research/revalidation/{a1_context_build.py,a1_microbos_verify.py,a1_microbos_pin.py,a1_forward_score.py,A1_MB3_ENTRY_PREREG_FORWARD_20260714.md} · commits 3bb7d27/1109b53',
  'active'
)
on conflict (id) do nothing;
commit;
