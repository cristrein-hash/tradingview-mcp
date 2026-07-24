# Ground-truth inputs CONGELADOS · 2026-07-23

Snapshot estavel para cruzar com os trades ideais do Cris (camada-2).

- **signals_measured.json** — 61 sinais FRACO/FORTE ja emitidos, com MFE/MAE/verdito (janela 90min).
- **bars_5m_window.jsonl** — 575 barras 5M, 21/07 13:45 -> 23/07 17:15 (Lisboa).

## Como cruzar
Quando o Cris plotar os trades ideais (via chart/MCP pine_boxes/labels), o joiner alinha cada trade dele
por timestamp/preco contra `bars_5m_window.jsonl` e compara com o que o motor emitiu em `signals_measured.json`:
- trade ideal do Cris SEM sinal nosso no mesmo instante = MISS (o motor nao viu).
- sinal nosso FRACO num instante que o Cris marcou como trade bom = MISLABEL (rebaixou um bom).
- sinal nosso FORTE onde o Cris NAO marcou trade = FALSO-FORTE.
Dai sai o ground-truth: que leitura teria dado o rotulo certo.
