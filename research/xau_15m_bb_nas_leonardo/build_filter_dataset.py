#!/usr/bin/env python3
"""Dataset enriquecido para o ENGINE DE FILTRO LONG (Cris 2026-06-27).
Base = candidatos A2 5ATR (h1_pos>=0.65 & disp4_atr>=0.78), PRE-DEDUP, cada um com cj/exi/R/win
calculados na regua APROVADA (SL=A flush-0.1ATR, let-run, RCAP20). exi independe de outros trades
=> harness aplica keep-predicate e RE-DEDUPA (uma-posicao) corretamente.
Features existentes copiadas de dataset_5atr.jsonl + NOVAS features CAUSAIS:
  Ponto do Cris (regiao anterior a entrada = perna do fundo-ancora ate cj, e janela 24b antes de cj):
    buy_bub_w/sell_bub_w (size-weighted S1/M2/L3, known_at<=tc), buy_bub_L (contagem LARGE BUY),
    nas_short_n/nas_long_n (t<=tc, first-appearance causal), em ambas janelas (_leg e _w24).
  Sugestao (A) esticado/late:  dist_ema_atr (entry-ema21)/atr, leg_ext_atr (entry-low)/atr,
    room_above_atr (dist a SUPPLY acima, born_t<=tc).
RAW-causal. Mapping bubbles confirmado: BUY=plot_0/2/4, SELL=plot_6/8/10."""
import json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
        for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480; SZ={"S":1,"M":2,"L":3}
# features base por (block, low_t)
F={}
for l in (HERE/"dataset_5atr.jsonl").read_text().splitlines():
    r=json.loads(l); F[(r["block"],r["low_t"])]=r
# bubbles por bloco-key (casa pelo prefixo de data do bloco)
BUB={}
for bf in sorted((HERE/"bubbles").glob("*.bubbles.jsonl")):
    key=bf.name[:10]  # YYYY-MM-DD inicio
    BUB[key]=sorted([json.loads(l) for l in bf.read_text().splitlines() if l], key=lambda x:x["t"])

def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),exi
def A2(r): return r.get("h1_pos") is not None and r["h1_pos"]>=0.65 and r["disp4_atr"]>=0.78

# copia este conjunto de features existentes para o harness
KEEP_FEATS=["h1_pos","disp4_atr","dist_supply_atr","dist_demand_atr","in_demand","demand_fresh",
            "rsi","rsi_low","h1_eff","h4_eff","h1_dist","h4_pos","path_eff","macro_retr","macro_drop_atr",
            "macro_bull","macro_bear","atr_regime","vol_climax","vol_low_vs_med","vpnode_dist_atr",
            "bars_to_base","bars_since_lowest","regime_age_h","killzone","is_ny_overlap","is_deadzone",
            "buy_sell_ratio4","absorption","smc_bos","flow_accel"]

def bub_feats(bub, t0, t1, tc):
    """size-weighted BUY/SELL + LARGE BUY count, known_at<=tc, t em [t0,t1]."""
    a=bisect.bisect_left([x["t"] for x in bub], t0)
    bw=sw=bl=0
    for x in bub[a:]:
        if x["t"]>t1: break
        if (x.get("known_at") or x["t"])>tc: continue
        if x["side"]=="BUY":
            bw+=SZ[x["size"]];  bl+= (1 if x["size"]=="L" else 0)
        else: sw+=SZ[x["size"]]
    return bw,sw,bl

rows=[]
for k,pr in PRIM.items():
    s=pr["series"]; tmap={b["t"]:idx for idx,b in enumerate(s)}
    bkey=k[:10]; bub=BUB.get(bkey,[])
    nas=sorted(pr["nas_events"], key=lambda x:x["t"]); nas_t=[x["t"] for x in nas]
    zones=pr["zones"]
    for (blk,lt),r in F.items():
        if blk!=bkey: continue
        if not A2(r): continue
        i=tmap.get(lt); cj=r["cj"]
        if i is None or cj+2>=len(s) or not s[i]["atr"]: continue
        atr=s[i]["atr"]
        flush=min(x["l"] for x in s[i:cj+1]); entry=s[cj]["c"]; sl=flush-0.1*atr
        R,exi=letrun(s,cj,entry,sl,atr)
        if R is None: continue
        tc=s[cj]["t"]; t_leg0=s[i]["t"]; t_w24=s[max(0,cj-24)]["t"]
        # bubbles regiao
        bw_l,sw_l,bl_l=bub_feats(bub,t_leg0,tc,tc)
        bw_w,sw_w,bl_w=bub_feats(bub,t_w24,tc,tc)
        # NAS regiao (first-appearance causal t<=tc)
        def nas_cnt(t0):
            a=bisect.bisect_left(nas_t,t0); b=bisect.bisect_right(nas_t,tc)
            sh=sum(1 for x in nas[a:b] if x["dir"]=="SHORT"); lo=sum(1 for x in nas[a:b] if x["dir"]=="LONG")
            return sh,lo
        nsh_l,nlo_l=nas_cnt(t_leg0); nsh_w,nlo_w=nas_cnt(t_w24)
        # esticado / late
        dist_ema_atr=(entry-s[cj]["ema21"])/atr if s[cj].get("ema21") else 0.0
        leg_ext_atr=(entry-s[i]["l"])/atr
        # room above: SUPPLY acima de entry, born_t<=tc
        room=99.0
        for z in zones:
            if z["text"]=="SUPPLY" and z.get("born_t",0)<=tc and z["low"]>entry:
                d=(z["low"]-entry)/atr
                if d<room: room=d
        out={"block":blk,"low_t":lt,"i":i,"cj":cj,"exi":exi,"t":tc,
             "entry":round(entry,2),"sl":round(sl,2),"R":round(R,3),"win":int(R>0),
             "yr":dt.datetime.utcfromtimestamp(tc).year,
             "buy_bub_w_leg":bw_l,"sell_bub_w_leg":sw_l,"buy_bub_L_leg":bl_l,
             "buy_bub_w_w24":bw_w,"sell_bub_w_w24":sw_w,"buy_bub_L_w24":bl_w,
             "nas_short_leg":nsh_l,"nas_long_leg":nlo_l,"nas_short_w24":nsh_w,"nas_long_w24":nlo_w,
             "dist_ema_atr":round(dist_ema_atr,3),"leg_ext_atr":round(leg_ext_atr,3),
             "room_above_atr":round(room,3)}
        for kf in KEEP_FEATS: out[kf]=r.get(kf)
        rows.append(out)
rows.sort(key=lambda x:x["t"])
with open(HERE/"filter_dataset.jsonl","w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
# resumo base (dedup uma-posicao = keep all)
def dedup_metrics(cands):
    cands=sorted(cands,key=lambda x:x["cj"] if False else x["t"])
    # dedup por cj/exi dentro de cada bloco
    byblk={}
    for c in cands: byblk.setdefault(c["block"],[]).append(c)
    taken=[]
    for blk,cs in byblk.items():
        cs.sort(key=lambda x:x["cj"]); busy=-10**9
        for c in cs:
            if c["cj"]<=busy: continue
            busy=c["exi"]; taken.append(c)
    taken.sort(key=lambda x:x["t"])
    n=len(taken); w=sum(c["win"] for c in taken); sm=sum(c["R"] for c in taken)
    eq=pk=dd=0; stk=mstk=0
    for c in taken:
        eq+=c["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if c["R"]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    return n,w,sm,dd,mstk,taken
n,w,sm,dd,stk,_=dedup_metrics(rows)
print(f"filter_dataset.jsonl: {len(rows)} candidatos A2 pre-dedup.")
print(f"BASE (keep all, dedup uma-posicao, SL=A let-run): N={n} WR={100*w/n:.1f}% sumR={sm:+.1f} DD={dd:.1f}R streak={stk}")
