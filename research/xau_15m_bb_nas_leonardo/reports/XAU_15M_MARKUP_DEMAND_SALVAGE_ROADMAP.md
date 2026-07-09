# XAU 15M MARKUP-DEMAND — SALVAGE ROADMAP
**2026-07-09.** Honesto e orientado a RESOLVER a 15M. Nenhum caminho assume edge.

## Caminho A — Opção A: entry pós-confirmação (`conf_i`)
Fiel ao conceito original "demanda de perna confirmada". Entries só após o pivô confirmar (rally 6 ATR); janela de reclaim de conf_i; filtro capitulation + SL V1 + 3R transferidos. Trade-offs: timing tardio (mediana ~20 barras), N menor, entry mais longe do low. **Teste: WR/DD melhoram vs Opção B?** Status: next rigorous salvage test (prereg pronto).

## Caminho B — Lab BULL bucket
Partir da base causal Option B; isolar regime BULL (44,4%/PF 2,4/n45); protocolo 15M completo (manifest→guard→buckets→ledger→DA); NÃO assumir edge; investigar se é estratégia própria (ex.: markup-demand só-BULL).

## Caminho C — Novo detector markup-demand causal
Reconstruir a deteção de demanda SEM pivô futuro (ex.: demanda = zona OB nativa/estrutura confirmada em tempo real, não zigzag retroativo); primitives live-fireable; capitulation como risk-control; SL/exit transferidos. Mais trabalho, mais fiel ao live.

## Caminho D — Desmontar o pacote, preservar componentes
Abandonar N96/N83 como estratégia; manter: filtro capitulation (risk-control transversal 15M), SL V1, exit 3R, BULL lead, motor live-fireable (lib). Voltar a 15M mais tarde.

## Recomendação técnica
1. **Executar Opção A primeiro** — é o teste direto de "salvar a demanda de perna original" e custa pouco (motor pronto).
2. **Se A falhar → abrir BULL bucket lab** (caminho B) como investigação própria.
3. **Nenhuma produção 15M até um caminho passar** protocolo completo + DA + decisão do Cris.
