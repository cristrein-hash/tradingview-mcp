#!/usr/bin/env python3
"""Reconstrói os 34 trades APROVADOS da L1 EMA21 do l1_discriminator_filter_v2.csv aplicando os filtros aprovados
(anti-extensão v1 + NAS shift1). Confirma n/WR/sumR vs aprovado (34, WR53%, +41R). Salva os 34 (ts,R) p/ aplicar
loser-cuts L2 depois. Verified 2026-06-25."""
import csv, json
from pathlib import Path
CSV = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/reports/l1_discriminator_filter_v2.csv")
rows = list(csv.DictReader(open(CSV)))
def fn(x):
    try: return float(x)
    except Exception: return None
print(f"candidatos no csv = {len(rows)}")
# filtros aprovados: ret5<=0.0142 & ext_ema<=2.95 & zone_w>=0.6 & dist_zone<=1.81 & nas_shift1>=1.31
appr = []
for r in rows:
    ret5, ext, zw, dz, nas = fn(r["ret5"]), fn(r["ext_ema"]), fn(r["zone_w"]), fn(r["dist_zone"]), fn(r["nas_shift1"])
    if None in (ret5, ext, zw, dz, nas): continue
    if ret5 <= 0.0142 and ext <= 2.95 and zw >= 0.6 and dz <= 1.81 and nas >= 1.31:
        appr.append(r)
R = [fn(r["R"]) for r in appr]; w = sum(1 for x in R if x > 0); s = sum(R)
print(f"34 aprovados? → n={len(appr)} | WR={100*w/len(appr):.0f}% | sumR={s:+.1f} | avgR={s/len(appr):+.2f}")
print(f"   (esperado: 34, WR53%, +41R) — match={'SIM' if len(appr)==34 else 'NÃO ('+str(len(appr))+')'}")
out = [{"ts": r["ts"], "R": fn(r["R"]), "mfe": fn(r["mfe"]), "res": r["res"], "win": fn(r["R"]) > 0,
        "rsi_vs_ma": fn(r["rsi_vs_ma"]), "ext_ema": fn(r["ext_ema"]), "zone_w": fn(r["zone_w"])} for r in appr]
json.dump(out, open(Path(__file__).parent / "l1_approved34.json", "w"), indent=1)
print(f"\nsalvo -> l1_approved34.json ({len(out)}). winners={w} losers={len(out)-w} | runners(mfe>=5)={sum(1 for r in out if r['mfe']>=5)}")
