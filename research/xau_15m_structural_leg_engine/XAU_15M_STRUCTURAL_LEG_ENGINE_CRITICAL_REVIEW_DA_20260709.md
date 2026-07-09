# DA DA AUDITORIA — XAU 15M STRUCTURAL LEG ENGINE CRITICAL REVIEW (2026-07-09)

> Devil's Advocate real (Agent tool, general-purpose, read-only) atacando a auditoria
> `XAU_15M_STRUCTURAL_LEG_ENGINE_CRITICAL_REVIEW_20260709.md`. Conflito de interesse declarado:
> o auditor auditou a própria spec — este DA é o contrapeso.

## VERDICT: `PARTIAL_REVIEW_INCOMPLETE`
A auditoria foi trabalho real (R1-R10 reais; E5/E7/E3 genuínos), MAS certificou como verdadeiras
afirmações falsas e deixou graus de liberdade abertos. 9 ataques CONFIRMADOS, 7 refutados.

## Ataques CONFIRMADOS (resumo; detalhe no output do agente)
1. **Paridade macro inexequível dentro das regras** — o engine canónico `engine_substrate4_v5_hourcausal.py`
   lê `*.primitives.json` (linha 7); o manifest bane primitives; o "assert de paridade" não tinha
   input legítimo, e o stop_condition atribuía falha a "port defeituoso" quando podia ser diferença
   de FONTE. → correção C1.
2. **"6 constantes novas ✅" era FALSO** — o classificador raw de leg_dir tinha ~6-10 constantes
   ocultas não especificadas (períodos EMA/ATR 1H, janela de range, cutoffs de decisão, W de warmup,
   quiet-count do flush) que seriam decididas em tempo de código, fora do grid/ledger. → C2.
3. **Estágio-1 de triagem sem bounds pré-registados** — "plausibilidade" escolhida por quem já viu a
   densidade do GT = look disfarçado. → C3.
4. **Check de construção (medianas ±30%) usava estatísticas do catálogo COMPLETO incluindo o holdout
   BULL-2026** = seleção informada pelo holdout. → C4.
5. **Mining-null F1.5 era "P reportado" sem fasquia** + matcher F1.5 largo (±2d). → C5.
6. **Porte preguiçoso parcial**: eff_thr/slope_thr congelados da escala DIÁRIA para buckets 1H sem
   sanity-check de transferibilidade; contingência só p/ eff_thr e estreita; slope_thr sem
   contingência. → C2/C8.
7. **Ponte losers ≤10 desconectada**: teto sósia 28-108:1 ⇒ precisão evento ~1-3%; a fasquia exige
   que Fase 2/3 fechem gap ~30-70× — a auditoria nunca fez a aritmética. → C6.
8. **Firewall temporal ausente**: calibração BEAR (mar-jun/2026) vive DENTRO da janela do holdout
   BULL-2026 e partilha constantes → contaminação indireta possível. → C7.
9. **Incoerências menores**: K_up seed∉grid; latência 1,5h vs 2h em docs distintos; bootstrap do
   retr_fam indefinido na 1ª perna; tol_anchor reciclada contada como "sem parâmetro novo"; cutoffs
   retr_fam {0,5;1,3} herdam calibração feita nos 50 círculos (recall_50 parcialmente
   auto-realizável — declarar). → C8.

## Ataques REFUTADOS (cobertos de origem)
Flush override não é retroativo (running_peak causal; truncation test cobre) · primitives limpos
como fonte de DADOS (exceto canal de paridade, corrigido) · E5 BEAR=calibração aplicado a sério ·
E3 anti-A-BULL propagado até stop_condition executável · E7 price-only coerente nos 3 docs ·
blockers executáveis existem · manifest no dir do protocolo.

## CORREÇÕES APLICADAS (v1.2 dos docs, mesmo dia)
- **C1** Paridade redefinida como paridade de LÓGICA: funções v5 portadas verbatim + fixtures
  sintéticas determinísticas; PROIBIDO correr/comparar contra série primitives-derived; stop_condition
  distingue defeito de porte vs divergência de fonte.
- **C2** Classificador raw ESPECIFICADO por completo como transposição verbatim congelada do
  `raw_stable()` v5 (E50/E100 em buckets 1H, slope lb5, s100 lb10, pos N=30, R_thr 2,0, banda
  0,15-0,85, cutoffs 0,55/0,6); W warmup = 400 barras 15M (cobre E100 1H); rec_flush = 5×mom (rácio
  herdado do override 1H do v5); contagem honesta: ~10 herdadas congeladas + 6 novas em grid.
- **C3** Estágio-1 pré-registado: janela SÓ pré-holdout (2024-05-25→2025-12-31); bounds: pernas/mês
  ∈[2,20], duração mediana ∈[8h,120h], % tempo por leg_dir ∈[5%,85%], LEG_FLAT ≤70%; top-20 =
  menor nº de desvios do seed v5, desempate lexicográfico determinístico (GT-free).
- **C4** Check de construção: medianas recomputadas SÓ nas marcas de calibração (holdout excluído)
  E rebaixado a REPORT-ONLY (sem poder de rejeição) até F3.
- **C5** Mining-null F1.5 com gate P≤0,05 + linha de sensibilidade com matcher apertado (±0,5d).
- **C6** Aritmética da ponte escrita no manifest: o engine SOZINHO NÃO atinge losers ≤10; gap
  declarado ~30-70× a fechar nas Fases 2/3 — qualquer relatório que omita isto = violação.
- **C7** Firewall temporal: constantes partilhadas da camada de pernas CONGELAM no fim do F1.5,
  ANTES de qualquer leitura de marcas BEAR-2026; sequência no manifest.
- **C8** K_up grid {4,5,6} (seed∈grid); latência unificada (stop = mediana >2h; % <1,5h informativo);
  retr_fam UNDEFINED na 1ª perna pós-warmup (eventos suprimidos até 1ª perna fechada); tol_anchor na
  banda BASE_BOTTOM = parâmetro novo com valor reciclado congelado (declarado); contingência
  slope_thr {0,15,0,20,0,25} pré-registada (só após falha F1.5, looks no ledger); herança dos cutoffs
  retr_fam declarada como caveat do recall_50.

## GO/NO-GO FINAL
GO para codar F0→F1.5 **após estas correções** (aplicadas em
`docs/architecture/XAU_15M_STRUCTURAL_LEG_ENGINE_GATE_MANIFEST.md` e
`XAU_15M_STRUCTURAL_LEG_ENGINE_SPEC_20260709.md` v1.2) — condicionado à ordem explícita do Cris.
Paragem obrigatória no gate F1.5.
