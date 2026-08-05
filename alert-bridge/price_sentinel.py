#!/usr/bin/env python3
"""SENTINELA DE PREÇO tick-level (Cris 2026-08-04: "constrói o sentinela"). Poll leve do quote via MCP
(~15s, UMA sessão persistente — zero contenção CDP) e imprime UMA linha quando o preço CRUZA um nível do
mapa do trader (bordas das zonas + nivel_confirmacao_short). Custo Fable = 0 em operação; o Claude é
acordado pelo Monitor SÓ no cruzamento. À noite (GLD/ws fechado) esta é a única fonte tick-level.

NÃO alerta Telegram (donos dos alertas = vela/validador) — é o gatilho de atenção do copiloto no chat.
Dedup: 1 linha por (nível, direção); re-arma se o preço recuar >=REARM_PTS do nível ou após REARM_S.
Fallback: MCP indisponível -> última 5M do store (marca [store]). py3.9."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent / "my-strategy" / "core"))
import trader_map

LX = ZoneInfo("Europe/Lisbon")
STORE = BASE.parent / "my-strategy/core/bar_store/store"
POLL_S = 15
REARM_PTS = 3.0          # re-arma o nível se o preço recuar >=3pts dele
REARM_S = 30 * 60        # ou após 30 min
SYMBOL = "PEPPERSTONE:XAUUSD"


def hm(): return dt.datetime.now(LX).strftime("%H:%M:%S")


def levels_from_map():
    """Níveis vigiados = bordas das zonas declaradas + gatilho de break. [(nome, preço, tese)]."""
    tmap = trader_map.load_map()
    if not tmap:
        return []
    out = []
    for z in tmap["zones"]:
        out.append((f"{z['id']}.low", z["low"], z["tese"]))
        out.append((f"{z['id']}.high", z["high"], z["tese"]))
    lvl = (tmap.get("tese_geral") or {}).get("nivel_confirmacao_short")
    if lvl:
        out.append(("GATILHO_BREAK", float(lvl), "SHORT"))
    return out


PROX_PTS = 2.0           # aviso de APROXIMAÇÃO: preço chega a <=2pts de um nível sem o cruzar


def proximities(cur, levels, prox_state, now):
    """Aviso one-shot quando o preço APROXIMA (<=PROX_PTS) de um nível sem cruzar — cobre a rejeição
    ANTES do toque (miss 04/08 23:30: spike a 4086 rejeitou a 4pts da micro-supply 4088-91 sem sinal).
    Re-arma com a mesma mecânica: afastou >=REARM_PTS+PROX_PTS ou REARM_S."""
    fired = []
    for name, lvl, tese in levels:
        st = prox_state.get(name, {"armed": True, "ts": 0})
        if not st["armed"] and (abs(cur - lvl) >= REARM_PTS + PROX_PTS or now - st["ts"] >= REARM_S):
            st["armed"] = True
        if st["armed"] and abs(cur - lvl) <= PROX_PTS:
            fired.append({"name": name, "level": lvl, "tese": tese, "price": cur})
            st = {"armed": False, "ts": now}
        prox_state[name] = st
    return fired


def crossings(prev, cur, levels, armed, now):
    """Cruzamentos entre prev->cur. Puro/testável. armed: nome->(armado_bool, ultimo_fire_ts).
    Re-arma por afastamento (REARM_PTS) ou tempo (REARM_S)."""
    fired = []
    for name, lvl, tese in levels:
        st = armed.get(name, {"armed": True, "ts": 0})
        just_rearmed = False
        # re-armar (só dispara a partir do tick SEGUINTE — evita fire imediato na oscilação do recuo)
        if not st["armed"]:
            if abs(cur - lvl) >= REARM_PTS or now - st["ts"] >= REARM_S:
                st["armed"] = True
                just_rearmed = True
        if st["armed"] and not just_rearmed and prev is not None:
            up = prev < lvl <= cur
            dn = prev > lvl >= cur
            if up or dn:
                fired.append({"name": name, "level": lvl, "dir": "ACIMA" if up else "ABAIXO",
                              "tese": tese, "price": cur})
                st = {"armed": False, "ts": now}
        armed[name] = st
    return fired


def _entry_on_break(price, level):
    """Entrada SHORT PRECISA no ATO do rompimento (Cris 2026-08-05: 'nunca temos entrada precisa realtime').
    SL apertado = nível rompido + buffer (invalidação = reclaim do nível); alvo = 1º OB Detector abaixo que
    dê RR>=2, senão o mais profundo. Também swing-SL 'seguro'. NADA de esperar fecho de vela."""
    try:
        with open(STORE / "bars_15m.jsonl", "rb") as f:
            f.seek(0, 2); sz = f.tell(); f.seek(max(0, sz - 30000))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        b = [x for x in rows if all(k in x for k in ("t", "o", "h", "l", "c"))][-20:]
        trs = [max(x["h"] - x["l"], abs(x["h"] - p["c"]), abs(x["l"] - p["c"])) for p, x in zip(b, b[1:])]
        atr = sum(trs[-14:]) / 14 if len(trs) >= 14 else 8.0
        swing = max(x["h"] for x in b[-8:])
    except Exception:
        atr, swing = 8.0, price + 12
    sl_tight = round(level + max(0.5 * atr, 3.0), 2)          # invalidação = reclaim do nível rompido
    sl_safe = round(swing + 0.15 * atr, 2)                    # estrutural (acima do swing)
    risk = abs(sl_tight - price) or 1
    # alvo = OB abaixo que dê RR>=2 com o SL apertado; senão o mais profundo
    tgt = None
    try:
        import market_read as MR
        obs = MR.ob_zones("240", ref_price=price) + MR.ob_zones("60", ref_price=price) + MR.ob_zones("15", ref_price=price)
        below = sorted({round(z["high"], 2) for z in obs if z["high"] < price - 3}, reverse=True)
        good = [t for t in below if (price - t) / risk >= 2.0]
        tgt = good[0] if good else (below[-1] if below else None)
    except Exception:
        pass
    rr = round((price - tgt) / risk, 1) if (tgt and risk) else None
    return {"entry": round(price, 2), "sl": sl_tight, "sl_safe": sl_safe, "target": tgt, "rr": rr}


def store_price():
    try:
        with open(STORE / "bars_5m.jsonl", "rb") as f:
            f.seek(0, 2); sz = f.tell(); f.seek(max(0, sz - 600))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        return rows[-1]["c"] if rows else None
    except Exception:
        return None


def main_loop():
    from draw_xau_4h_trades import MCPClient
    print(f"👁️ SENTINELA DE PREÇO armado — quote MCP ~{POLL_S}s, linha só no CRUZAMENTO de nível do mapa", flush=True)
    c = None
    prev = None
    armed = {}
    prox_state = {}
    last_map_load = 0
    levels = []
    while True:
        try:
            now = time.time()
            if now - last_map_load > 120:                      # recarrega o mapa a cada 2 min
                levels = levels_from_map()
                last_map_load = now
            px = None; src = "mcp"
            try:
                if c is None:
                    c = MCPClient(); c.start()
                q = c.call_tool("quote_get", {"symbol": SYMBOL}) or {}
                px = q.get("last") or q.get("close")
            except Exception:
                try:
                    if c: c.stop()
                except Exception: pass
                c = None
                px = store_price(); src = "store"
            if px is not None:
                # aproximação: SÓ chat/log (Cris 05/08: "não atrolha o Telegram") — TG fica p/ entrada/reclaim/GO.
                # coalesce: níveis partilhados (ex. 4066 = borda de 2 zonas) -> 1 linha por preço de nível
                prox = {f["level"]: f for f in proximities(float(px), levels, prox_state, now)}
                for f in prox.values():
                    print(f"📍 {hm()} APROXIMOU {f['level']:.2f} ({f['name']}, tese {f['tese']}) — "
                          f"preço {f['price']:.2f}. Atenção à reação AQUI.", flush=True)
                for f in crossings(prev, float(px), levels, armed, now):
                    print(f"👁️ {hm()} CRUZOU {f['dir']} {f['level']:.2f} ({f['name']}, tese {f['tese']}) "
                          f"— preço {f['price']:.2f} [{src}]", flush=True)
                    # RECLAIM do gatilho p/ cima = retest a falhar OU invalidação — avisa na hora
                    if f["name"] == "GATILHO_BREAK" and f["dir"] == "ACIMA":
                        txt = (f"⚠️ RECLAIM {f['level']:.2f} ({hm()}) — preço {f['price']:.2f} de volta ACIMA do nível "
                               f"rompido. Short de continuação em risco: se segurar acima, invalida; rejeição aqui = retest SHORT.")
                        print(txt, flush=True)
                        try:
                            import e2_quality as E2
                            if os.environ.get("SENTINEL_TG_AUTHORIZED", "") == "1":
                                E2._tg_send(txt, audience="assistant"); print("(→ Telegram)", flush=True)
                        except Exception:
                            pass
                    # ENTRADA PRECISA NO ATO: break do gatilho p/ baixo = SHORT já (sem esperar fecho)
                    if f["name"] == "GATILHO_BREAK" and f["dir"] == "ABAIXO":
                        e = _entry_on_break(f["price"], f["level"])
                        txt = (f"⚡🔻 ENTRADA SHORT REALTIME — rompeu {f['level']:.2f} AGORA ({hm()})\n"
                               f"entry {e['entry']} · SL {e['sl']} · alvo {e['target'] or '—'} · RR {e['rr'] or '—'}\n"
                               f"SL seguro (swing) {e['sl_safe']} · tick-level, NÃO espera fecho")
                        print(txt, flush=True)
                        try:
                            import e2_quality as E2
                            if os.environ.get("SENTINEL_TG_AUTHORIZED", "") == "1":
                                E2._tg_send(txt, audience="assistant"); print("(→ Telegram)", flush=True)
                        except Exception:
                            pass
                prev = float(px)
        except Exception as e:
            print(f"sentinela erro: {type(e).__name__}:{str(e)[:60]}", flush=True)
            time.sleep(POLL_S)
        time.sleep(POLL_S)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        lv = [("z.low", 4090.59, "SHORT"), ("GATILHO_BREAK", 4075.0, "SHORT")]
        armed = {}
        now = 1000.0
        f1 = crossings(4088.0, 4091.2, lv, armed, now)                    # cruza 4090.59 p/ cima
        ok1 = len(f1) == 1 and f1[0]["dir"] == "ACIMA" and f1[0]["level"] == 4090.59
        f2 = crossings(4091.2, 4090.8, lv, armed, now + 15)               # oscila sem re-armar: nada
        ok2 = len(f2) == 0
        f3 = crossings(4090.8, 4086.0, lv, armed, now + 30)               # recuou >=3pts -> re-arma (sem fire ainda: cruzou p/ baixo já desarmado? recuo re-arma E cruza)
        # após recuo re-armar, novo cruzamento p/ cima dispara
        f4 = crossings(4086.0, 4091.0, lv, armed, now + 60)
        ok3 = len(f4) == 1 and f4[0]["dir"] == "ACIMA"
        f5 = crossings(4076.0, 4074.2, lv, armed, now + 90)               # break do gatilho p/ baixo
        ok4 = len(f5) == 1 and f5[0]["name"] == "GATILHO_BREAK" and f5[0]["dir"] == "ABAIXO"
        ok5 = crossings(None, 4080.0, lv, {}, now) == []                  # primeiro tick: sem prev, sem fire
        for lab, ok in (("cruzamento p/ cima dispara", ok1), ("oscilação desarmada não dispara", ok2),
                        ("re-arma por afastamento + novo cruzamento", ok3), ("break gatilho p/ baixo", ok4),
                        ("primeiro tick sem prev não dispara", ok5)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    main_loop()
