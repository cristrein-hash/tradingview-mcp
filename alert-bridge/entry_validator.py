#!/usr/bin/env python3
"""VALIDADOR DE ENTRADA — fulltime/realtime/paralelo (Cris 2026-08-04). NÃO decide direção nem procura trades
(isso é o Cris). Pega nos níveis QUE O CRIS DECLARA no mapa (zonas + gatilho de break) e, em tempo real, dá o
ESTADO de cada entrada: ESPERA / GO / INVALIDOU / DISTANTE — com entry/SL/alvo/RR quando GO. Valida a leitura
DELE, no nível DELE, dá confiança para carregar no gatilho. Alerta só nas TRANSIÇÕES para GO (o momento).

CONSOME vela_no_nivel.decide (rejeição-por-zona) + a lógica de break — não reinventa régua. Corre em paralelo
ao sistema de sinais (E2/vela/candle-reader), sem os tocar. Telegram do GO atrás de EV_TG_AUTHORIZED.
Estado contínuo em logs/entry_validator_status.json (snapshot) + stdout. py3.9."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import trader_map
import vela_no_nivel as V

LX = ZoneInfo("Europe/Lisbon")
STORE = BASE.parent / "my-strategy/core/bar_store/store"
STATUS_F = BASE / "logs" / "entry_validator_status.json"
LAST_TG_F = BASE / "logs" / ".entry_validator_last_tg.json"   # cooldown PERSISTENTE (sobrevive a restarts —
                                                              # cada restart zerava o dedup e re-enviava; Cris 10/08)


def _load_last_tg():
    try:
        return {k: float(v) for k, v in json.loads(LAST_TG_F.read_text()).items()}
    except Exception:
        return {}


def _save_last_tg(d):
    try:
        tmp = LAST_TG_F.with_suffix(".tmp"); tmp.write_text(json.dumps(d)); os.replace(tmp, LAST_TG_F)
    except Exception:
        pass
TG_OK = os.environ.get("EV_TG_AUTHORIZED", "") == "1"
POLL_S = 25
NEAR_ATR = 1.5           # dentro de 1.5·ATR da zona = EM JOGO (ESPERA); mais longe = DISTANTE
import os as _os
TG_COOLDOWN_S = int(_os.environ.get("EV_TG_COOLDOWN_S") or 7200)   # anti-spam: mesma zona não re-alerta TG <2h
                                                                   # (o estado oscila GO→ESPERA→GO entre barras
                                                                   # e re-disparava o MESMO sinal 5×; Cris 10/08)


def hm(t): return dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")


def _bars(fname, n=80):
    try:
        with open(STORE / fname, "rb") as f:
            f.seek(0, 2); sz = f.tell(); f.seek(max(0, sz - 30000))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        return [b for b in rows if all(k in b for k in ("t", "o", "h", "l", "c"))][-n:]
    except Exception:
        return []


def eval_zone(zone, last15, last1h, atr15, atr1h, price, tmap, dsr):
    """Estado da entrada de REJEIÇÃO numa zona declarada. GO se a última 15M OU 1H rejeitou; INVALIDOU se o
    preço foi ACEITE do outro lado da zona; DISTANTE se longe; senão ESPERA."""
    zl, zh, tese = zone["low"], zone["high"], zone["tese"]
    # GO: rejeição impressa (mesma régua da vela) em 15M ou 1H
    for bar, atr, tf in ((last15, atr15, "15"), (last1h, atr1h, "1H")):
        if bar and atr:
            r = V.decide(bar, zone, atr)
            if r:
                tgts = V.targets_for(r, tmap, dsr) if dsr else []
                risk = abs(r["entry"] - r["sl"]) or 1
                rr = round(abs(r["entry"] - tgts[0]) / risk, 1) if tgts else None
                return {"state": "GO", "tf": tf, "entry": r["entry"], "sl": r["sl"],
                        "target": tgts[0] if tgts else None, "rr": rr, "wick_pct": r["wick_pct"]}
    # INVALIDOU: preço aceite do lado errado da zona (short: fechou acima do topo; long: abaixo do fundo)
    lc = last15["c"] if last15 else price
    if tese == "SHORT" and lc > zh + 0.2 * (atr15 or 6):
        return {"state": "INVALIDOU", "detail": f"fechou {lc} acima da zona (supply aceite)"}
    if tese == "LONG" and lc < zl - 0.2 * (atr15 or 6):
        return {"state": "INVALIDOU", "detail": f"fechou {lc} abaixo da zona (demanda perdida)"}
    # DISTANTE vs ESPERA
    dist = min(abs(price - zl), abs(price - zh)) if not (zl <= price <= zh) else 0
    if dist > NEAR_ATR * (atr15 or 6):
        return {"state": "DISTANTE", "detail": f"{dist:.0f}pts da zona"}
    return {"state": "ESPERA", "detail": ("no nível, sem rejeição ainda" if zl - 1 <= price <= zh + 1
                                          else f"a {dist:.0f}pts — a aproximar")}


def eval_break(tmap, last15, atr15, price):
    """Estado da entrada de CONTINUIDADE no break do gatilho declarado (nivel_confirmacao_short)."""
    lvl = ((tmap.get("tese_geral") or {}).get("nivel_confirmacao_short"))
    if not lvl or not last15 or not atr15:
        return None
    lc = last15["c"]
    if lc < lvl - 0.05 * atr15:
        swing = max((b["h"] for b in _bars("bars_15m.jsonl", 9)[-8:-1]), default=last15["h"])
        sl = round(max(swing, last15["h"]) + 0.15 * atr15, 2)
        return {"level": lvl, "state": "GO", "entry": lc, "sl": sl,
                "detail": f"15M fechou {lc} abaixo de {lvl} = break confirmado (short continuidade)"}
    if price > lvl:
        return {"level": lvl, "state": "ESPERA", "detail": f"preço {price} acima de {lvl} — sem break"}
    return {"level": lvl, "state": "ESPERA", "detail": f"a testar {lvl}"}


def _tg(txt):
    if (BASE / "logs" / ".break_retest_tg_off").exists():   # kill-switch (Cris 10/08: para spam rompimento/reteste)
        return "tg-off (kill-switch rompimento/reteste)"
    if not TG_OK:
        return "tg-off"
    try:
        import e2_quality as E2
        return "tg" if E2._tg_send(txt, audience="assistant") else "tg-fail"
    except Exception:
        return "tg-erro"


def snapshot(rows, price, ts):
    import os, tempfile
    tmp = STATUS_F.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": ts, "price": price, "levels": rows}, ensure_ascii=False, indent=1))
    os.replace(tmp, STATUS_F)


def main_loop():
    print(f"🎯 VALIDADOR DE ENTRADA armado — GO/ESPERA/INVALIDOU nos níveis do Cris, realtime "
          f"(telegram GO={'ON' if TG_OK else 'OFF'})", flush=True)
    last_state = {}                                   # id -> state (p/ alertar só transições p/ GO)
    last_tg = _load_last_tg()                          # id -> ts último TG, PERSISTENTE (anti-spam sobrevive restart)
    while True:
        try:
            tmap = trader_map.load_map()
            m15 = _bars("bars_15m.jsonl"); m5 = _bars("bars_5m.jsonl")
            if tmap and len(m15) >= 16:
                price = (m5[-1]["c"] if m5 else m15[-1]["c"])
                # OB AUTO-WATCH (Cris 10/08): valida também as demandas OB Detector perto do preço, não só
                # as declaradas. Dedup vs declaradas dentro de load_ob_zones. Fail-safe.
                try:
                    import ob_watch
                    obz = ob_watch.load_ob_zones(price, tmap["zones"])
                    if obz:
                        tmap = {**tmap, "zones": tmap["zones"] + obz}
                except Exception as e:
                    print(f"ob_watch erro transitório: {type(e).__name__}:{str(e)[:50]}", flush=True)
                last15 = m15[-1]
                h1 = [b for b in V.agg_1h(m15) if b.get("_n15") == 4]
                last1h = h1[-1] if h1 else None
                atr15 = V.atr14(m15); atr1h = V.atr14(h1) if len(h1) >= 15 else atr15
                try:
                    import e2_quality as E2
                    dsr = E2.load_dossier() or {}
                except Exception:
                    dsr = {}
                rows = []
                for zone in tmap["zones"]:
                    st = eval_zone(zone, last15, last1h, atr15, atr1h, price, tmap, dsr)
                    st["id"] = zone["id"]; st["zona"] = f"{zone['low']:.0f}-{zone['high']:.0f}"; st["tese"] = zone["tese"]
                    rows.append(st)
                bk = eval_break(tmap, last15, atr15, price)
                if bk:
                    bk["id"] = "break_gatilho"; bk["zona"] = f"<{bk['level']}"; bk["tese"] = "SHORT"
                    rows.append(bk)
                ts = hm(m15[-1]["t"])
                snapshot(rows, price, ts)
                # alertar só TRANSIÇÕES para GO (o momento de entrar)
                for r in rows:
                    if r["state"] == "GO" and last_state.get(r["id"]) != "GO":
                        klass = "break" if r["id"] == "break_gatilho" else f"reject_{r.get('tf','15')}"
                        key = f"{klass}_{last15['t']}"
                        e = r.get("entry"); s = r.get("sl"); t = r.get("target"); rr = r.get("rr")
                        # GATE DO READER (ordem Cris 05/08 02:4x: "validador TEM QUE passar pelo reader" —
                        # o GO SHORT 4084 saiu com o preço em força máxima; 1 vela de rejeição ≠ rejeição da
                        # zona). GO mecânico → reader lê o contexto; só vai a TG se o reader NÃO refutar.
                        # Reader indisponível = fail-open (TG sai — o gate nunca pode calar por avaria).
                        jz = ""
                        # FAIL-CLOSED p/ SHORT (Cris 10/08: short 4341 vazou ao TG por reader SALTADO —
                        # dossiê momentaneamente vazio no race, o consult não correu, ok_reader ficou True).
                        # LONG = fail-open (default True); SHORT = fail-CLOSED (só ao TG se o reader CONFIRMAR).
                        ok_reader = (r["tese"] == "LONG")
                        # GATE DE DOUTRINA (Cris 05/08 16:4x): reversão SÓ em região 4H/1D macro (mapa
                        # marca a única permitida). SHORT fora dela = chat-only SEMPRE, mesmo com o
                        # reader indisponível (o fail-open deixou passar um short contra-doutrina às 19:1x).
                        # GATE DE DOUTRINA (Cris 07/08: "esquece shorts" — inversão bull confirmada 4285).
                        # SHORT fora de 4337-82 macro = chat-only SEMPRE.
                        if r["tese"] == "SHORT" and r.get("id") != "ob_supply_4h_4337_4382":
                            print(f"(doutrina: SHORT em {r.get('id')} fora da região macro — chat-only)", flush=True)
                            ok_reader = False
                            jz = "\n(continuação: reversão só na zona 4H/1D macro — não enviado)"
                        # GATE-CHoCH p/ LONG (Cris 2026-08-14): bloqueia GO-LONG se CHoCH-down (quebra do
                        # higher-low) no 4H E 1H (consome dossiê E0). Impede induzir compra na faca (13/08:
                        # GO-longs o dia todo num down-leg). Fail-open: sem dossiê = não bloqueia.
                        if r["tese"] == "LONG":
                            try:
                                import choch_guard as CHG
                                if CHG.blocks_long():
                                    print("(CHoCH-guard: GO-LONG bloqueado — choch_dn 4H+1H, não enviado)", flush=True)
                                    ok_reader = False
                                    jz = "\n(CHoCH-guard: quebra estrutural 4H+1H — long não enviado, é faca)"
                            except Exception:
                                pass
                            # SWEEP-REJECT 4H (Cris 2026-08-14, tripwire): vela 4H pavio-sup>50%corpo bloqueia
                            # GO-LONG ate quebra de estrutura 15M (HH+HL). Fail-open.
                            try:
                                import sweep_reject_guard as SRG
                                if SRG.blocks_long():
                                    print("(sweep-reject-4H: GO-LONG bloqueado — sweep>50%corpo sem quebra 15M)", flush=True)
                                    ok_reader = False
                                    jz = "\n(sweep-reject-4H: vela 4H pavio>50%corpo, sem quebra 15M — long não enviado)"
                            except Exception:
                                pass
                        try:
                            import e2_quality as E2
                            dsr = E2.load_dossier() or {}
                            if dsr and ok_reader:               # doutrina-bloqueado NÃO consulta (nem re-abre)
                                cand = {"direction": r["tese"], "rule": "validator_go", "tf": r.get("tf", "15"),
                                        "entry": e, "sl": s, "target": t or (e - 3 * abs(e - s) if r["tese"] == "SHORT"
                                                                             else e + 3 * abs(e - s)),
                                        "rr": rr or 3.0,
                                        "materiality": {"sl_atr": None, "confluence": None, "confluence_breakdown": {}}}
                                th = E2.run_read(cand, dsr, timeout=90)
                                if not th.get("error"):
                                    sf = E2.surfaced(th, cand)
                                    cv = E2.fnum(th.get("conviction")) or 0
                                    thesis = str(th.get("thesis") or "")
                                    # ANTI-PREMATURO (Cris 07/08 03:xx: GO conv48 'CONFIRMA' mas tese='preço ainda
                                    # a subir/prematuro' chegou ao TG). Exigir conv>=55 E que a tese NÃO se
                                    # auto-contradiga com 'prematuro/ainda a subir/antecipa'. Fronteira = chat-only.
                                    premature = any(w in thesis.lower() for w in
                                                    ("prematur", "ainda a sub", "antecipa", "sem rejeição", "não imp"))
                                    jz = (f"\nreader: {'CONFIRMA' if sf else 'NÃO confirma'} · conv {th.get('conviction')} · "
                                          f"{thesis[:150]}")
                                    ok_reader = bool(sf) and cv >= 55 and not premature
                        except Exception as ex:
                            # FAIL-CLOSED p/ SHORT (Cris 07/08: GO short 4341 chegou ao TG sem juízo por
                            # falha do reader). Reader indisponível: LONG mantém fail-open; SHORT = chat-only.
                            if r["tese"] == "SHORT":
                                ok_reader = False
                                jz = f"\n(reader indisponível — SHORT retido por segurança, não enviado)"
                            else:
                                jz = f"\n(reader indisponível: {type(ex).__name__} — long enviado sem juízo)"
                        txt = (f"🎯 VALIDADOR: GO — {r['tese']} @ {r.get('zona')} ({r.get('id')})\n"
                               f"{r.get('detail','rejeição/break confirmado')}\n"
                               f"entry {e} · SL {s} · alvo {t or '—'} · RR {rr or '—'}{jz}\n"
                               f"(validação da TUA entrada — a decisão é tua)")
                        print(txt, flush=True)
                        if not ok_reader:
                            print("(canal: chat-only — reader refutou o GO mecânico)", flush=True)
                        elif time.time() - last_tg.get(r["id"], 0) < TG_COOLDOWN_S:
                            # ANTI-SPAM (Cris 10/08: 5 msgs iguais): mesma zona já alertou há <2h — chat-only.
                            print("(canal: chat-only — cooldown do mesmo sinal/zona, já alertado <2h)", flush=True)
                        else:
                            first = V.tg_claim(key)
                            if first:
                                last_tg[r["id"]] = time.time(); _save_last_tg(last_tg)   # persiste cooldown
                            print(f"(canal: {_tg(txt) if first else 'dedup — vela já alertou'})", flush=True)
                    # sinal que TINHA dado GO e invalidou = alerta de SL/saída (relativo ao sinal — Cris 05/08:
                    # TG só sinais entry/SL/TP e alertas relativos a eles)
                    if r["state"] == "INVALIDOU" and last_state.get(r["id"]) == "GO":
                        txt = (f"🛑 INVALIDOU — {r.get('tese')} @ {r.get('zona')} ({r.get('id')})\n"
                               f"{r.get('detail','')}\nSe estás no trade deste sinal: zona perdida, reavalia SL/saída.")
                        print(txt, flush=True)
                        print(f"(canal: {_tg(txt)})", flush=True)
                    last_state[r["id"]] = r["state"]
        except Exception as e:
            print(f"validador erro: {type(e).__name__}:{str(e)[:70]}", flush=True)
        time.sleep(POLL_S)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        tmap = {"zones": [{"id": "z", "low": 4101.07, "high": 4116.28, "tese": "SHORT", "criticidade": "critica", "nota": ""}],
                "tese_geral": {"nivel_confirmacao_short": 4075.0}}
        atr = 7.9
        # GO: rejeição na premium (a vela 18:00)
        b_go = {"t": 1785862800, "o": 4093.46, "h": 4106.46, "l": 4092.53, "c": 4099.85}
        rgo = eval_zone(tmap["zones"][0], b_go, None, atr, atr, 4099.85, tmap, {})
        ok1 = rgo["state"] == "GO" and rgo["entry"] == 4099.85
        # ESPERA: preço encostado sem rejeição
        b_wait = {"t": 2, "o": 4098, "h": 4100, "l": 4097, "c": 4099}
        ok2 = eval_zone(tmap["zones"][0], b_wait, None, atr, atr, 4099, tmap, {})["state"] in ("ESPERA", "DISTANTE")
        # INVALIDOU: fechou acima da supply
        b_inv = {"t": 3, "o": 4110, "h": 4120, "l": 4109, "c": 4119}
        ok3 = eval_zone(tmap["zones"][0], b_inv, None, atr, atr, 4119, tmap, {})["state"] == "INVALIDOU"
        # DISTANTE: preço longe
        ok4 = eval_zone(tmap["zones"][0], {"t": 4, "o": 4060, "h": 4062, "l": 4058, "c": 4060}, None, atr, atr, 4060, tmap, {})["state"] == "DISTANTE"
        # break GO
        bk = eval_break(tmap, {"t": 5, "o": 4076, "h": 4077, "l": 4072, "c": 4072.5}, atr, 4072.5)
        ok5 = bk and bk["state"] == "GO" and bk["entry"] == 4072.5
        # break ESPERA
        bk2 = eval_break(tmap, {"t": 6, "o": 4080, "h": 4082, "l": 4078, "c": 4080}, atr, 4080)
        ok6 = bk2 and bk2["state"] == "ESPERA"
        for lab, ok in (("GO na rejeição da premium", ok1), ("ESPERA encostado sem rejeição", ok2),
                        ("INVALIDOU fechou acima", ok3), ("DISTANTE longe", ok4),
                        ("break <4075 = GO", ok5), ("acima de 4075 = ESPERA", ok6)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5, ok6])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    if "--once" in sys.argv:
        tmap = trader_map.load_map()
        m15 = _bars("bars_15m.jsonl"); m5 = _bars("bars_5m.jsonl")
        price = m5[-1]["c"]; last15 = m15[-1]
        h1 = [b for b in V.agg_1h(m15) if b.get("_n15") == 4]; last1h = h1[-1] if h1 else None
        atr15 = V.atr14(m15); atr1h = V.atr14(h1) if len(h1) >= 15 else atr15
        try:
            import e2_quality as E2; dsr = E2.load_dossier() or {}
        except Exception:
            dsr = {}
        print(f"preço {price} @ {hm(last15['t'])}")
        for zone in tmap["zones"]:
            st = eval_zone(zone, last15, last1h, atr15, atr1h, price, tmap, dsr)
            print(f"  [{st['state']:9}] {zone['tese']} {zone['low']:.0f}-{zone['high']:.0f} — {st.get('detail', st.get('entry',''))}")
        bk = eval_break(tmap, last15, atr15, price)
        if bk:
            print(f"  [{bk['state']:9}] SHORT break <{bk['level']} — {bk.get('detail','')}")
        sys.exit(0)
    main_loop()
