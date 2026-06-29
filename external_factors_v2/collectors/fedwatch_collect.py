#!/usr/bin/env python3
"""COLETOR FED PATH (proxy CME FedWatch, keyless).
⚠️ HONESTO: a CME FedWatch oficial deriva de fed funds futures (ZQ), que são PAYWALLED (FMP premium, CME WS bloqueado,
Yahoo rate-limit). A curva de T-bills (keyless) tem BASIS vs fed funds (bills acima do SOFR -> falso "hike" no nível).
SOLUÇÃO defensável: a SLOPE da curva curta (6mo−1mo) cancela o basis ~constante -> sinal DIRECIONAL de path da Fed
(cortes vs altas precificados). NÃO é probabilidade por reunião (isso exige ZQ). Confiança média, contexto Tier-2.
Fontes FRED keyless: DFEDTARU/L (target), SOFR (overnight), DGS1MO/3MO/6MO/1 (curva). Saída: snapshots/fed_path.json."""
import json,subprocess,time,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
def fred_last(fid):
    for _ in range(3):
        txt=subprocess.run(["curl","-sS","--http1.1","--max-time","45",
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fid}&cosd=2026-04-01"],capture_output=True,text=True).stdout
        if txt and "," in txt and "<" not in txt[:200]:
            for ln in reversed(txt.splitlines()[1:]):
                p=ln.split(",")
                if len(p)>=2 and p[1] not in("",".","NA"):
                    try: return (p[0],float(p[1]))
                    except: pass
            return None
        time.sleep(4.0)
    return None
def next_fomc():
    ff=SNAP/"ff_calendar.json"
    if ff.exists():
        try:
            for e in sorted(json.loads(ff.read_text()).get("events",[]),key=lambda x:x["release_ts"]):
                if "FOMC" in e.get("event","") and e["release_ts"]>=NOWT: return e["date"]
        except Exception: pass
    return None
def main():
    g={}
    for k,fid in [("tgt_upper","DFEDTARU"),("tgt_lower","DFEDTARL"),("sofr","SOFR"),
                  ("y1mo","DGS1MO"),("y3mo","DGS3MO"),("y6mo","DGS6MO"),("y1y","DGS1")]:
        time.sleep(1.5); v=fred_last(fid); g[k]=v[1] if v else None; g[k+"_asof"]=v[0] if v else None
    mid=round((g["tgt_upper"]+g["tgt_lower"])/2,3) if g.get("tgt_upper") and g.get("tgt_lower") else None
    # SLOPE basis-robust (cancela bill-basis ~constante): 6mo - 1mo
    slope_6m_1m=round(g["y6mo"]-g["y1mo"],3) if g.get("y6mo") and g.get("y1mo") else None
    slope_1y_3m=round(g["y1y"]-g["y3mo"],3) if g.get("y1y") and g.get("y3mo") else None
    # bias: curva curta caindo/invertida = cortes precificados (gold supportive); subindo = sem cortes/altas
    bias="unknown"; gold_read="neutral"
    if slope_6m_1m is not None:
        if slope_6m_1m<=-0.10: bias="easing_priced (cortes)"; gold_read="supportive"
        elif slope_6m_1m>=0.10: bias="tightening/no-cut (altas ou sem corte)"; gold_read="headwind"
        else: bias="hold (estável)"; gold_read="neutral"
    state={"_meta":{"built_ts":NOWT,"method":"proxy_treasury_curve_slope (basis-robust)","confidence":"media",
            "caveat":"FedWatch oficial=fed funds futures ZQ (paywalled); aqui SLOPE da curva curta keyless cancela basis; NÃO é prob. por reunião"},
           "target_midpoint":mid,"target_range":[g.get("tgt_lower"),g.get("tgt_upper")],"sofr_overnight":g.get("sofr"),
           "short_curve":{"1mo":g.get("y1mo"),"3mo":g.get("y3mo"),"6mo":g.get("y6mo"),"1y":g.get("y1y")},
           "slope_6m_1m_bp":round(slope_6m_1m*100,1) if slope_6m_1m is not None else None,
           "slope_1y_3m_bp":round(slope_1y_3m*100,1) if slope_1y_3m is not None else None,
           "rate_path_bias":bias,"gold_read":gold_read,"next_fomc":next_fomc(),"asof":g.get("sofr_asof")}
    (SNAP/"fed_path.json").write_text(json.dumps(state,indent=1,ensure_ascii=False))
    print("FED PATH (proxy CME FedWatch, keyless):")
    print(f"  target midpoint={mid} | SOFR overnight={g.get('sofr')} | next FOMC={state['next_fomc']}")
    print(f"  curva curta: 1mo={g.get('y1mo')} 3mo={g.get('y3mo')} 6mo={g.get('y6mo')} 1y={g.get('y1y')}")
    print(f"  slope 6m-1m={state['slope_6m_1m_bp']}bp -> bias={bias} (gold {gold_read})")
    print(f"  ⚠️ direcional (basis-robust); prob. por reunião exigiria fed funds futures ZQ (paywalled)")
    print(f"-> {SNAP/'fed_path.json'}")
if __name__=="__main__": main()
