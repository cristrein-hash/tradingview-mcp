#!/usr/bin/env python3
"""VIGIA DA REAÇÃO FOMC (Cris 2026-07-28). Dorme até T-15min do release (release_ts EXATO do ff_calendar,
keyless), estabelece baseline do preço a T-5min, e na janela do evento (decisão 19:00 + Powell 19:30 Lisboa)
emite: o 1º movimento pós-release, marcos +5/+15/+30 min de cada fase, e qualquer excursão nova >=8 pts.
Fecha ~21:00 com resumo. Silencioso até lá (0 notificações). Fonte de preço = bar-store 5M (o mesmo do
trading). Read-only."""
import json, os, time, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
hm = lambda t=None: dt.datetime.fromtimestamp(t or time.time(), LX).strftime("%H:%M:%S")

# release exato do calendário (keyless)
cal = json.load(open(R + "external_factors_v2/snapshots/ff_calendar.json"))
REL = next((e.get("release_ts") for e in cal.get("events", []) if e.get("event") == "FOMC Rate Decision"), None)
if not REL:
    print("FOMC release_ts não encontrado no calendário — vigia aborta"); raise SystemExit(1)
POWELL = REL + 1800                      # conferência ~30 min depois
END = REL + 7200                         # fecha 2h depois da decisão

def px():
    try:
        p = R + "my-strategy/core/bar_store/store/bars_5m.jsonl"
        with open(p, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 3000))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines() if l.strip() and l[0] == "{"]
        return rows[-1]["c"] if rows else None
    except Exception:
        return None

# dorme até T-15min (sem output = sem notificações)
while time.time() < REL - 900:
    time.sleep(60)

print(f"FOMC T-15min ({hm()}): vigia da reação ATIVO. Decisão {hm(REL)} · Powell {hm(POWELL)} Lisboa. Preço {px()}")
base = None
marks = {REL + 300: "decisão +5min", REL + 900: "decisão +15min", POWELL: "POWELL começa",
         POWELL + 900: "Powell +15min", POWELL + 1800: "Powell +30min"}
done = set()
max_up = 0.0; max_dn = 0.0; last_note = 0.0
while time.time() < END:
    try:
        now = time.time()
        p = px()
        if p is None:
            time.sleep(30); continue
        if base is None and now >= REL - 300:
            base = p
            print(f"baseline T-5min: {base}")
        if base is not None and now >= REL:
            d = p - base
            max_up = max(max_up, d); max_dn = min(max_dn, d)
            # 1º movimento pós-release
            if "first" not in done and now >= REL + 60:
                done.add("first")
                print(f"FOMC REAÇÃO 1º MIN ({hm()}): {p} ({d:+.1f} pts vs baseline {base})")
            # marcos
            for mt, lbl in marks.items():
                if mt not in done and now >= mt:
                    done.add(mt)
                    print(f"FOMC {lbl} ({hm()}): {p} ({d:+.1f} pts) · extremos até agora +{max_up:.1f}/{max_dn:.1f}")
            # excursão nova forte (>=8 pts além do último aviso)
            if abs(d) >= 8 and abs(d) >= last_note + 8:
                last_note = abs(d)
                print(f"FOMC MOVIMENTO FORTE ({hm()}): {p} ({d:+.1f} pts) — {'ALTA' if d > 0 else 'BAIXA'}")
    except Exception as e:
        print(f"vigia-fomc erro transitório: {type(e).__name__}")
    time.sleep(30)
p = px()
print(f"FOMC RESUMO ({hm()}): fecho da janela {p} ({(p - base):+.1f} pts vs pré-FOMC) · extremos +{max_up:.1f}/{max_dn:.1f}. Vigia encerra; reader/E2 continuam de serviço.")
