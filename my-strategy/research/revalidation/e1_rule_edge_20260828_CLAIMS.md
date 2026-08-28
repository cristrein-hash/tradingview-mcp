# EDGE POR RULE DO E1 — CORRIGIDO PELO DA (28/08)
BUGS no meu script (e1_rule_edge_20260828.py), apanhados pelo DA:
1. Dedup pela chave ERRADA (ts de emissão, não bar_time) → sweep_reclaim LONG inflado 4.7× (N297=63 reais).
2. Resolução a partir da emissão, não da barra do sinal (18% >1 dia depois = não-causal).
3. Mistura de TFs (240/15/60/1D) resolvidos como 15M.

NÚMEROS CORRIGIDOS (dedup por bar_time):
- sweep_reclaim LONG: −229R → −29R (era 4.7× contado + SL 0.16 ATR apertadíssimo, não "rule tóxica").
- sweep_reclaim SHORT: −194R → +5R (o −194 era só o mês de bull).
- Reader-aprovados (surfaced) TODOS breakeven/positivos (~+17R total, N minúsculo).

CONCLUSÃO (DA): NÃO cortar rules com base nisto. É 24 dias de bull, não 2 anos.
ÚNICO achado robusto (sobrevive a todos os fixes): ob_touch_hold LONG (+0.66) e zone_reject LONG (+0.71)
têm edge positivo. Tudo o resto é indistinguível do viés do mês / SL-apertado / pré-filtro.
Para decidir cortar: preciso RAW 2 anos + os 3 fixes + separar por TF + coorte surfaced. Não feito.
