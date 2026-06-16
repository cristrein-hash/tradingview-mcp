# Rebuild v1 — XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5

**Data:** 2026-06-14 · **Tipo:** RECONSTRUÇÃO de fonte perdida. **NÃO é validação, NÃO promove, NÃO popula registry.**

## Objetivo
Restaurar a fonte técnica (código + trades reproduzíveis) da L1 EMA21_A + F5, perdida (era /tmp volátil), a partir do RAW 4H + da definição documentada na memória `project_caminho_a_L1_v1_F4F5_status_candidato_escasso`.

## Fontes usadas (RAW/canonical, sem SLIM)
- RAW 4H: `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz` (ohlcv + pine_boxes Custom OB v11).
- regime_B_v3: `candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl` (D-1 SHIFT1).
- EMA21/SMA50/ATR14/vol_ratio calculados causalmente dos closes.

## Resultado da reconstrução (rodada 1)
- **n=3** trades (2023-10 → 2025-04), sumR −0.3R, WR 33.3%, big15W=0, **reconciliation_status = MISMATCH** vs documentado (n=16, +31.74R, WR 43.8%, monumental 2024-03-26).
- ⚠️ **Isto NÃO é prova de que a estratégia não funciona** (warning NOT_VALIDATION no summary).

## Devil's Advocate (obrigatório) — veredito: RECONSTRUCTION_UNFAITHFUL_NEEDS_FIX
DA instrumentou o funil real do script. Achados:
1. **Os gates DISPARAM em 2020-2025** — **38 bars candidatos pré-cooldown**, incluindo as datas de winners documentados (2020-08-04, 2022-02-21, 2024-05-14, 2025-09-12/25). Não é refutação: a estratégia bate as datas certas.
2. **Colapso 38→3 = cooldown no-overlap** (`busy_until = idx[t_exit]` com TIME_STOP=60): um trade ativo bloqueia os candidatos seguintes em cascata. O original n=16 é incompatível com este cooldown agressivo → a semântica de cooldown/exit da reconstrução diverge da original.
3. **Trigger gap no monumental:** o bar **2024-03-26 não está nos 38 candidatos** (mais próximo 2024-04-02/10) → a definição exata de entry-trigger desse bar também diverge.
4. **Strictness assimétrica:** over-strict = cooldown, body≥0.35, F5≤1.0 (105→38, gate mais duro — questionar se F5 original era ≤1.0). Sem look-ahead NOVO introduzido; o único resíduo é o herdado do regime_B_v3 (~10.68%, NEEDS_AUDIT), que inflaria, não suprimiria.
5. **Veredito:** **RECONSTRUCTION_UNFAITHFUL_NEEDS_FIX** — corrigir cooldown/entry-trigger antes de qualquer conclusão de edge.

## Ressalvas / ASSUMPTIONs (ver config.json NOTES_UNKNOWN)
- ATR band [0.4,3.0] interpretado como ratio [0.004,0.030].
- OB demand zone = box geométrico abaixo do preço (RAW não traz label DEMAND/SUPPLY).
- EMA21_proxy fallback nunca disparou (OB sempre presente) → assumption #3 moot.
- regime_B_v3 com bias residual ~10.68% (NEEDS_SHIFT1_AUDIT) herdado.
- Sem lista de trades original → reconciliação só agregada (CANNOT_RECONCILE_NO_ORIGINAL_TRADES).

## Isto NÃO é validação
Os números acima NÃO provam nem refutam edge. São output de uma reconstrução **infiel** (rodada 1) cujo cooldown/trigger diverge do original.

## Próximos passos (separados, com autorização)
1. **Rebuild v2 — corrigir cooldown/exit semantics** (cooldown não deve serializar meses; rever se time-stop bloqueia entries seguintes) + investigar o entry-trigger do bar 2024-03-26.
2. Re-rodar e reconciliar agregado vs n=16.
3. Só DEPOIS de reconstrução fiel: lookahead/SHIFT1 audit + walk-forward. **Nada de promoção/registry antes disso.**
