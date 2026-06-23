# VISUAL POST-AUDIT REVIEW — Cluster 1 COM VALUE-AREA real — 2026-06-23

Obrigatório pós outcome-audit. Prints = VISUAL_AUX_ONLY (reconciliação visual = Cris; não capturei). Base:
`reader_dossier_RAW_FROZEN.md` (com VA) + `phase3_audit_RAW_FROZEN_vs_outcome.md` + backbone causal + VA real (F6/svp_bars).

## 8 checagens
1. **Mapping bar_idx→data:** 9/9 batem; anchor exato 9/9. ✓
2. **Causalidade:** 9/9 janela termina na entry (sem futuro). ✓
3. **VA real as-of-entry:** svp_state/dist_poc do F6 validado (7f3c852); POC/VAH/VAL de svp_bars. ✓
4. **VA STATE vs outcome:** `ACCEPTING_ABOVE_VALUE`+não-bear → correu (4918); em BEAR (1661/5701) o regime sobrepôs a VA (stop, lido corretamente como trap). ✓ regime-conditioned
5. **dist_poc MAGNITUDE (o erro):** o reader leu dist_poc grande (4926=2.07) como sobre-extensão → **REFUTED** (correu +18R). **Flag visual p/ Cris:** confirmar nos prints que 4926 é continuação saindo do valor, não topo. ⚠ erro de interpretação
6. **NAS/SMC/bubbles/RSI-div RAW:** era-correta. ✓
7. **Campos:** VA agora disponível (não-BLOCKED); nenhum campo inventado. ✓
8. **4918 vs 4926:** a VA SPLITOU os gêmeos ERRADO (manteve 4918 CONFIRMED, rebaixou 4926 a sobre-extensão=REFUTED). **A VA converteu 1 leitura certa (sem-VA: gêmeos) em 1 errada.** ⚠

## Conclusões
- A VA **ajudou** onde é STATE-puro (8878 in-value pullback: REFUTED→CONFIRMED vs sem-VA).
- A VA **atrapalhou** onde virou magnitude-de-extensão (4926) ou confiança falsa (6887 REFUTED).
- **Lente sobrevivente:** VA STATE `ACCEPTING_ABOVE_VALUE` (regime-permitindo) = construtivo.
- **Lente FALHA:** `dist_poc grande = exaustão/topo` — invertido em bull (momentum sai do valor pra correr). NÃO usar como exaustão.
- Ação humana: check #5/#8 (eyeball 4926/6887).
