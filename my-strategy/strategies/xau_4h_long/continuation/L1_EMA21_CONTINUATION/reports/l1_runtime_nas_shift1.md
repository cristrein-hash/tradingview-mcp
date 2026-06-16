# L1 runtime live — NAS SHIFT1 causal + guarda close-only-causal (2026-06-16)

## O que foi feito
- **`tv_read_adapter.py`**: snapshot agora extrai `nas_dist` (NAS_DISTANCE_FROM_EMA_ATR, corrente) + OHLCV count 5→300 (p/ EMA21/SMA50/ATR14/swing/ret/BOS convergirem no runtime).
- **`runtime_xau.py`**: `evaluate` reusa **`scanner.evaluate`** (MESMOS gates) sobre uma `scanner.Series` construída do snapshot live. NAS SHIFT1 (bar i-1) vem de `.runtime_state/l1_feature_history.jsonl` (persistência append-only por ciclo, gitignored), **nunca o NAS atual**. Estados novos: `blocked_l1_refined_filter`, `blocked_missing_nas_shift1`, `blocked_missing_base_rule_live_fields`, `blocked_bar_not_closed`.

## Validação
- **Fixture (`test_nas_shift1.py`) PASS:** dado histórico i-1 nas=2.0 e snapshot atual nas=5.0 → o gate usa **2.0 (i-1)**, não 5.0; i-1 = penúltimo bar (sem futuro). Sem histórico → `blocked_missing_nas_shift1`. <60 bars → `blocked_missing_base_rule_live_fields`.
- **Live `--once` → `blocked_bar_not_closed`**, sem Telegram, **forming bar NÃO persistido** (guarda OK).

## DA — 9/10 PASS + 1 CRÍTICO corrigido
PASS: NAS SHIFT1 vem de i-1 (não atual); mesmos gates do scanner; sem proxy/futuro/recompute de NAS; vol_entry_z/regime_B_v3 ausentes; Telegram bloqueado em todo estado não-operacional; persistência segura/gitignored; convergência EMA/SMA/ATR em 300 bars (SMA50 exata, EMA21/ATR Wilder ~idênticas; divergência só epsilon em fronteira de threshold — LOW). 
**CRÍTICO (item 4) CORRIGIDO:** `data_get_ohlcv` traz o bar EM FORMAÇÃO como último → avaliar/persistir isso quebraria close-only-causal. **Guarda de bar-fechado adicionada** (só prossegue se `now ≥ bar_time+14400`); forming bar nunca é avaliado/persistido.
**MÉDIO (item 5):** zonas OB atuais atribuídas a i-1 (proxy causal — zonas persistem historicamente; pode diferir do scanner se zona nova/invalidada entre i-1 e agora). Aceitável, sinalizado.

## STATUS: runtime live = PARCIAL (causalmente seguro, NÃO operacional ainda)
Mecanismo NAS SHIFT1 correto + guarda close-only-causal aplicada. **Operacional bloqueado** porque, no timing do scheduler (+5min após fechamento), o snapshot traz o bar em formação como último → `blocked_bar_not_closed`. Para tornar operacional (bloco futuro, com autorização): alinhar a leitura ao bar JÁ FECHADO — opções: (a) `data_get_ohlcv` excluir o realtime / ler o penúltimo com seus study-values fechados; (b) capturar study-values do bar no fechamento; (c) tool MCP de histórico per-bar de study-value. Sem isso, runtime segue não-operacional/sem Telegram (honesto). scanner = gate autoritativo enquanto isso.

_Produção intacta. Telegram não enviado. Broker intocado. Histórico em .runtime_state (gitignored)._
