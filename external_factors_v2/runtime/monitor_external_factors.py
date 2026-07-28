#!/usr/bin/env python3
"""FASE 2 — MONITOR de External Factors (spine always-active). Um CICLO de monitoração das fontes canônicas:
- Tier-1 macro: últimos valores + frescor + needs_refresh por cadência (FRED keyless via macro_panel/refresh)
- Camada A (reação imediata): calendário de eventos US de alto impacto (NFP/jobless/ADP) com release_ts + proximidade
- Camada B (macro lento): tendência de real-yield/USD/curva (rotação de smart money)
- source_health por fonte canônica (ok/stale/pending) + freeze do estado.
Determinístico, Python 3.9 (sem SDK). LaunchAgent persistente = sign-off do Cris (este roda on-demand)."""
import json,subprocess,bisect,datetime as dt,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
try:
    from load_env import load_env; load_env()
except Exception: pass
H=Path(__file__).parent.parent
NOW=dt.datetime.now(dt.timezone.utc); NOWT=int(NOW.timestamp())
WL=json.loads((H/"config/sources_whitelist.json").read_text())
REG=json.loads((H/"config/factor_registry.json").read_text())
PANEL={}
pf=H/"snapshots/macro_panel.jsonl"
if pf.exists():
    for l in pf.read_text().splitlines():
        r=json.loads(l); PANEL.setdefault(r["series_id"],[]).append((r["obs_date"],r["value"]))
    for k in PANEL: PANEL[k].sort()
def latest(sid):
    a=PANEL.get(sid); return a[-1] if a else None
def chg(sid,days):
    a=PANEL.get(sid)
    if not a: return None
    t1=a[-1][0]; v1=a[-1][1]; tgt=t1-days*86400
    i=bisect.bisect_right(a,(tgt,float("inf")))-1
    return round(v1-a[i][1],3) if i>=0 else None
# ---- Tier-1 estado + frescor ----
CAD={"daily":3,"monthly":45}
tier1={}; stale=[]
for s in REG["tier1_series"]:
    lt=latest(s["id"])
    if not lt: tier1[s["id"]]={"status":"no_data"}; stale.append(s["id"]); continue
    age=(NOWT-lt[0])/86400; fresh= age<=CAD.get(s["cadence"],3)*2
    tier1[s["id"]]={"value":lt[1],"obs_age_days":round(age,1),"fresh":fresh,"chg20":chg(s["id"],20),"driver":s["driver"]}
    if not fresh: stale.append(s["id"])
# ---- Camada A: calendário via coletor ForexFactory (keyless, snapshots/ff_calendar.json) ----
# Substitui o gerador 1ª-sexta (bug shift feriado) + overlay manual. Datas/consenso/actual REAIS do feed FF.
ffc=H/"snapshots/ff_calendar.json"; events=[]
if ffc.exists():
    try: events=json.loads(ffc.read_text()).get("events",[])
    except Exception as ex: print("[warn] ff_calendar read falhou:",ex)
else:
    print("[warn] ff_calendar.json ausente — rode collectors/forexfactory_collect.py")
events.sort(key=lambda e:e["release_ts"])
for e in events: e["hours_until"]=round((e["release_ts"]-NOWT)/3600,1)
imminent=[e for e in events if 0<=e["hours_until"]<=96]
# ---- Camada texto: Fed RSS (keyless) + Alpha Vantage market news (key) ----
nf=H/"snapshots/news_feed.json"; news_recent=[]
if nf.exists():
    try: news_recent=json.loads(nf.read_text()).get("recent_le7d",[])
    except Exception: pass
mn=H/"snapshots/market_news.json"; market_news=[]
if mn.exists():
    try: market_news=json.loads(mn.read_text()).get("recent_le72h",[])
    except Exception: pass
# ---- News lane rápida (InvestingLive RSS keyless, coletor próprio ~4min) snapshots/investinglive_news.json — advisory ----
il=H/"snapshots/investinglive_news.json"; news_live={}
if il.exists():
    try: news_live=json.loads(il.read_text())
    except Exception: pass
_nl_gate=news_live.get("gate",{}); _nl_items=news_live.get("items",[])
news_headline_reason=[f"HEADLINE HI: {_nl_items[0]['title'][:70]}"] if _nl_gate.get("high_impact_headline") and _nl_items else []
# ---- Ouro: fontes canônicas (CME/COMEX preço+COT, keyless+FMP) snapshots/gold_data.json ----
gf=H/"snapshots/gold_data.json"; gold={}
if gf.exists():
    try: gold=json.loads(gf.read_text())
    except Exception: pass
gold_ok=bool(gold.get("price_comex",{}).get("price_usd") or gold.get("cot_comex",{}).get("noncomm_net") is not None)
# ---- Fed path (proxy CME FedWatch via slope da curva, keyless) snapshots/fed_path.json ----
fpf=H/"snapshots/fed_path.json"; fed_path={}
if fpf.exists():
    try: fed_path=json.loads(fpf.read_text())
    except Exception: pass
# ---- Teorias (núcleo humano credível não-dealer) snapshots/theory_feed.json ----
tff=H/"snapshots/theory_feed.json"; theory={}
if tff.exists():
    try: theory=json.loads(tff.read_text())
    except Exception: pass
theory_recent=theory.get("recent",[])
tsb=H/"snapshots/theory_scoreboard.json"; theory_board={}
if tsb.exists():
    try: theory_board=json.loads(tsb.read_text())
    except Exception: pass
nfp_next=next((e for e in imminent if e["event"].lower().startswith("nonfarm")),None)
nfp_bias=(nfp_next or {}).get("direction",{}).get("bias") if nfp_next else None
# CPI/FOMC/PCE = via Calendar agent (Phase 3); marcados pendentes
# ---- Camada B: macro lento (rotação) ----
layerB={
 "real_yield_10y": {"value":tier1.get("us10y_real",{}).get("value"),"chg20":tier1.get("us10y_real",{}).get("chg20"),"gold_read":"queda=favorável"},
 "usd_broad":      {"value":tier1.get("usd_broad",{}).get("value"),"chg20":tier1.get("usd_broad",{}).get("chg20"),"gold_read":"queda=favorável"},
 "curve_2s10s":    {"value":tier1.get("curve_2s10s",{}).get("value")},
 "vix":            {"value":tier1.get("vix",{}).get("value")},
}
# ---- source_health (fontes canônicas) ----
health=[]
for s in WL["sources"]:
    if s["kind"]=="macro_numeric" and s["id"] in ("FRED",):
        st="ok" if not stale else "partial_stale"
    elif s["id"]=="FED_RSS":
        st="live_keyless_fed_rss" if news_recent else "no_data"
    elif s["kind"]=="news":
        st="live_av_news" if market_news else "needs_vendor_key"   # Reuters/Bloomberg/FT abastecidos via Alpha Vantage
    elif s["id"]=="CME":
        st="live_gold_cme" if gold_ok else "no_data"   # preço GCUSD + COT positioning
    elif s["id"]=="LBMA":
        st="price_via_comex_futures"  # fixing descontinuado no FRED; benchmark=GCUSD
    elif s["id"]=="WGC":
        st="context_on_demand"  # relatórios demanda/ETF/central-bank (sem API free)
    elif s["id"]=="CME_FEDWATCH":
        st="live_proxy_curve" if fed_path.get("rate_path_bias") else "no_data"  # ZQ paywalled -> slope curva keyless
    elif s["tier"]=="tier2":
        st="context_on_demand"
    elif s["kind"]=="calendar":
        if s["id"]=="FOREXFACTORY": st="live_keyless" if events else "no_data"  # feed JSON FairEconomy
        else: st="cross_check_webfetch"  # TradingEconomics = cross-check on-demand
    else:
        st="configured"
    health.append({"id":s["id"],"tier":s["tier"],"status":st,"headless_safe":s["headless_safe"]})
# fontes de TEORIA (núcleo humano não-dealer) — keyless RSS (dedup vs whitelist)
_hids={h["id"] for h in health}
for tsid in (theory.get("_meta",{}).get("sources") or []):
    if tsid in _hids:
        for h in health:
            if h["id"]==tsid: h["status"]="live_theory_rss" if theory_recent else h["status"]
        continue
    health.append({"id":tsid,"tier":"tier2","status":"live_theory_rss" if theory_recent else "no_data","headless_safe":True})
state={
 "_meta":{"module":"external_factors_v2","cycle_ts":NOWT,"cycle_dt":NOW.strftime("%Y-%m-%d %H:%M UTC"),"status_classification":"recorded_context (Tier-1 sem edge validado; uso=contexto/flag human-in-loop)"},
 "tier1_macro_recorded_context":tier1,
 "layer_A_immediate_events":events,
 "layer_A_imminent_le96h":imminent,
 "layer_B_slow_macro":layerB,
 "layer_text_news_recent":news_recent[:10],
 "layer_market_news_recent":market_news[:12],
 "news_live":{k:news_live.get(k) for k in ("fetch_ts","fetch_age_s","high_impact_now","urgency","gate","n_relevant")} if news_live else None,
 "layer_gold_canonical":{"price_comex":gold.get("price_comex"),"cot_comex":gold.get("cot_comex"),"wgc":gold.get("wgc")},
 "layer_fed_path":{k:fed_path.get(k) for k in ("target_midpoint","sofr_overnight","short_curve","slope_6m_1m_bp","rate_path_bias","gold_read","next_fomc","_meta")},
 "layer_theory_core":{"recent":theory_recent[:12],"ledger_total":theory.get("ledger_total"),"new_this_cycle":theory.get("new_this_cycle"),
   "scoreboard":theory_board.get("scoreboard"),"theory_consensus":theory_board.get("theory_consensus"),
   "scored_total":theory_board.get("scored_total"),"claims_total":theory_board.get("claims_total")},
 "source_health":health,
 "stale_series":stale,
 # schema external_* (consumo claude_recheck) — neutro até Tier-2 agents (Phase 3)
 "external_factors":{"external_bias":"unknown","external_risk_level":"event_window" if imminent else "normal",
   "external_trade_validation":"neutral","external_confidence":0,"external_fetch_ok":True,"external_stale":bool(stale),
   "external_event_direction_bias":nfp_bias,
   "external_main_reasons":news_headline_reason+[f"{e['event']} em {e['hours_until']}h"+(f" (consenso {e.get('consensus')} vs ant {e.get('previous')} -> {e.get('direction',{}).get('bias')})" if e.get('consensus_k') is not None else "") for e in imminent],
   "external_us10y_real":tier1.get("us10y_real",{}).get("value"),"external_usd_broad":tier1.get("usd_broad",{}).get("value"),
   "external_vix":tier1.get("vix",{}).get("value")}
}
SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
(SNAP/f"state_{NOWT}.json").write_text(json.dumps(state,indent=1))
(SNAP/"latest.json").write_text(json.dumps(state,indent=1))
# ROTAÇÃO (Cris 2026-07-28): os state_<ts> são snapshots write-only (nada os lê de volta; latest.json é o
# corrente). Sem cap acumulavam ~45/dia. Mantém só as últimas 24h; apaga os mais antigos. Fail-soft.
try:
    _cut=NOWT-86400
    for _p in SNAP.glob("state_*.json"):
        try:
            if int(_p.stem.split("state_")[-1])<_cut: _p.unlink()
        except Exception: pass
except Exception: pass
# ---- report ----
print(f"=== EXTERNAL FACTORS MONITOR — ciclo {state['_meta']['cycle_dt']} ===")
print(f"Tier-1 macro (recorded_context): {sum(1 for v in tier1.values() if v.get('fresh'))}/{len(tier1)} fresh | stale: {stale or 'nenhum'}")
print(f"  real_yield_10y={tier1.get('us10y_real',{}).get('value')} (Δ20={tier1.get('us10y_real',{}).get('chg20')}) | USD_broad={tier1.get('usd_broad',{}).get('value')} (Δ20={tier1.get('usd_broad',{}).get('chg20')}) | VIX={tier1.get('vix',{}).get('value')}")
print(f"\nCamada A — eventos imediatos próximos (≤96h): {len(imminent)}")
for e in imminent:
    extra=f" | consenso {e.get('consensus')} vs ant {e.get('previous')} -> dir={e.get('direction',{}).get('bias')}" if e.get('consensus_k') is not None else (f" | consenso {e.get('consensus')}" if e.get('consensus') else "")
    src=" [ForexFactory]" if e.get("source","").startswith("ForexFactory") else ""
    print(f"  [{e['impact']}] {e['event']} — {e['date']} (em {e['hours_until']}h){src} | {e['driver']}{extra}")
from collections import Counter as _C
_hc=_C(h['status'] for h in health)
print(f"\nsource_health: "+" ".join(f"{k}={v}" for k,v in _hc.items()))
print(f"news/Fed (keyless): {len(news_recent)} ≤7d | market news (Alpha Vantage): {len(market_news)} ≤72h -> abastece fed-tone/news/geopolitical/risk")
_gp=gold.get("price_comex",{}); _gc=gold.get("cot_comex",{})
print(f"OURO (CME/COMEX): preço {_gp.get('price_usd')} ({_gp.get('change_pct')}%) | COT net {_gc.get('noncomm_net')} ({_gc.get('report_date')}) -> abastece gold-driver")
print(f"FED PATH (proxy FedWatch keyless): midpoint={fed_path.get('target_midpoint')} SOFR={fed_path.get('sofr_overnight')} | slope6m-1m={fed_path.get('slope_6m_1m_bp')}bp -> {fed_path.get('rate_path_bias')} (gold {fed_path.get('gold_read')})")
_tc=theory_board.get("theory_consensus",{}) or {}
print(f"TEORIAS (núcleo não-dealer): {len(theory_recent)} recentes | ledger {theory.get('ledger_total')} | claims {theory_board.get('claims_total')} scored {theory_board.get('scored_total')} | consenso ponderado={_tc.get('label')} (CONTEXTO, não-gate)")
print(f"external_risk_level={state['external_factors']['external_risk_level']} | freeze -> snapshots/latest.json")
