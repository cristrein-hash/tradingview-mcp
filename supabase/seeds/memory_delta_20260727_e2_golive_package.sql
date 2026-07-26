-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260727_e2_golive_package
-- ============================================================================
-- Sessao 2026-07-26/27 (pre-abertura -> abertura): pacote completo E1/E2 aprovado pelo Cris e posto em
-- PRODUCAO DIRETA ("APROVO, SEM SMOKE, VAI A PRODUCAO DIRETO EM LIVE AGORA"). Inclui a remocao total de
-- session_vacuum+chase, a auditoria profunda do funil (3 passes) e o ground-truth dos SLs do Cris.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260727_e2_golive_package:memory_items:funnel-audit-hidden-factors')::uuid,
  'product', 'internal', 'project',
  'Auditoria profunda do funil E1->E2 (2026-07-26, 3 passes): 5 fatores ocultos — SL-de-brinquedo fabricava losers falsos; sistema calibrado ao contrario',
  'Auditoria pre-implementacao exigida pelo Cris ("tem muitos fatores ocultos") sobre TODOS os 210 candidatos unicos E1 da semana 16-24/07, outcome contrafactual vs bars_15m (SL-first, horizonte 96 barras), 3 passes de refinamento (bruto -> geometria valida -> risco executavel sl_atr>=0.3). FATORES OCULTOS: (1) BUG: 31 candidatos com SL do LADO ERRADO da entry + 15 risk<1pt = 46/210 geometria invalida. (2) SL SISTEMATICAMENTE CURTO: swing 15M local como stop em gatilhos 1H/4H -> 99/164 validos marcados SL tinham MFE>=2R (losers FALSOS; ex 20/07 15:30 LONG 4007.56 stop 1.8pts, subiu 43R). (3) Regua confluencia penaliza reversoes de extremo POR CONSTRUCAO (eixos MTF/momentum estao contra no fundo); act_dens zero separacao (TP 19% com vs 16% sem). (4) TOPO 100% INVISIVEL: zero candidatos SHORT >=4090 na semana (dia do topo 23/07: 20 LONG, 0 SHORT; E1 gerava LONGs a comprar 4120-4142 na descida) — nao havia gatilho de teste-e-rejeicao no iman. (5) Alvo cap 5R com SL curto = TP-rate 12% (33% em RR baixo). FUNIL DOS 29 WINNERS EXECUTAVEIS: materialidade 15 · gate 5 (vacuum 4+chase 1) · antispam 6 · read 3 · SURFACED 0; e os 3 unicos surfaced da semana foram SL — o sistema estava calibrado AO CONTRARIO. Anti-spam por zona simulado: +2TP/+2SL. Perna-proxy: com-perna 47% TP vs contra 22%. Scripts research/deep_funnel_audit{,2,3}_20260726.py + funnel_audit{,2}_20260726.py. Diagnostico in-sample 1 semana; arbitro = forward.',
  array['seed:memory_delta_20260727_e2_golive_package','auditoria-funil','fatores-ocultos','sl-de-brinquedo','losers-falsos','topo-invisivel','geometria-invalida','calibrado-ao-contrario','mfe-mae'],
  'research/deep_funnel_audit_20260726.py · research/deep_funnel_audit2_20260726.py · research/deep_funnel_audit3_20260726.py · memoria project_camada2_e2_convergence_read',
  'active'
),
(
  md5('seed:memory_delta_20260727_e2_golive_package:memory_items:e2-golive-package')::uuid,
  'product', 'internal', 'decision',
  'PACOTE E1/E2 GO-LIVE (Cris 2026-07-26 "APROVO, SEM SMOKE, PRODUCAO DIRETO"): R7 magnet_reject + SL estrutural + frame perna-1H + E2 LIVE Telegram; session_vacuum e chase REMOVIDOS do sistema',
  'ORDENS Cris executadas em producao antes/na abertura 2026-07-27: (0) session_vacuum e chase RETIRADOS POR COMPLETO do sistema (nao observacional, nao rebaixado — "blocks primitivos que ja foram descartados"): gate E2 = SO higiene bad_rr+stale; sessao/frescura/catalisador/contra-regime = contexto do READ. Removidos tambem do e1 (dedup destino-consciente), backfill (mapa por sessao -> por hora, observacional nunca-veto) e config (DEAD_SESSIONS). (1) E1 R7 magnet_reject: teste-e-rejeicao no iman supply/demand 4H/1D, toque INTRABAR (wick, high/low da barra 15M do bar-store) + fecho de volta fora da zona; fecha o gap do topo invisivel; zonas do dossie E0 (nunca inventadas). (2) SL ESTRUTURAL: extremo da zona protetora -+0.1ATR — VALIDADO pelo ground-truth do Cris no chart: ele estendeu S2/S4/S5 e os 3 SLs cairam NO MESMO preco 3997.55 = borda inferior da demanda (entradas 4007.56/4005.89/4006.81 diferentes, stop igual -> stop e funcao da ESTRUTURA); S3 confirmou. (3) ENTRADA ANCORADA (licao S1 do Cris): candidato so nasce com entry a <=0.5ATR da borda da zona; longe = espera retest, NUNCA esticar stop (S1 4061 com estrutura a 4053 = RxR podre = pullback apanhado a pressa). (4) fix A: SL do lado errado descarta (bug dos 31). (5) anti-spam POR ZONA (dir+zona 5pts): admite 1o toque OU conf>max-anterior OU 4h — re-teste que aguenta FORTALECE. (6) act_dens descritivo (nao mata). (7) E2 FRAME-EXPLICITO: render_composite abre com "# FRAME: PERNA 1H=BULL/BEAR" (consome _leg_1h do price-shock, fallback fiel) + regra de zonas do Cris; READ_SYS le as vozes CONTRA o frame, gradua por CONVERGENCIA nunca contagem. (8) E2 LIVE: surfaced -> Telegram advisory (nunca ordem), hard-lock E2_PRODUCTION_AUTHORIZED=1 exportado no wrapper start_e2_quality.sh (auditavel/reversivel). Selftests PASS, daemons reiniciados, mercado aberto com stack novo (price 4089). ARBITRO = semana forward 27-31/07. Vigiar: flood pos-abertura, custo Opus/read, volume R7.',
  array['seed:memory_delta_20260727_e2_golive_package','e2-live','frame-perna-1h','r7-magnet-reject','sl-estrutural','entrada-ancorada','anti-spam-por-zona','gate-so-higiene','vacuum-chase-removidos','ground-truth-sl-cris','user-approved','producao'],
  'alert-bridge/e1_detector.py::levels/detect/anti_spam · alert-bridge/e2_quality.py::render_composite/notify_surfaced · alert-bridge/start_e2_quality.sh · commits fd84b67 + go-live 2026-07-27 · memoria project_camada2_e2_convergence_read',
  'active'
)
on conflict (id) do nothing;
commit;
