#!/usr/bin/env python3
"""MAPA DO TRADER — fonte única (Cris aprovou 2026-08-04, desenho pós-falha 04/08: o E2 surfou um LONG
para dentro da zona de venda pré-declarada do Cris sem aviso, e ninguém leu a vela de absorção das 09:00).

O mapa é o canal de 1ª classe onde o Cris declara zonas/tese ANTES do preço lá chegar. Consumido por:
  - e2_quality.render_composite (secção '# MAPA DO TRADER' em toda leitura)
  - e2_quality.notify_surfaced (prefixo de CONFLITO obrigatório em sinais contra-tese na zona)
  - vela_no_nivel.py (modo vela-a-vela nas zonas 'critica')
Ficheiro: alert-bridge/trader_map.json. SEM mapa = comportamento byte-idêntico ao anterior (fail-open).
Atualização v1: Cris pede em chat/Telegram-bridge -> Claude edita o JSON (validar com --validate).
py3.9, sem dependências."""
import json, datetime as dt
from pathlib import Path

BASE = Path(__file__).resolve().parent
MAP_F = BASE / "trader_map.json"


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _parse_ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def load_map(now=None):
    """Carrega o mapa; remove zonas expiradas/invalidas. None se não há nada ativo (fail-open)."""
    now = now or _now()
    try:
        raw = json.loads(MAP_F.read_text())
    except Exception:
        return None
    if raw.get("version") != 1:
        return None
    zones = []
    for z in raw.get("zones", []):
        try:
            lo, hi = float(z["low"]), float(z["high"])
        except Exception:
            continue
        if z.get("tese") not in ("SHORT", "LONG", "NEUTRA"):
            continue
        exp = _parse_ts(z.get("validade"))
        if exp is not None and exp < now:
            continue
        zones.append({"id": z.get("id") or f"z_{lo}_{hi}", "low": lo, "high": hi,
                      "tese": z["tese"], "nota": str(z.get("nota") or "")[:160],
                      "criticidade": z.get("criticidade") or "normal",
                      "fast_5m": bool(z.get("fast_5m")),   # preservar flag do fast-lane 5M (era descartada)
                      "validade": z.get("validade")})
    tg = raw.get("tese_geral") or None
    if tg:
        exp = _parse_ts(tg.get("validade"))
        if exp is not None and exp < now:
            tg = None
    if not zones and not tg:
        return None
    return {"zones": zones, "tese_geral": tg, "updated_ts": raw.get("updated_ts")}


def zones_near(price, atr, tmap=None, mult=1.0):
    """Zonas cuja banda [low−mult·atr, high+mult·atr] contém o preço."""
    tmap = tmap if tmap is not None else load_map()
    if not tmap or price is None:
        return []
    a = float(atr or 6.0) * mult
    return [z for z in tmap["zones"] if z["low"] - a <= float(price) <= z["high"] + a]


def conflict(cand, tmap=None, atr=None):
    """Zona declarada cuja tese CONTRADIZ a direção do candidato, com entry a <=1·ATR da zona. None se não."""
    d = (cand or {}).get("direction")
    entry = (cand or {}).get("entry")
    if d not in ("LONG", "SHORT") or entry is None:
        return None
    for z in zones_near(entry, atr, tmap, mult=1.0):
        if z["tese"] in ("LONG", "SHORT") and z["tese"] != d:
            return z
    return None


def _fmt_validade(v):
    t = _parse_ts(v)
    return t.strftime("%d/%m") if t else "sem prazo"


def render_section(tmap):
    """Secção '# MAPA DO TRADER' + regra de peso (atenção-não-obediência) — vai no briefing do reader."""
    L = ["\n# MAPA DO TRADER (leitura pré-declarada pelo Cris — voz de 1ª classe, NÃO ordem)"]
    for z in tmap["zones"]:
        crit = "CRÍTICA " if z["criticidade"] == "critica" else ""
        L.append(f"  zona {crit}{z['low']:.2f}–{z['high']:.2f} · tese {z['tese']} · \"{z['nota']}\" "
                 f"(válida até {_fmt_validade(z.get('validade'))})")
    tg = tmap.get("tese_geral")
    if tg:
        L.append(f"  tese geral: {tg.get('direcao')} — \"{str(tg.get('nota') or '')[:120]}\"")
    L.append(
        "  COMO PESAR ESTE MAPA: o trader marcou estas zonas ANTES do preço lá chegar. Reações do preço numa "
        "zona marcada = MÁXIMA ATENÇÃO — nestas zonas a sensibilidade é de 1ª rejeição (não exijas confirmação "
        "repetida para DESCREVER a absorção/rejeição que a fita mostrar). O mapa NÃO é ordem: o trader pode "
        "estar errado, e se a fita contradisser a tese dele com evidência clara, di-lo frontalmente — descreve "
        "a realidade, como sempre. MAS: um candidato CONTRA a tese declarada DENTRO ou ENCOSTADO (≤1 ATR) a "
        "uma zona marcada exige convicção EXTRAORDINÁRIA (fita inequívoca no sentido do candidato, invalidação "
        "da tese do trader nomeada e visível nos dados) E OBRIGA a declarar o conflito por extenso no reasoning "
        "e em conflicting_readings ('CONTRA a leitura declarada do trader: zona X, tese Y'). Nunca apresentes "
        "um candidato contra-mapa como leitura limpa.")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    if "--validate" in sys.argv:
        tmap = load_map()
        if not tmap:
            print("mapa: VAZIO/inexistente/expirado (fail-open — sistema opera como antes)")
            sys.exit(0)
        print(f"mapa ATIVO (updated {tmap.get('updated_ts')}):")
        for z in tmap["zones"]:
            print(f"  {z['id']}: {z['low']}-{z['high']} tese={z['tese']} crit={z['criticidade']} "
                  f"validade={z.get('validade')}")
        if tmap.get("tese_geral"):
            print(f"  tese_geral: {tmap['tese_geral']}")
        sys.exit(0)
    if "--selftest" in sys.argv:
        now = dt.datetime(2026, 8, 4, 10, 0, tzinfo=dt.timezone.utc)
        fix = {"version": 1, "updated_ts": "x", "zones": [
            {"id": "s1", "low": 4066.0, "high": 4073.0, "tese": "SHORT", "nota": "n", "criticidade": "critica",
             "validade": "2026-08-08T21:00:00Z"},
            {"id": "old", "low": 4000.0, "high": 4010.0, "tese": "LONG", "nota": "n", "criticidade": "normal",
             "validade": "2026-08-01T00:00:00Z"}],
            "tese_geral": {"direcao": "SHORT", "nota": "bear", "validade": "2026-08-08T21:00:00Z"}}
        MAP_F_BAK = globals()["MAP_F"]
        tmp = BASE / ".trader_map_selftest.json"
        tmp.write_text(json.dumps(fix))
        globals()["MAP_F"] = tmp
        try:
            m = load_map(now)
            ok1 = m and len(m["zones"]) == 1 and m["zones"][0]["id"] == "s1"          # expirada removida
            c = conflict({"direction": "LONG", "entry": 4063.36}, m, atr=5.77)
            ok2 = c is not None and c["id"] == "s1"                                    # caso 08:03 real
            ok3 = conflict({"direction": "SHORT", "entry": 4068.0}, m, atr=5.77) is None   # mesma tese = sem conflito
            ok4 = conflict({"direction": "LONG", "entry": 4040.0}, m, atr=5.77) is None    # longe (>1ATR) = sem conflito
            sec = render_section(m)
            ok5 = "MAPA DO TRADER" in sec and "4066.00–4073.00" in sec and "NÃO ordem" in sec
            for lab, ok in (("expiradas removidas", ok1), ("conflito 08:03 detetado", ok2),
                            ("mesma tese sem conflito", ok3), ("longe sem conflito", ok4),
                            ("render seção ok", ok5)):
                print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
            allok = ok1 and ok2 and ok3 and ok4 and ok5
            print("selftest", "PASS" if allok else "FAIL")
            sys.exit(0 if allok else 1)
        finally:
            globals()["MAP_F"] = MAP_F_BAK
            tmp.unlink(missing_ok=True)
    print("uso: trader_map.py --validate | --selftest")
