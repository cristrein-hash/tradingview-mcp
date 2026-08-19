# CONTRATO DE AUTORIDADE — REGIME + RAW CANÓNICO (2026-08-19)

Sela as decisões O4 + RC4-regime do DEEP_AUDIT_20260819. Documenta o que É, não muda comportamento.

## 1. REGIME — três representações, três papéis (NENHUMA é redundante; não fundir sem research)
- `my-strategy/core/layer1_service/.layer1_state/current_layer1.json` — **AUTORIDADE MACRO 1D**
  (macro_structural_v3, paridade 2981, USER_APPROVED 13/07; fundida no daemon regime-engine 19/07).
  Consumidores: ENTRY_ROUTER (roteamento BEAR/RANGE/BULL), AMD (contexto), context_engine, vigias.
  Limitação CONHECIDA (Cris 19/08): não imprimiu RANGE nos 2 ranges reais de 26/07-18/08 e atrasa nas
  viragens — PENDENTE research RANGE-recall-forward (ver memória signal-reorg). Override humano nas
  estratégias = padrão `*_REGIME_GATE_OFF` (validação manual do Cris manda).
- `my-strategy/core/regime_engine/.regime_state/current_regime.json` — **AUXILIAR 4H** (detetor v5;
  decisão A da auditoria 19/07: leitura auxiliar, nunca autoridade). Consumidores: mtf_cross, context_engine.
- `my-strategy/core/regime_l1/regime_l1_v4_classifications.jsonl` — **GATE INTERNO da estratégia L1**
  (D-1 causal, matemática congelada da aprovação; NÃO é leitura de mercado geral). Consumidores: L1
  scanner/runtime (atualmente neutralizado por L1_REGIME_GATE_OFF=1 no wrapper, ordem Cris 05/08+19/08).
Regra: novo consumidor de "regime" usa current_layer1.json salvo justificação escrita.

## 2. RAW CANÓNICO — localização e provenance (O4: NÃO mover nesta fase)
- `my-strategy/research/revalidation/raw_1h_ohlc.jsonl`, `raw_4h_ohlc.jsonl`, `raw_dxy_1d.jsonl`
  são RAW CANÓNICO DE PRODUÇÃO apesar do path research/ (histórico + cauda live).
- ESCRITOR-DONO: bar_store_cycle.py (extend de barras fechadas, atómico, guard anti-truncamento).
  Escritor secundário tolerado: regime_engine_cycle.py APENAS no ramo mcp-fallback (store stale);
  risco lost-update raro documentado (C7) — qualquer 3º escritor é PROIBIDO.
- LEITORES: store_reader (60/240), layer1_cycle (1D/DXY), research via raw_reader (.gz históricos).
- Retenção: infinita (retain None). NUNCA truncar/reescrever histórico; gzip lossless permitido (política
  DATA_STORAGE). Qualquer cleanup em research/revalidation/ TEM de excluir raw_*.jsonl.

## 3. SL-FIRST — implementações vivas (RC4; consolidação DIFERIDA por segurança)
Existem 4 implementações: scoreboard.resolve, router run_B (delega b_forward_score), copilot/journal
(resolve+capture). Fundir exige provar equivalência byte-a-byte (semânticas de fronteira podem divergir)
= mudança de outcomes se mal feita → fica REGISTADO como pendência, não executado no cleanup 19/08.
Política canónica: SL avaliado ANTES do target na mesma barra; i0 = primeira barra t > t_entrada.
