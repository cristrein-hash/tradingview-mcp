#!/usr/bin/env python3
"""POC read-only (gap #1): a lógica de ZONAS EMPILHADAS apanharia a venda no topo de hoje que a lógica
atual (só a zona mais próxima) perdeu? Replica o gatilho zone_reject do E1 sobre as barras 15M de hoje,
contra o STACK de supply real do store. CAVEAT declarado: uso o snapshot ATUAL das zonas (não tenho as
zonas as-of madrugada); as zonas de supply do topo formam-se do próprio movimento, por isso a rejeição
causalmente limpa é o RE-TESTE posterior. Isto demonstra o MECANISMO, não é o replay de produção (esse,
com zonas as-of, faz parte do plano). Nada é alterado no live."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
t0 = dt.datetime(2026, 7, 26, 22, 0, tzinfo=dt.timezone.utc).timestamp()
today = [b for b in bars if b["t"] >= t0]

# STACK de supply real (store, dedup) — as caixas laranja do print do Cris
SUPPLY = sorted({(round(4089.8,1),round(4090.4,1)),(4096.9,4104.1),(4100.8,4112.6),(4108.7,4116.0)},
                key=lambda z: z[0])  # (low, high) ordenado por low
POT = (4089.8, 4090.4)   # Power of Three — a ÚNICA que a lógica atual via como 'nearest'

def pos_proxy(i):
    """pos-freshness aproximado: onde está o close na janela de 20 barras (short precisa topo, pos>=0.5)."""
    w = today[max(0, i-20):i+1]
    lo = min(x["l"] for x in w); hi = max(x["h"] for x in w)
    return (today[i]["c"] - lo) / (hi - lo) if hi > lo else 0.5

def nearest_above(price):
    cand = [z for z in SUPPLY if z[0] > price]
    return min(cand, key=lambda z: z[0]) if cand else None

print("=== REPLAY zone_reject SHORT sobre barras 15M de hoje ===")
print("(rejeição = fecho anterior >= zona.low E fecho atual < zona.low, i.e. voltou a fechar por baixo da zona)\n")
sing = []; stak = []
for i in range(1, len(today)):
    pc = today[i-1]["c"]; c = today[i]["c"]; bt = today[i]["t"]
    pos = pos_proxy(i)
    # LÓGICA ATUAL: só a zona mais próxima acima do preço anterior
    za = nearest_above(pc)
    if za and pc >= za[0] and c < za[0] and pos >= 0.5:
        sing.append((bt, c, za))
    # LÓGICA EMPILHADA: qualquer zona do stack rejeitada
    for z in reversed(SUPPLY):   # de cima para baixo
        if pc >= z[0] and c < z[0] and pos >= 0.5:
            stak.append((bt, c, z)); break

def show(evts, lbl):
    print(f"--- {lbl}: {len(evts)} rejeições-short ---")
    for bt, c, z in evts:
        print(f"   {hm(bt)}  fecho {c:.2f}  rejeitou supply {z[0]}-{z[1]}")
    print()
show(sing, "LÓGICA ATUAL (só zona mais próxima)")
show(stak, "LÓGICA EMPILHADA (proposta)")

# o que a empilhada apanha que a atual não
extra = [e for e in stak if e[:2] not in [(x[0], x[1]) for x in sing]]
print(f"=== A EMPILHADA GERA {len(extra)} venda(s) que a ATUAL perdeu ===")
for bt, c, z in extra:
    print(f"   ✅ {hm(bt)}  short @ {c:.2f}  (rejeição da supply {z[0]}-{z[1]})")
print()
# o topo real e onde a venda cairia
hi = max(today, key=lambda x: x["h"])
print(f"topo real de hoje: {hi['h']} @ {hm(hi['t'])} | preço agora: {today[-1]['c']}")
