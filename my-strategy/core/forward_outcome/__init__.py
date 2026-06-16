"""Forward Outcome Layer — MVP Fase 1 (read-only).

Lê o event store live (`alert-bridge/logs/indicator_signals.jsonl`) e produz um
relatório de QUALIDADE forward — densidade, completude de payload, duplicatas,
parse errors. NÃO calcula R, NÃO compara backtest, NÃO envia Telegram, NÃO muta
o event store. Spec: docs/FORWARD_OUTCOME_LAYER_SPEC.md.

Importar este pacote NÃO tem side effects (nenhuma leitura/escrita em import).
"""
