#!/usr/bin/env python3
"""WIRE — anexa as 3 lentes do Operating Manual (OM1/OM2/OM3) ao inventário da Camada 2 (schema da biblioteca),
para que fluam nos dossiês futuros via assembler. IDEMPOTENTE (não duplica). NÃO altera lentes existentes.
OM1/OM2 = POLARITY_DEPENDS_ON_CONTEXT (always-on); OM3 = WARNING_FAILURE_MODE (always-on). Origem: audit fase-3 c3839b8."""
import csv
INV = "results/l2_bpt_reader_layer2_evidence_inventory.csv"
# rows no schema do inventário: family|evidence_name|source|domain|saw_correctly|failed_isolated|status|reader_use|reader_not_use|helps
NEW = [
    ["MICRO", "supply_proximity_momentum_conditioned", "audit fase-3 c3839b8 ep4926",
     "interacao com supply overhead CONDICIONADA ao momentum (refina A3/E6/E7/D12)",
     "supply perto inverte pelo momentum: parede se fraco/esticado, alvo-a-consumir em impulso fresco forte",
     "4926 dist_supply 1.61ATR lido como freio era combustivel (monumental); nao inverter cegamente",
     "POLARITY_DEPENDS_ON_CONTEXT",
     "condicionar a leitura de supply ao momentum; impulso forte consome supply proximo (probe de inversao)",
     "NUNCA dist_supply como veto/gate binario; NUNCA threshold ATR fixo isolado",
     "markup-through-supply-vs-supply-rejection;preservar-monumentais"],
    ["REGIME", "bottom_turn_regime_conditioned", "audit fase-3 c3839b8 ep5701vs4918",
     "bottom_turn CONDICIONADO ao weekly (refina A8/F6/A1)",
     "bottom_turn so upgrada trap->absorcao quando weekly concorda; sob weekly<0 nao promove",
     "5701 bottom_turn sob weekly -0.22 induziu lean absorcao era trap (loser)",
     "POLARITY_DEPENDS_ON_CONTEXT",
     "checar weekly ANTES de promover bottom_turn a fundo/absorcao",
     "NUNCA bottom_turn isolado como sinal de fundo; nunca ignorar weekly",
     "reversao/fundo/capitulacao;bear-buy-legitimo-vs-trap"],
    ["MICRO", "recovery_apex_timing_penalty_cascade_neg", "audit fase-3 c3839b8 ep6887",
     "penalidade de TIMING: entry-no-apex de recuperacao em cascade negativo (refina A7/A10/I1)",
     "natureza pode estar certa mas apex de recuperacao em cascade-1 falha; comprar reteste de higher-low",
     "6887 pullback-continuacao certo na natureza mas entry no apex falhou (loser por timing nao leitura)",
     "WARNING_FAILURE_MODE",
     "flag de timing/risk-review; rotear entrada-boa-mal-temporizada para melhor entry, nao descarte",
     "NUNCA gate de SKIP (a natureza pode estar certa)",
     "reversao/fundo/capitulacao;topo/range/chop"],
]
existing = {r["evidence_name"] for r in csv.DictReader(open(INV), delimiter="|")}
to_add = [r for r in NEW if r[1] not in existing]
if not to_add:
    print("WIRE: as 3 lentes JA estao no inventario (idempotente, nada a fazer).")
else:
    # garante newline final antes de anexar
    data = open(INV).read()
    with open(INV, "a") as f:
        if not data.endswith("\n"):
            f.write("\n")
        for r in to_add:
            f.write("|".join(r) + "\n")
    print(f"WIRE: {len(to_add)} lentes anexadas ao inventario: {[r[1] for r in to_add]}")
# verificacao
rows = list(csv.DictReader(open(INV), delimiter="|"))
from collections import Counter
st = Counter(r["status"] for r in rows)
print(f"inventario agora: {len(rows)} lentes | POLARITY={st['POLARITY_DEPENDS_ON_CONTEXT']} WARNING={st['WARNING_FAILURE_MODE']}")
