# XAU 15M — MARKUP-DEMAND + FILTER N83 · RECOVERY Devil's Advocate

**2026-07-09.** DA real (Agent tool, general-purpose) sobre o recovery da fonte N96→N83. Verdict: **PASS_READY_FOR_TEST_AUTHORIZATION.**

## Erro anterior (reconhecido)
O bloco anterior concluiu `BLOCKED_MISSING_N83` porque o grep literal por `N83`/`filter_n83` no repo deu 0 matches. **Erro de método: grep-por-nome não bastava** — o nome "N83" era do PDF externo, não do repo. O Cris corrigiu apontando o PDF como prova de que a fonte existia.

## PDF como ponte de proveniência (não validação)
`~/Desktop/Sistema_Agentico_Trading_XAU_LONG_PT.pdf` (2026-07-08 11:36). Tabela "A SUITE APROVADA": **"Markup-Demanda + Filtro Capitulação · 15M · 96 → 83 · 62,7% · +125"**. O DA confirmou ~7 bindings textuais independentes no PDF (não só 3 métricas): nome literal "Filtro Capitulação"; página própria "Motor Markup-Demanda + filtro de capitulação"; "13→0 · 13 perdas cortadas, 0 ganhos"; "em regime de baixa, saltar longs rasos (não-capitulação)"; "null de permutação com busca de features (p≈0,005)"; "+valor fora da baixa e −valor dentro"; rejeição do sinal "topo de range" — tudo verbatim do doc do filtro.

## Identificação (única)
**"Filter N83" = INTRA-BEAR CAPITULATION FILTER sobre o N96.** Caveat adversarial declarado: as 3 métricas sozinhas são degeneradas (qualquer corte 13L/0W daria 83/62,7/+125) — mas nenhum outro filtro do repo corta 13 (range_distribution alveja 26 ids "SEM veredito"; d_bear_active "SEM veredito"). Binding = nome + predicado + 13→0 + p≈0,005 + métricas.

## Aritmética (re-derivada independentemente)
Base: 164 rows, MARKUP=96, 52W/44L. Os 13 ids cortados (1-based na ordem markup) têm **out==0 na base** (timestamps batem com o CSV). 52/(96−13)=62,65%→62,7 · 52·3−31·1=+125. Exato.
**CONCERN corrigido:** o verify v1 confiava no CSV ("LOSER" substring) e assumia W83=52 por doc. **Endurecido:** agora checa `out` na base + aplica o predicado cego (abaixo). Resultado: `SOURCE_RECOVERED` com todos os checks.

## Causalidade (teste decisivo do DA)
Predicado aplicado **cego aos 96** (winners incluídos; `n96_causal_regime.json` + `n96_exhaustive_mtf_features.csv`, cobertura 96/96): seleciona **exatamente** [24,25,55-59,66,67,79,83-85], **zero winners** — todos os 16 BEAR-winners têm `1D_px_vs_ema` < 0 (−0,557…−80,078). A lista é genuinamente gerada-pelo-predicado, **não** "losers que calham de casar" (isso seria contaminação na construção). Gerador `n96_fase1_fase2_maps.py` linha 22 confirma o predicado + assert fail-loud anti-winner. Regime = v5 hour-causal; 1D = último bar FECHADO. Descoberta in-sample = caveat separado e declarado (feature-search null P=0,005).
**Minor:** idiom `or -99` no gerador → `1D_px_vs_ema==0.0` seria KEEP (falsy); 0 ocorrências no dataset; documentado como edge-case latente.

## Status honesto
Prereg/manifest mantêm: `PREREG_ONLY_NOT_TESTED` · `USER_APPROVED_NOT_PRODUCTION` · `PROFITABLE_BUT_FRAGILE` (+4…+13R conforme detector, **nunca +13 solto**) · N pequeno · 11/13 num único bear 2026 · HTF congela 2026-05-24 · "não rodar teste sem autorização explícita". PDF usado só para matching, nenhum número do PDF como evidência. Nota: o PDF (comercial) mostra só a variante +13R sem a faixa — caveat do PDF, não herdado pelos artifacts.

## RAW mapping
`macro_regime` 96/96 ✅ · `1D_px_vs_ema` 96/96 (`n96_exhaustive_mtf_features.csv`, recomputável do RAW 1D) ✅ · o filtro **não depende de family_label** (colunas `familia`/`CDR_gestao` do CSV = anotação pós-seleção). family_label loser-only = pendência só se estudo futuro a usar como gate.

## Cadeia de proveniência
`n96_fase1_fase2_maps.py` (predicado+assert) → `cut_trades.csv` (+`cut_list.json` commitado em a32b25a, gerador não-nomeado — atribuição imprecisa, conteúdo reproduz cego) → doc `XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md` → commit `a32b25a` (2026-07-08 **01:08**) → PDF (**11:36**) — **commit precede PDF, direção correta.**

## Hardenings aplicados em resposta ao DA
1. `n83_source_recovery_verify.py` endurecido (check base-`out` + predicado cego aos 96) → re-run `SOURCE_RECOVERED`.
2. Atribuição do cut_list.json corrigida no prereg §5.
3. Edge-case `or -99` documentado (não alterado o gerador — artifact aprovado congelado).

## Veredito final
**PASS_READY_FOR_TEST_AUTHORIZATION.** Binding correto (único, multi-ponto) · aritmética exata · predicado outcome-clean quando aplicado cego · mapping completo · status honesto. **Nenhum teste corre sem autorização explícita do Cris.**
