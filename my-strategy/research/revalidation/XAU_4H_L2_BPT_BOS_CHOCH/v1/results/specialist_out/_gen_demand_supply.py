#!/usr/bin/env python3
"""Demand & Supply Quality Specialist — per-episode structured evidence.
ONLY emits factors in the allowed list; value copied EXACTLY from packet.
No decision / no performance language. Lens = demand defended near vs supply blocking target."""
import json, os

SAMPLE = os.path.join(os.path.dirname(__file__), '..', 'specialist_sample.jsonl')
OUT = os.path.join(os.path.dirname(__file__), 'demand_supply.jsonl')
SPEC = 'demand_supply'

# data-grounded thresholds (from observed quartiles of the 276-episode sample)
D4_NEAR = 2.16     # p25 dist_4h_demand_low_atr -> demand colada
D4_FAR  = 4.12     # p75 -> demanda longe, retest mal defendido
S4_NEAR = 0.97     # p25 dist_4h_supply_low_atr -> supply colado em cima
S4_FAR  = 3.18     # p75 -> espaco limpo acima
D1D_NEAR = 1.02    # p25 dist_d1_demand_atr
D1S_NEAR = 0.69    # p25 dist_d1_supply_atr
RCL_D_NEAR = 1.16  # p25 reclaim_dist_from_demand_atr

def ev(ep, factor, value, interp, impact, strength, dec, caveat=""):
    return {"specialist_id": SPEC, "episode_id": ep, "factor_used": factor,
            "value": value, "interpretation": interp, "impact": impact,
            "strength": strength, "decisive_or_supporting": dec,
            "caveat": caveat, "causal": True}

def process(r):
    ep = str(r["bar_idx"])
    E = []
    conflicts = []
    missing = []
    pos = 0; neg = 0  # net tally

    has_d = r["has_4h_demand"]
    dist_d = r.get("dist_4h_demand_low_atr")
    touched = r["demand_touched_on_retest"]
    origin = r["demand_origin_of_leg"]
    width = r.get("demand_width_atr")
    rcl_d = r.get("reclaim_dist_from_demand_atr")

    has_s = r["has_4h_supply_overhead"]
    dist_s = r.get("dist_4h_supply_low_atr")
    blk2 = r["supply_blocks_2ATR"]
    blk3 = r["supply_blocks_3ATR"]
    rej = r["supply_rejected_before"]
    brk = r["supply_broken_before"]

    has_d1d = r["has_d1_demand"]
    dist_d1d = r.get("dist_d1_demand_atr")
    has_d1s = r["has_d1_supply"]
    dist_d1s = r.get("dist_d1_supply_atr")

    # ---- DEMAND PRESENCE ----
    if has_d == "0":
        E.append(ev(ep, "has_4h_demand", "0",
            "Sem zona de demanda 4H identificada para defender o reclaim", "negative", "strong", "decisive"))
        neg += 2
        missing.append("dist_4h_demand_low_atr (sem demanda 4H)")
    else:
        # demand distance
        if dist_d is not None:
            if dist_d <= D4_NEAR:
                E.append(ev(ep, "dist_4h_demand_low_atr", dist_d,
                    "Demanda 4H colada abaixo do preco (<=p25), suporte proximo e defensavel", "positive", "strong", "decisive"))
                pos += 2
            elif dist_d >= D4_FAR:
                E.append(ev(ep, "dist_4h_demand_low_atr", dist_d,
                    "Demanda 4H distante (>=p75); reclaim opera longe do suporte estrutural", "negative", "medium", "supporting"))
                neg += 1
            else:
                E.append(ev(ep, "dist_4h_demand_low_atr", dist_d,
                    "Demanda 4H a distancia mediana do preco", "neutral", "weak", "supporting"))
        # touched on retest
        if touched == "1":
            E.append(ev(ep, "demand_touched_on_retest", "1",
                "Demanda foi tocada no retest: zona testada e defendida", "positive", "medium",
                "decisive" if has_s != "1" or dist_d is None else "supporting"))
            pos += 1
        else:
            E.append(ev(ep, "demand_touched_on_retest", "0",
                "Demanda nao tocada no retest: defesa nao confirmada por touch", "negative", "weak", "supporting"))
            neg += 1
        # origin of leg
        if origin == "1":
            E.append(ev(ep, "demand_origin_of_leg", "1",
                "Demanda e origem da perna: zona com pedigree estrutural", "positive", "medium", "supporting"))
            pos += 1
        # reclaim distance from demand
        if rcl_d is not None and rcl_d <= RCL_D_NEAR:
            E.append(ev(ep, "reclaim_dist_from_demand_atr", rcl_d,
                "Reclaim ocorre colado a demanda (<=p25): entrada perto do suporte", "positive", "medium", "supporting"))
            pos += 1

    # ---- SUPPLY OVERHEAD ----
    if has_s == "0":
        E.append(ev(ep, "has_4h_supply_overhead", "0",
            "Sem supply 4H em cima: espaco limpo de resistencia acima", "positive", "strong", "decisive"))
        pos += 2
        missing.append("dist_4h_supply_low_atr (sem supply overhead)")
    else:
        if dist_s is not None:
            if dist_s <= S4_NEAR:
                E.append(ev(ep, "dist_4h_supply_low_atr", dist_s,
                    "Supply 4H colado em cima (<=p25): resistencia imediata sobre o reclaim", "negative", "strong", "decisive"))
                neg += 2
            elif dist_s >= S4_FAR:
                E.append(ev(ep, "dist_4h_supply_low_atr", dist_s,
                    "Supply 4H distante (>=p75): espaco amplo ate a resistencia", "positive", "medium", "supporting"))
                pos += 1
            else:
                E.append(ev(ep, "dist_4h_supply_low_atr", dist_s,
                    "Supply 4H a distancia mediana acima", "neutral", "weak", "supporting"))
        # blocking flags
        if blk3 == "1":
            E.append(ev(ep, "supply_blocks_3ATR", "1",
                "Supply bloqueia dentro de 3 ATR: alvo estendido obstruido", "negative", "medium", "supporting"))
            neg += 1
        if blk2 == "1":
            E.append(ev(ep, "supply_blocks_2ATR", "1",
                "Supply bloqueia ja dentro de 2 ATR: alvo proximo obstruido", "negative", "strong",
                "decisive" if dist_s is None or dist_s > S4_NEAR else "supporting"))
            neg += 1
        elif blk3 == "0":
            E.append(ev(ep, "supply_blocks_2ATR", "0",
                "Supply nao bloqueia dentro de 2 nem 3 ATR: caminho relativamente livre", "positive", "medium", "supporting"))
            pos += 1
        # rejected vs broken
        if rej == "1":
            E.append(ev(ep, "supply_rejected_before", "1",
                "Supply overhead ja rejeitou preco antes: resistencia ativa/defendida", "negative", "medium", "supporting"))
            neg += 1
        if brk == "1":
            E.append(ev(ep, "supply_broken_before", "1",
                "Supply overhead ja foi quebrado antes: resistencia enfraquecida", "positive", "medium", "supporting"))
            pos += 1
            if rej == "1":
                conflicts.append("supply_rejected_before=1 e supply_broken_before=1: overhead com historico misto (rejeitou e quebrou)")

    # ---- D1 CONTEXT ----
    if has_d1d == "1" and dist_d1d is not None:
        if dist_d1d <= D1D_NEAR:
            E.append(ev(ep, "dist_d1_demand_atr", dist_d1d,
                "Demanda D1 colada (<=p25): suporte de timeframe superior apoia", "positive", "medium", "supporting"))
            pos += 1
        else:
            E.append(ev(ep, "dist_d1_demand_atr", dist_d1d,
                "Demanda D1 presente porem afastada do preco", "neutral", "weak", "supporting"))
    if has_d1s == "1" and dist_d1s is not None and dist_d1s <= D1S_NEAR:
        E.append(ev(ep, "dist_d1_supply_atr", dist_d1s,
            "Supply D1 colado em cima (<=p25): resistencia de timeframe superior contradiz", "negative", "medium", "supporting"))
        neg += 1
    elif has_d1s == "0":
        E.append(ev(ep, "has_d1_supply", "0",
            "Sem supply D1 acima: timeframe superior sem resistencia mapeada", "positive", "weak", "supporting"))
        pos += 1

    # ---- guarantee >=1 evidence and >=1 decisive ----
    if not E:
        # fallback: always have has_4h_demand present
        E.append(ev(ep, "has_4h_demand", has_d,
            "Presenca de demanda 4H registrada (leitura base)", "neutral", "weak", "decisive"))
    if not any(e["decisive_or_supporting"] == "decisive" for e in E):
        # promote strongest by tally direction
        # pick supply-near or demand-near or supply-clear as the structural pivot
        # default: mark the first strong/medium as decisive
        cand = max(E, key=lambda e: {"strong":2,"medium":1,"weak":0}[e["strength"]])
        cand["decisive_or_supporting"] = "decisive"

    # ---- net_read ----
    if neg - pos >= 2:
        net = "hostile"
    elif pos - neg >= 2:
        net = "supportive"
    else:
        net = "neutral"

    return {"episode_id": ep, "specialist_id": SPEC, "net_read": net,
            "evidence": E, "unresolved_conflicts": conflicts, "missing_data": missing}

def main():
    rows = [json.loads(l) for l in open(os.path.abspath(SAMPLE))]
    with open(os.path.abspath(OUT), 'w') as f:
        for r in rows:
            f.write(json.dumps(process(r), ensure_ascii=False) + "\n")
    print("episodes", len(rows))

if __name__ == "__main__":
    main()
