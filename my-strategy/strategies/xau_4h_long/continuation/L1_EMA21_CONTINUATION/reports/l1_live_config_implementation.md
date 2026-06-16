# L1 — Implementação da config aprovada no scanner (2026-06-16) — IN-SAMPLE

`scanner.py` agora implementa a config APROVADA: stack v1 (ret5≤1.42% + ext_ema≤2.95ATR + zone_w≥0.6ATR + dist_zone≤1.81ATR) + NAS SHIFT1≥1.31 + RSI gate(≤−9.35) + SL estrutural max(zona_OB_low, swing6_low)−0.1ATR + target +3R. vol_entry_z e regime_B_v3 ausentes do código (só comentário). Regime via regime_l1_v4.

## Validação full-scan 2020-2026
- **31 operacionais · 17 TARGET / 13 STOP / 1 TIME · sumR +40.0R · PF 4.08 · 5/5 monumentais · #3 removido.**
- **Reconciliação vs estudo (34):** os 3 a menos (#26/#31/#47) são `blocked_exhaustion` (RSI≤−9.35). O estudo não aplicou o gate de exaustão como exclusão dura; o scanner aplica (config aprovada mantém o gate). → scanner-31 = estudo-34 − 3 RSI-blocked. Realização FIEL.
- Causalidade: NAS i-1 (SHIFT1), SL/swing6/ret5/ext_ema usam só barras ≤ bar i. DA 10/10 PASS.

## Runtime live — HARD STOP (regra #10)
NAS_DISTANCE no bar i-1 **não é extraível** do snapshot MCP live (study_value só corrente; sem histórico per-bar; recompute proibido). Runtime live segue **não-operacional** (também falta base-rule live). **scanner = gate autoritativo.** Desbloqueio = bloco futuro (persistir NAS por ciclo ou tool MCP de study-history).

## Caveats (DA)
In-sample (sem OOS, risco assumido pelo Cris). Alvo +3R fixo ≠ V_stair de produção (config aprovada usa +3R). PF 4.08 é exit-defined + in-sample. Thresholds congelados nos próprios dados 2020-2026.

_Produção (scheduler→runtime) NÃO alterada por este bloco: o scanner não é chamado pelo runtime; runtime segue não-operacional + sem Telegram._
