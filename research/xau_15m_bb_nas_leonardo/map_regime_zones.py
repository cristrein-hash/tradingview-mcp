#!/usr/bin/env python3
"""Mapa das ZONAS DE REGIME marcadas pelo Cris no chart 15M (lidas via MCP draw_get_properties, 2026-06-28).
Cor de fundo -> tipo: laranja(255,152,0)=RANGE · verde(56/76,142/175,...)=BULL · vermelho(178,40,51)=BEAR.
Salva regime_zones_cris.json (ground-truth p/ testar detector causal). Sem lookahead aqui: é só o rótulo do Cris."""
import json,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
Z=[  # (id, type, t_start, t_end) — pontos do retângulo (MCP)
 ("giXIT3","RANGE",1754009100,1756345500),
 ("CVdtrP","BULL", 1756351800,1761029100),
 ("x4sCuR","BEAR", 1761024600,1761769800),
 ("pgDUsR","RANGE",1761735600,1762743600),
 ("Jft0QZ","BULL", 1762731000,1769701500),
 ("eebJNc","BEAR", 1769730300,1782690300),
]
out=[]
for zid,typ,a,b in Z:
    a,b=min(a,b),max(a,b)
    out.append({"id":zid,"type":typ,"t_start":a,"t_end":b,
                "start":dt.datetime.utcfromtimestamp(a).strftime("%Y-%m-%d %H:%M"),
                "end":dt.datetime.utcfromtimestamp(b).strftime("%Y-%m-%d %H:%M"),
                "dias":round((b-a)/86400,1)})
out.sort(key=lambda x:x["t_start"])
(HERE/"regime_zones_cris.json").write_text(json.dumps(out,indent=1))
print(f"{'#':>2} {'tipo':<6} {'início':<17} {'fim':<17} {'dias':>5}")
for i,z in enumerate(out,1): print(f"{i:>2} {z['type']:<6} {z['start']:<17} {z['end']:<17} {z['dias']:>5}")
print(f"\ncobertura: {out[0]['start']} -> {out[-1]['end']}  (RAW 15M vai até ~2026-05-25)")
