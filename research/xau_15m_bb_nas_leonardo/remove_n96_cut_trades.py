#!/usr/bin/env python3
"""Remocao CIRURGICA (opcao B, autorizada Cris 2026-07-08) dos 13 trades intra-BEAR cortados do chart 15M,
preservando os 83 validos E quaisquer desenhos do Cris. Match = desenhos cujo tempo-ancora esta nos 13 entry_t
cortados (posicao long_position + label #num partilham esse tempo). GUARDA: aborta se um tempo cortado colidir
com um trade valido. dry-run por default (lista, NAO remove); --apply para remover. Requer pause flag.
plotting-canon: NAO draw_clear, NAO screenshot, verificacao via draw_list. Conecta via MCPClient (CDP)."""
import sys, json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
sys.path.insert(0,str(REPO/"research/xau_15m_bb_nas_leonardo"))
from draw_xau_4h_trades import MCPClient
from agent_ctx_kit import ENTRIES
PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF="PEPPERSTONE:XAUUSD","15"
CUT13={24,25,55,56,57,58,59,66,67,79,83,84,85}
CUT_T={e["n"]:int(e["t"]) for e in ENTRIES if e["n"] in CUT13}
VALID_T={int(e["t"]) for e in ENTRIES if e["n"] not in CUT13}
assert len(CUT_T)==13, f"esperado 13 cortados, {len(CUT_T)}"
# GUARDA: nenhum tempo cortado pode coincidir com trade valido (senao match-por-tempo apagaria valido)
collide=set(CUT_T.values()) & VALID_T
assert not collide, f"ABORT: tempos cortados colidem com validos: {collide}"
CUT_TIMES=set(CUT_T.values())
def norm_t(x):
    try: x=float(x)
    except: return None
    return x/1000.0 if x>1e12 else x

def main():
    apply="--apply" in sys.argv
    if not PAUSE.exists(): print(json.dumps({"ERRO":"pause flag ausente"})); return 1
    c=MCPClient(); c.start(); rep={"mode":"APPLY" if apply else "DRY_RUN"}
    try:
        st=c.call_tool("chart_get_state"); sym,res=st.get("symbol"),str(st.get("resolution"))
        rep["chart"]={"symbol":sym,"tf":res}
        if not (str(sym).endswith("XAUUSD") and res==TF):
            print(json.dumps({"HARD_STOP":f"chart nao XAUUSD/15: {sym}/{res}","fix":"confirmar symbol/TF"})); return 1
        dl=c.call_tool("draw_list"); shapes=dl.get("shapes",[]) if isinstance(dl,dict) else []
        rep["draw_list_count_before"]=dl.get("count") if isinstance(dl,dict) else None
        if "--probe" in sys.argv:
            probe=[]; nt=0; nl=0
            for s in shapes:
                nm=s.get("name")
                if nm=="text" and nt<3:
                    probe.append({"name":nm,"raw":c.call_tool("draw_get_properties",{"entity_id":s.get("id")})}); nt+=1
                elif nm=="long_position" and nl<1:
                    probe.append({"name":nm,"raw":c.call_tool("draw_get_properties",{"entity_id":s.get("id")})}); nl+=1
                if nt>=3 and nl>=1: break
            print(json.dumps(probe,indent=2,ensure_ascii=False)[:4000]); return 0
        import re
        def props_retry(eid, tries=4):
            for _ in range(tries):
                pr=c.call_tool("draw_get_properties",{"entity_id":eid})
                if isinstance(pr,dict) and (pr.get("points") or pr.get("properties")): return pr
            return pr if isinstance(pr,dict) else {}
        matches=[]  # {id, name, time, matched_num, text}
        for s in shapes:
            eid=s.get("id"); nm=s.get("name")
            if not eid or nm not in ("long_position","text"): continue   # ignora circle/text_note/svp/short (do Cris)
            pr=props_retry(eid)
            pts=pr.get("points"); props=pr.get("properties") if isinstance(pr,dict) else None
            text=props.get("text") if isinstance(props,dict) else None
            t0=None
            if isinstance(pts,list) and pts and isinstance(pts[0],dict): t0=norm_t(pts[0].get("time"))
            num=None
            if nm=="text" and text:
                m=re.match(r"#(\d+)", str(text));
                if m and int(m.group(1)) in CUT13: num=int(m.group(1))
            elif nm=="long_position" and t0 is not None:
                num=next((n for n,ct in CUT_T.items() if abs(t0-ct)<450), None)
            if num is not None:
                matches.append({"id":eid,"name":nm,"time":int(t0) if t0 else None,"matched_num":num,"text":text})
        rep["matched_drawings"]=len(matches)
        # nums cobertos + verificacao (esperado: 13 nums, 2 desenhos cada = 26)
        nums_hit=sorted({m["matched_num"] for m in matches})
        rep["nums_matched"]=nums_hit
        rep["missing_nums"]=sorted(CUT13-set(nums_hit))
        rep["texts_sample"]=[m["text"] for m in matches if m["text"]][:20]
        # DIAGNOSTICO: por-num quantos desenhos + tipo; e cobertura de pontos no chart todo
        from collections import Counter
        rep["per_num_count"]={n:sum(1 for m in matches if m["matched_num"]==n) for n in nums_hit}
        rep["matched_by_name"]=dict(Counter(m["name"] for m in matches))
        rep["all_shapes_by_name"]=dict(Counter(s.get("name") for s in shapes))
        rep["matches_detail"]=[{"num":m["matched_num"],"name":m["name"],"text":m["text"],"t":m["time"]} for m in matches]
        # SEGURANCA: se algum match tem text que NAO e um #cut, avisar
        bad=[m for m in matches if m["text"] and m["text"].lstrip("#").isdigit() and int(m["text"].lstrip("#")) not in CUT13]
        rep["texts_fora_cut13"]=[m["text"] for m in bad]
        complete = (len(matches)==26 and set(rep["per_num_count"].values())=={2} and len(nums_hit)==13)
        rep["complete_2each"]=complete
        if apply and bad:
            rep["ABORT_APPLY"]="matches contem texto fora dos #cut13"
        elif apply and not complete:
            rep["ABORT_APPLY"]=f"match incompleto (esperado 26=13x2, obtido {len(matches)}) — nao removi nada; re-correr dry-run"
        elif apply and complete:
            removed=0; fails=[]
            for m in matches:
                r=c.call_tool("draw_remove_one",{"entity_id":m["id"]})
                if isinstance(r,dict) and r.get("removed"): removed+=1
                else: fails.append({"id":m["id"],"r":str(r)[:100]})
            dl2=c.call_tool("draw_list"); rep["draw_list_count_after"]=dl2.get("count") if isinstance(dl2,dict) else None
            rep["removed"]=removed; rep["remove_fails"]=fails
        elif apply and bad:
            rep["ABORT_APPLY"]="matches contem texto fora dos #cut13 — nao removi nada"
    finally:
        try: c.stop()
        except Exception: pass
    print(json.dumps(rep,indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__":
    sys.exit(main())
