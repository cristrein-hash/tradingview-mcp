#!/usr/bin/env python3
"""EXTRAI bubbles do RAW (Market Order Bubbles - By Leviathan), first-appearance CAUSAL por (time,plot) — igual NAS.
Mapping a AUDITAR (não assumir): BUY=plot_0/2/4(s/m/L), SELL=plot_6/8/10(s/m/L), POC=plot_12.
Âncora de preço = bar do `time` nos primitives. known_at = replay_current_dt do snapshot 1ª-aparição (causal).
AUDITORIA empírica do mapping: ordem de mercado BUY agressiva LEVANTA o preço → bar onde bate tende a ser de ALTA;
SELL → de BAIXA. Se BUY up-bar% NÃO > SELL up-bar%, mapping suspeito. Escreve bubbles/{key}.bubbles.jsonl. 2026-06-26."""
import gzip,json,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent; RAW=Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
OUT=HERE/"bubbles"; OUT.mkdir(exist_ok=True)
BUY={"plot_0":"S","plot_2":"M","plot_4":"L"}; SELL={"plot_6":"S","plot_8":"M","plot_10":"L"}
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z","+00:00")).timestamp())
    except Exception: return None
keys=[p.name.replace("XAUUSD_15m_replay_","").replace(".primitives.json","") for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
agg={"BUY":{"S":0,"M":0,"L":0},"SELL":{"S":0,"M":0,"L":0}}
audit={"BUY":[0,0],"SELL":[0,0]}  # [up_bars, total]
lag=[]
for key in keys:
    gz=RAW/f"XAUUSD_15m_replay_{key}.jsonl.gz"
    prim=json.loads((HERE/"primitives"/f"XAUUSD_15m_replay_{key}.primitives.json").read_text())
    bar={b["t"]:b for b in prim["series"]}
    seen={}  # (time,plot) -> known_at_ep
    with gzip.open(gz) as fh:
        for line in fh:
            r=json.loads(line); b=r.get("pine_shapes_bubbles")
            if not b: continue
            ka=iso2ep(r.get("replay_current_dt") or "")
            for act in (b[0].get("activations") or []):
                tt=act.get("time")
                for plot,cnt in (act.get("shapes") or {}).items():
                    if plot not in BUY and plot not in SELL: continue
                    k=(tt,plot)
                    if k in seen: continue
                    seen[k]=ka
    rows=[]
    for (tt,plot),ka in seen.items():
        side="BUY" if plot in BUY else "SELL"; size=(BUY if side=="BUY" else SELL)[plot]
        bb=bar.get(tt)
        if bb is None: continue
        agg[side][size]+=1
        up=1 if bb["c"]>bb["o"] else 0; audit[side][0]+=up; audit[side][1]+=1
        if ka and ka>=tt: lag.append((ka-tt)/900.0)
        rows.append({"t":tt,"plot":plot,"side":side,"size":size,"known_at":ka,
                     "o":bb["o"],"h":bb["h"],"l":bb["l"],"c":bb["c"],"atr":bb["atr"]})
    rows.sort(key=lambda x:x["t"])
    (OUT/f"{key}.bubbles.jsonl").write_text("\n".join(json.dumps(x) for x in rows))
    print(f"  {key[:10]}: {len(rows)} bubbles (BUY {sum(1 for x in rows if x['side']=='BUY')} / SELL {sum(1 for x in rows if x['side']=='SELL')})")
tot=sum(agg[s][z] for s in agg for z in agg[s])
print(f"\n=== TOTAL bubbles únicas (causal first-appearance) = {tot} ===")
print(f"  BUY  s/m/L = {agg['BUY']['S']}/{agg['BUY']['M']}/{agg['BUY']['L']}  (total {sum(agg['BUY'].values())})")
print(f"  SELL s/m/L = {agg['SELL']['S']}/{agg['SELL']['M']}/{agg['SELL']['L']}  (total {sum(agg['SELL'].values())})")
print(f"\n=== AUDITORIA MAPPING (direção do bar-âncora) ===")
for s in ("BUY","SELL"):
    up,t=audit[s]; print(f"  {s}: up-bar% = {100*up/t:.1f}%  (n={t})")
print(f"  → esperado p/ mapping correto: BUY up% >> SELL up% (ordem BUY levanta, SELL derruba)")
if lag: print(f"  causalidade: known_at>=time em {len(lag)} bubbles, lag mediano {sorted(lag)[len(lag)//2]:.0f} bars (>=0 OK)")