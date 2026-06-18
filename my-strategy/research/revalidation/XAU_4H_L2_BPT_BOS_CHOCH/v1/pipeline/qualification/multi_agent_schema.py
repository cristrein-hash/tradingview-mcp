#!/usr/bin/env python3
"""FASE 0 — Schema TIPADO do packet de 84 fatores + famílias de especialistas (engine multiagente).
INFRA DE AUDITORIA APENAS. Não roda agentes, não decide, não toca o engine atual.
Cada fator: type, source, causal, nullable, unit, bucket, description, allowed_families.
Metadados embutidos (versionados; SEM dependência runtime de /tmp). Ref design:
docs/XAU_4H_L2_BPT_MULTI_AGENT_ENGINE_DESIGN.md (§3a roster, §5 evidência)."""
from dataclasses import dataclass, field

# ---- famílias de especialistas (design §3a) ----
SPECIALIST_FAMILIES = [
 "context_classifier","macro_regime","htf_daily","auction_structure","demand_supply","volume_vp",
 "nas","bubbles","rsi_momentum","smc_structure","custom_ob","capitulation","liquidity_sweep",
 "exhaustion_top","entry_reclaim","risk_sl","session_time","historical_analogues","bull_beta",
 "volatility","causality_audit","devils_advocate","aggregator",
]
# context_classifier/causality_audit/devils_advocate/aggregator podem referenciar QUALQUER fator
WILDCARD_FAMILIES = {"context_classifier","causality_audit","devils_advocate","aggregator"}

# ---- metadados dos 84 fatores: name -> (type, null_rate_pct) ----
_META = {
 "episode_id":("categorical",96.4),"bar_idx":("int",0.0),"ts":("epoch",0.0),"datetime":("categorical",0.0),
 "price":("price",0.0),"atr":("price",0.0),
 "macro_leg_direction":("categorical",0.0),"macro_leg_phase":("categorical",0.0),
 "trend_30_atr":("float",0.0),"trend_90_atr":("float",0.7),"slope20_atr":("float",0.0),
 "dist_sma20_atr":("float",0.0),"dist_sma50_atr":("float",0.0),"price_vs_sma50":("categorical",0.0),
 "rsi_1d":("float",0.4),"rsi_1d_ma":("float",1.4),"rsi_1d_sub_ma":("bool",0.0),
 "drop20_atr":("float",0.0),"rise20_atr":("float",0.0),"rsi":("float",0.0),"rsi_min8":("float",0.0),
 "rsi_max8":("float",0.0),"rsi_vs_ma":("categorical",3.3),"rsi_drop_6b":("float",0.0),
 "consec_down":("int",0.0),"consec_up":("int",0.0),"range_exp":("float",0.0),"atr_level":("price",0.0),
 "atr_pctile_proxy":("float",0.7),"sweet_spot_falling_knife":("bool",0.0),
 "legpos30":("float",0.0),"legpos60":("float",0.0),"legpos90":("float",0.0),
 "rsi_bear_div_20b":("int",0.0),"rsi_bull_div_20b":("int",0.0),
 "nas_long_new_8b":("int",0.0),"nas_short_new_8b":("int",0.0),"nas_dist_ema_atr":("float",37.3),
 "nas_rsi":("float",3.3),"nas_1d_long_recent":("int",0.0),
 "bub_buy_s":("int",0.0),"bub_buy_m":("int",0.0),"bub_buy_L":("int",0.0),"bub_sell_s":("int",0.0),
 "bub_sell_m":("int",0.0),"bub_sell_L":("int",0.0),"bub_poc_recent":("int",0.0),"bub_buy_total":("int",0.0),
 "bub_sell_total":("int",0.0),"bub_buy_sell_ratio":("float",0.0),"bub_large_sell_10b":("int",0.0),
 "bub_large_buy_10b":("int",0.0),
 "has_4h_demand":("categorical",0.0),"dist_4h_demand_low_atr":("float",3.6),"demand_width_atr":("float",3.6),
 "demand_age_bars":("float",100.0),"demand_touched_on_retest":("categorical",0.0),
 "demand_origin_of_leg":("categorical",0.0),"has_d1_demand":("categorical",0.0),"dist_d1_demand_atr":("float",0.0),
 "has_4h_supply_overhead":("categorical",0.0),"dist_4h_supply_low_atr":("float",18.1),
 "supply_blocks_2ATR":("categorical",0.0),"supply_blocks_3ATR":("categorical",0.0),
 "supply_rejected_before":("categorical",0.0),"supply_broken_before":("categorical",0.0),
 "has_d1_supply":("categorical",0.0),"dist_d1_supply_atr":("float",21.4),
 "rel_volume":("float",1.8),"below_VAL":("bool",0.0),"dist_POC_atr":("float",0.0),"dist_VAL_atr":("float",0.0),
 "va_width_atr":("float",0.0),"smc_bos":("dict",58.7),"smc_choch":("dict",58.7),
 "reclaim_body_atr":("float",0.0),"reclaim_dist_from_demand_atr":("float",3.6),
 "reclaim_dist_from_supply_atr":("float",18.1),"sl_atr":("float",0.0),"sl_source":("categorical",0.0),
 "sl_type":("categorical",0.0),"F_STRICT_top_late":("bool",0.0),"hour_utc":("int",0.0),"dead_hour":("bool",0.0),
}

def _source(n):
    if n in ("smc_bos","smc_choch"): return "gz:SMC_LuxAlgo(pine_labels)"
    if n.startswith("nas"): return "gz:NAS(labels+study_values)/d1_sig"
    if n.startswith("bub"): return "gz/frozen:bubbles_recent(pine_shapes)"
    if n.startswith(("rel_volume","below_VAL","dist_POC","dist_VAL","va_width")): return "svp:SessionVP_native"
    if ("demand" in n or "supply" in n) and "d1" in n: return "csv:macro_context(D1)"
    if "demand" in n or "supply" in n or n.startswith("reclaim_dist"): return "csv:demand_supply_quality(gz OB as-of-bar)"
    if n.startswith(("macro_leg",)): return "csv:macro_context"
    if n.startswith(("rsi_1d","dist_d1")) or "d1" in n: return "frozen:daily_agg/csv"
    if n.startswith(("sl_",)) : return "derived:demand-anchored SL"
    return "frozen:OHLC/RSI (raw_features)"

def _unit(n,t):
    if t=="bool": return "bool"
    if t=="categorical": return "categorical"
    if n.endswith("_atr"): return "ATR"
    if n.startswith("legpos"): return "pct(0-100)"
    if n.startswith("rsi") or n in("rsi","nas_rsi"): return "rsi(0-100)"
    if n.startswith("bub") or n.startswith("consec") or "div" in n or n.endswith("_new_8b"): return "count"
    if n=="hour_utc": return "hour(0-23)"
    if n in("price","atr","atr_level"): return "price"
    if n=="ts": return "epoch_s"
    return "ratio/atr"

def _bucket(n):
    if n.startswith("legpos"): return "low<30 / mid 30-75 / high>75 / topo>=85"
    if n in("rsi","rsi_min8","rsi_max8","nas_rsi","rsi_1d"): return "oversold<30 / neutral 30-70 / overbought>70"
    if n.endswith("_atr") and ("demand" in n or "supply" in n): return "colada<=1 / perto<=2.5 / longe>5"
    if n=="dead_hour": return "UTC {2,18,20}"
    return ""

# ---- factor -> famílias permitidas (mandatos §3a; disjuntos por design) ----
def _families(n):
    f=set()
    META_META={"episode_id","bar_idx","ts","datetime","price","atr"}
    if n in META_META: return set()  # meta: contexto técnico, não citável como evidência decisória
    if n.startswith("macro_leg") or n in("trend_30_atr","slope20_atr","dist_sma20_atr","dist_sma50_atr","price_vs_sma50"): f|={"macro_regime"}
    if n=="trend_90_atr": f|={"macro_regime","bull_beta"}
    if n.startswith("rsi_1d") or n in("has_d1_demand","dist_d1_demand_atr","has_d1_supply","dist_d1_supply_atr"): f|={"htf_daily"}
    if n=="rsi_1d": f|={"macro_regime"}
    if n in("drop20_atr","rsi_drop_6b","consec_down","sweet_spot_falling_knife"): f|={"capitulation"}
    if n=="rise20_atr": f|={"exhaustion_top"}
    if n in("range_exp",): f|={"capitulation","volatility"}
    if n in("rsi","rsi_vs_ma","rsi_bull_div_20b"): f|={"rsi_momentum"}
    if n=="rsi_min8": f|={"rsi_momentum","capitulation"}
    if n in("rsi_max8","rsi_bear_div_20b"): f|={"rsi_momentum","exhaustion_top"}
    if n in("atr_level","atr_pctile_proxy"): f|={"volatility"}
    if n=="legpos90": f|={"exhaustion_top","liquidity_sweep","bull_beta"}
    if n in("legpos30","legpos60"): f|={"liquidity_sweep","macro_regime","bull_beta"}
    if n.startswith("nas"): f|={"nas"}
    if n.startswith("bub"):
        f|={"bubbles"}
        if "sell" in n: f|={"capitulation"}
        if "buy" in n: f|={"exhaustion_top"}
        if "poc" in n: f|={"auction_structure"}
    if "demand" in n: f|={"demand_supply","custom_ob","risk_sl"}
    if "supply" in n: f|={"demand_supply","risk_sl","exhaustion_top"}
    if n in("rel_volume","dist_POC_atr","dist_VAL_atr","va_width_atr"): f|={"volume_vp","auction_structure"}
    if n=="below_VAL": f|={"volume_vp","auction_structure","capitulation"}
    if n in("smc_bos","smc_choch"): f|={"smc_structure","entry_reclaim","liquidity_sweep"}
    if n in("reclaim_body_atr","reclaim_dist_from_demand_atr","consec_up","demand_touched_on_retest"): f|={"entry_reclaim"}
    if n=="reclaim_dist_from_supply_atr": f|={"entry_reclaim","risk_sl"}
    if n.startswith("sl_"): f|={"risk_sl"}
    if n=="F_STRICT_top_late": f|={"exhaustion_top","risk_sl"}
    if n in("hour_utc","dead_hour"): f|={"session_time"}
    if n in("demand_origin_of_leg","demand_age_bars"): f|={"custom_ob"}
    # historical_analogues e bull_beta: eixos-chave (NÃO outcome)
    if n in("drop20_atr","rsi_min8","legpos90","dist_4h_demand_low_atr","sl_atr","trend_90_atr"): f|={"historical_analogues"}
    if n in("trend_90_atr","legpos90","legpos60","rel_volume"): f|={"bull_beta"}
    return f

REPAINT_RISK={"smc_bos","smc_choch"}  # LuxAlgo pode repintar: usar direção/recência, não preço exato

@dataclass
class FactorSpec:
    name:str; type:str; source:str; causal:bool; nullable:bool; unit:str; bucket:str
    description:str; allowed_families:set; repaint_caveat:bool=False

FACTORS={}
for n,(t,nr) in _META.items():
    FACTORS[n]=FactorSpec(name=n,type=t,source=_source(n),causal=True,nullable=(nr>0.0),
                          unit=_unit(n,t),bucket=_bucket(n),
                          description=f"{n} ({_unit(n,t)}); null_rate={nr}%",
                          allowed_families=_families(n),repaint_caveat=(n in REPAINT_RISK))
# família -> fatores que pode citar
FAMILY_FACTORS={fam:set() for fam in SPECIALIST_FAMILIES}
for n,spec in FACTORS.items():
    for fam in spec.allowed_families: FAMILY_FACTORS.setdefault(fam,set()).add(n)
for fam in WILDCARD_FAMILIES: FAMILY_FACTORS[fam]=set(FACTORS)  # podem citar qualquer um

def is_factor(n): return n in FACTORS
def is_causal(n): return FACTORS[n].causal if n in FACTORS else False
def allowed_for(n,family):
    if family in WILDCARD_FAMILIES: return n in FACTORS
    return n in FACTORS and family in FACTORS[n].allowed_families

if __name__=="__main__":
    print(f"FATORES: {len(FACTORS)} | famílias: {len(SPECIALIST_FAMILIES)}")
    print("fatores citáveis por família:")
    for fam in SPECIALIST_FAMILIES:
        nf=len(FAMILY_FACTORS.get(fam,set()))
        print(f"  {fam:<20} {nf} fatores")
    print("repaint-risk:",REPAINT_RISK,"| meta (não-citáveis):", {n for n in FACTORS if not FACTORS[n].allowed_families})
