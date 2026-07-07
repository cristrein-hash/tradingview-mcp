# XAU 15M N96 — RAW MTF Loser Filter · Devil's Advocate

**2026-07-07.** Checagem adversarial do audit RAW-native multi-TF (`XAU_15M_N96_RAW_MTF_LOSER_FILTER_AUDIT_20260704.md`).

## Checks

**1. Source check — PASS (RAW-native).**
- 15M = `primitives/` (RAW-15M lineage, source guard PASS). 30M/1H = `htf_primitives/` extraídos do RAW gz por `build_30m1h_primitives.py` (cópia FIEL da lógica validada de `build_htf_primitives`). 4H/1D = `htf_primitives` nativos. **Zero resample, zero Fractal-MTF, zero SLIM, zero staging.** Cada feature tem TF + campo do RAW/primitives.

**2. Lookahead check — PASS.**
- `CAUSAL_BAD=0/96`: nenhuma barra HTF com t>entry usada (a barra HTF corrente que contém o entry é EXCLUÍDA; usa-se `t+bar_sec<=entry_t`). Zonas DEMAND/SUPPLY filtradas por **born_t<entry**, NUNCA `last_t` (o defeito que contaminou o supply_above resampleado). RSI/ATR/EMA das barras HTF fechadas. e['out'] só no score, nunca na feature.

**3. Resample check — PASS.**
- Nada resampleado. 30M/1H vêm do RAW 30M/1H nativo (extractor validado), não de agregação de 15M. Corrige explicitamente o erro do Fractal-MTF.

**4. Overfit / mining check — o resultado NÃO sobrevive, e é reportado como tal.**
- OOF leave-one-out (não in-sample) + mining-null (200 permutações, re-corre o LOO): **obs 0,525 < base 0,542; null mediana 0,542; P(null≥obs)=0,605.** O classificador HTF multivariado **não bate o acaso** → **sem edge a explorar**. Não há mineração de threshold (usou-se logística LOO multivariada, não best-of-grid). As medianas descritivas separam in-sample mas isso é esperado com famílias rotuladas; o árbitro (OOF) reprova.

**5. Runner-kill — não aplicável.**
- Nenhum gate foi adotado (verdict NO_CLEAN_FILTER). Portanto nenhum runner é cortado. Se o "review-layer D=HTF-fraco" for adotado no futuro, exigir medir runner-loss antes.

**6. Regime-confound — a causa provável do NO_EDGE.**
- O sinal descritivo mais forte (RSI-HTF: D fraco ~46, C sobrecomprado ~61, WIN meio ~56) correlaciona com o REGIME/ano (2025 bull vs 2026 bear/topo). Sob LOO, o classificador não generaliza porque a separação vive no regime, não numa regra intra-regime — o mesmo padrão do `ms_state` 15M anterior. A fonte RAW correta **não** resolve isto; é limite estrutural das features.

## Veredito DA
- **Análise CAUSAL e RAW-native limpa** (nenhum defeito de fonte/lookahead/resample). **Ganho real de processo:** 30M/1H extraídos do RAW; muro do Fractal-MTF removido.
- **NENHUM filtro preditivo sobrevive OOF+null.** As assinaturas de família são reais mas confundidas com regime; não formam gate honesto in-sample.
- **Recomendação:** tratar a assinatura de D (RSI-HTF fraco) como **hipótese ÚNICA a pré-registar** e julgar em **forward/janela virgem**; não promover como gate agora. Qualquer re-seleção in-sample re-incorre winner's-curse.
- **Não reportar como "filtro encontrado".** Reportar como: RAW-native audit limpo + NO_CLEAN_FILTER + 1 hipótese para forward.
