# FORWARD PREREG — DISTRIB TRACKER SHADOW (selado 2026-08-28, ANTES de qualquer dado forward)
Decisões Cris: D1 desenho aprovado · D2 volume no store (feito) · D3 SÓ FORWARD (sem backtest) · D4 LPPLS sim.
Lição DA v2: critério de sucesso definido ANTES, senão forking-paths em forward.

## O que corre
distrib_tracker.py (launchd 300s, SHADOW log-only → logs/distrib_tracker.jsonl). Zero contacto com emissores.
Componentes b3 (no-demand) e b4 (value migration) amadurecem sozinhos (v desde 28/08; POC 2+ sessões).

## Critério de avaliação (selado)
- Janela mínima: 4 semanas de calendário OU N>=15 sinais LONG (a1a2+AMD-long+L1) emitidos com phase=B
  e score>=2 no tick mais próximo (<=300s) — o que demorar MAIS.
- Medição: cada sinal LONG emitido é etiquetado a posteriori com (phase, score) do tracker no envio;
  resolução SL-first 3R do ledger existente. Grupos: score>=2/phase B-C vs resto.
- Leitura de sucesso (referência, veredito final = Cris): grupo flaggeado avgR <= 0 E gap avgR >= 0.3R
  vs não-flaggeado E nenhum componente individual explica sozinho (senão o componente é o guard, não o score).
- Proibido durante o forward: mudar params/limiar/componentes (mudança = reinicia o relógio); usar o tracker
  para decisões live; qualquer wiring a emissor sem estudo fechado + ordem Cris.
