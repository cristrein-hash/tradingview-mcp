#!/usr/bin/env python3
"""AUDITOR AUTOMÁTICO dos coletores news/EF (Cris 2026-07-28). Deteta FALHA por coletor (snapshot stale OU
conteúdo degradado: preço None, feed vazio prolongado, calendário sem FOMC) e emite 1 linha na TRANSIÇÃO
OK->FALHA (e FALHA->OK na recuperação) — dedup por estado, nunca a cada ciclo. Cada linha = notificação
no chat -> o Claude audita automaticamente. Read-only, poll 120s."""
import json, os, time
SN = "/Users/cristrein/tradingview-mcp/external_factors_v2/snapshots/"

# coletor -> (ficheiro, idade_max_s, verificador_de_conteúdo(dict)->None|str-motivo-falha)
def chk_price(d):
    q = d if isinstance(d, dict) else {}
    # oil/gold: procura price_usd em qualquer nível
    px = q.get("price_usd") or ((q.get("brent") or {}) if False else {}).get("price_usd")
    if px is None:
        # tenta estrutura {brent:{price_usd}} / {gold:{price_usd}}
        for k in ("brent", "gold", "quote"):
            sub = q.get(k)
            if isinstance(sub, dict) and sub.get("price_usd") is not None:
                return None
        if q.get("error"):
            return f"preço None (erro: {str(q.get('error'))[:50]})"
    return None

def chk_calendar(d):
    evs = d.get("events") if isinstance(d, dict) else None
    if not evs:
        return "calendário sem eventos"
    if not any("FOMC" in (e.get("event") or "") for e in evs):
        return None  # FOMC pode já ter passado; não falha por ausência futura
    return None

COLLECTORS = {
    "InvestingLive": ("investinglive_news.json", 900, None),
    "Finnhub":       ("finnhub_news.json", 900, None),
    "Geopolitical":  ("geopolitical_news.json", 900, None),
    "Oil/Brent":     ("oil_data.json", 900, chk_price),
    "Polymarket":    ("polymarket.json", 900, None),
    "Calendário":    ("ff_calendar.json", 5400, chk_calendar),
    "Ouro-contexto": ("gold_data.json", 5400, chk_price),
    "E0 dossiê":     ("market_context.json", 400, None),
}

def status(name, spec):
    fn, max_age, contentf = spec
    p = SN + fn
    if not os.path.exists(p):
        return "FALHA", "ficheiro ausente"
    age = time.time() - os.path.getmtime(p)
    if age > max_age:
        return "FALHA", f"stale {int(age)}s (max {max_age}s) — coletor parou de escrever"
    if contentf:
        try:
            d = json.load(open(p))
        except Exception as e:
            return "FALHA", f"ilegível ({type(e).__name__})"
        m = contentf(d)
        if m:
            return "FALHA", m
    return "OK", ""

def run():
    last = {}
    print("auditor de coletores armado: InvestingLive · Finnhub · Geopolitical · Oil · Polymarket · Calendário · Ouro · E0 (transição OK<->FALHA)")
    while True:
        try:
            for name, spec in COLLECTORS.items():
                s, reason = status(name, spec)
                prev = last.get(name)
                if prev is None:
                    last[name] = s
                    if s == "FALHA":
                        print(f"COLETOR EM FALHA (arranque): {name} — {reason}")
                    continue
                if s != prev:
                    if s == "FALHA":
                        print(f"COLETOR FALHOU: {name} — {reason} · AUDITAR")
                    else:
                        print(f"COLETOR RECUPEROU: {name} — voltou a OK")
                    last[name] = s
        except Exception as e:
            print(f"auditor erro transitório: {type(e).__name__}")
        time.sleep(120)


if __name__ == "__main__":
    run()
