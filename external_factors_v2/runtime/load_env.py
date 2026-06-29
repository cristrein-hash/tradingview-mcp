#!/usr/bin/env python3
"""Carrega external_factors_v2/.env em os.environ (sem dependência externa). NUNCA loga valores. Idempotente."""
import os
from pathlib import Path
def load_env():
    H=Path(__file__).parent.parent
    loaded={}
    # external_factors_v2/.env (local) + raiz do repo .env (onde o Cris pôs as keys)
    for f in [H/".env", H.parent/".env"]:
        if not f.exists(): continue
        for ln in f.read_text().splitlines():
            ln=ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln: continue
            k,_,v=ln.partition("="); k=k.strip(); v=v.strip().strip('"').strip("'")
            if k and v: os.environ.setdefault(k,v); loaded[k]=True
    return loaded
if __name__=="__main__":
    L=load_env(); print("keys carregadas:",sorted(L.keys()) or "(nenhuma — crie .env a partir de .env.example)")
