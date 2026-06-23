# VISUAL POST-AUDIT REVIEW — Cluster 1 POST-ANCHOR-FIX — 2026-06-23

Obrigatório pós outcome-audit (canon). Prints/chart = `VISUAL_AUX_ONLY` (nunca fonte primária; reconciliação
visual final fica para Cris — não capturei screenshots). Reconciliação estrutural RAW + flags p/ olho humano.
Base: `reader_dossier_RAW_FROZEN.md` (causal) + `phase3_audit_RAW_FROZEN_vs_outcome.md` + backbone causal.

## 8 checagens

1. **Mapping bar_idx→data:** 9/9 timestamps batem com o frozen; anchor exato 9/9. ✓
2. **Causalidade da janela:** 9/9 `causal_window_ends_at_entry=True` (zero barra futura). ✓ (este é o ganho do bloco)
3. **close RAW vs frozen:** 1661 com `anchor_close_fidelity=False` (feed PEPPERSTONE ~$13 ≠ frozen) — flag de FEED, anchor exato por timestamp; demais OK. ⚠ 1661 (feed, não look-ahead)
4. **supply/demand RAW vs visual:** sup_cat/dist causal coerentes (4918 SUPPLY_FAR distSup=4.01 distDem=0.02 = demanda colada; 4926 SUPPLY_BLOCKS). **Flag visual p/ Cris:** confirmar nos prints que 4918 está sobre demanda fresca e 4926 sob blocos de supply. ⚠ humano
5. **NAS/SMC/bubbles/RSI-div RAW vs visual:** era-correta (tail as-of-bar), sem head stale; 4918 RSI35+div bullish, 8923 RSI82 parabólico. **Flag visual:** confirmar cluster NAS/bubbles nos prints. ⚠ humano
6. **TPO/acceptance:** proxy de TEMPO, não volume VA; 4926=ACCEPTED_ABOVE (correu — coerente c/ runner), 4918=INSIDE (VA de volume bloqueada limitou). Honesto. ✓
7. **Campos BLOCKED:** volume VA = UNKNOWN_BLOCKED em 9/9; reader flagou 8923/8878/4926/7426 como mais cegos — bate com onde o audit achou o árbitro ausente. ✓
8. **4918 vs 4926 + lentes:** o reader leu OPOSTO; outcome mostra GÊMEOS (ambos ~18-19R monster). **Veredito visual:** a discriminação "geometria de wall ⇒ sem-edge" do 4926 é REFUTADA pelo chart (a alta atravessou os blocos). Confirmar visualmente que 4926 absorveu o supply. ⚠ humano

## Conclusões da revisão
- **Anchor fix mudou veredito?** Sim em parte: 4918 ficou um CONFIRMED contrarian mais limpo (causal: demanda 0.02ATR + RSI35+div). Mas **4926 segue REFUTED** (lido wall/sem-edge, correu 18R) — agora com confiança maior, o que é *pior* calibração nesse caso isolado. Líquido C1: parecido com pré-fix (4C/2M/3R vs 5C/3R/1M).
- **Lente confirmada:** regime-inverte-significado (4918 vs 1661), RSI-blow-off (8923 RSI82), FUEL distante (6887/8940 direção certa).
- **Lente REFUTADA/quarentenada (reconfirmado causal):** supply-WALL/geometria-colada ⇒ fade/sem-edge — over-fade runners (4926, 8878 wall+correram). **Não vira regra.**
- **Ação humana pendente:** checks #4/#5/#8 (eyeball prints) + warning de feed do 1661. Nada bloqueia as conclusões de lente.
