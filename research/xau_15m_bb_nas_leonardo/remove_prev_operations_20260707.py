#!/usr/bin/env python3
"""Remoção SELETIVA das operações anteriores (2026-07-07, autorizado Cris: "apaga operações anteriores
mantendo restante dos meus draws"). Remove APENAS long_position + text (labels de trade #C/#S).
PRESERVA circle + text_note (VELA DE FUNDO/ENTRY, PLT/DM = draws do Cris). NÃO usa draw_clear.
Uso: python3 remove_prev_operations_20260707.py [--dry]"""
import sys,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
REMOVE={"long_position","short_position","text"}; KEEP={"circle","text_note"}
def main():
    dry="--dry" in sys.argv
    c=MCPClient(); c.start()
    try:
        dl=c.call_tool("draw_list"); shapes=dl.get("shapes",[])
        from collections import Counter
        before=dict(Counter(s.get("name") for s in shapes))
        to_rm=[s for s in shapes if s.get("name") in REMOVE]
        keep=[s for s in shapes if s.get("name") in KEEP]
        print(json.dumps({"before":before,"a_remover":len(to_rm),"a_preservar":len(keep)}))
        if dry: return 0
        removed=0; fails=0
        for s in to_rm:
            r=c.call_tool("draw_remove_one",{"entity_id":s.get("id")})
            if r.get("success"): removed+=1
            else: fails+=1
        dl2=c.call_tool("draw_list")
        after=dict(Counter(s.get("name") for s in dl2.get("shapes",[])))
        print(json.dumps({"removed":removed,"fails":fails,"after":after,"total_after":dl2.get("count")}))
    finally:
        try: c.stop()
        except Exception: pass
if __name__=="__main__": sys.exit(main() or 0)
