# VISUAL POST-AUDIT REVIEW — Cluster 2 POST-ANCHOR-FIX — 2026-06-23

Obrigatório pós outcome-audit (canon). Prints/chart = `VISUAL_AUX_ONLY` (reconciliação visual final = Cris; não
capturei screenshots). Reconciliação estrutural RAW + flags p/ olho humano. Base: `reader_dossier_RAW_FROZEN.md`
(causal) + `phase3_audit_RAW_FROZEN_vs_outcome.md` + backbone causal.

## 8 checagens

1. **Mapping bar_idx→data:** 10/10 batem; anchor exato 10/10. ✓
2. **Causalidade da janela:** 10/10 `causal_window_ends_at_entry=True` (zero futuro). ✓
3. **close RAW vs frozen:** 4401 e 1775 com `anchor_close_fidelity=False` (feed ~$13) — flag de FEED, anchor exato; demais OK. ⚠ 4401/1775 (feed)
4. **supply/demand RAW vs visual (o eixo central):** 3949 SUPPLY_FAR(2.42) vs 3929 SUPPLY_BLOCKS(1.34) mesmo dia/macro; 5627 causal distSup=1.87 (era 0.84 contaminado). **Flag visual p/ Cris:** confirmar nos prints a geometria invertida 3949/3929 e o teto de 5627 mais afastado. ⚠ humano (mas outcome já confirmou 3949v3929)
5. **NAS/SMC/bubbles/RSI-div RAW vs visual:** 1873 div Regular Bearish explícita (trap mais limpo); 5826 sell_mL=16 longe. **Flag visual:** confirmar div bearish do 1873 e bubbles longe do 5826. ⚠ humano
6. **TPO/acceptance partial:** 3949=ACCEPTED_ABOVE (correu), 3929=INSIDE (parou) — coerente; 5627=ACCEPTED_BELOW (correu = limite do proxy). VA de volume bloqueada. ✓
7. **Campos BLOCKED:** volume VA=UNKNOWN_BLOCKED 10/10; reader flagou 5627/1623 como mais cegos — bate com os 2 casos onde o audit notou bloqueio honesto. ✓
8. **5627 muda? 3949/3929 segue confirmando geometria? weekly-neg=trap quebra?** Sim/Sim/Sim:
   - **5627:** o fix tirou de "supply colado 0.84 (confident trap)" para "1.87 SUPPLY_BLOCKS + resíduo hedgeado" → calibração melhor (REFUTED mas hedgeado, não confiante-errado). ✓ melhoria causal
   - **3949 vs 3929:** outcome confirmou LIMPO (6.62R vs 0.05R) — geometria é eixo causal real, **não artefato de look-ahead**. ✓✓ (achado mais forte)
   - **weekly-negativo = trap:** QUEBRADA (5826 16.73R, 3949 −0.6657 macro correu 6.62R). ✓

## Conclusões da revisão
- **Anchor fix melhorou a leitura do Cluster 2** (7/10 CONFIRMED vs versão contaminada): o eixo geometria-preço×supply emergiu LIMPO no par casado 3949/3929, e o 5627 melhorou calibração.
- **Lentes confirmadas (causal):** geometria-sob-macro-controlado (3949v3929, prova limpa), weekly-não-é-veto, entry-red-bar/esforço-de-comprador-ausente=trap (1873/3929/3825), forma>etiqueta.
- **Lente refutada/quarentenada:** WALL próximo ⇒ fade como REGRA (4401/5627 correram) — confirma a quarentena; o que separa é a CONJUNÇÃO (supply próximo × push-into/rejeição × esforço comprador ausente × div bearish), não a proximidade isolada.
- **Confidence:** não precisa recalibração global; os 2 REFUTED caíram onde a confiança já era a mais baixa (hedge). Bem calibrado.
- **Ação humana pendente:** checks #4/#5 (eyeball prints) + warnings de feed (4401/1775). Nada bloqueia conclusões.
