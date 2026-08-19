#!/usr/bin/env python3
"""ZONE-WATCH — máquina de estados determinística por zona (Cris 2026-08-12).

Resolve o erro "inverti a convicção cedo e desliguei-me": a deteção de ENTRADA/REJEIÇÃO/ROMPIMENTO deixa
de depender do juízo do Claude. Corre via launchd (StartInterval ~30s → sobrevive, não é loop que dorme).
Lê o preço 5M do bar-store e, para cada zona declarada (short/long) com invalidação, avança um FSM:

  ARMED --preço ENTRA na zona--> TAGGED --fecha DE VOLTA fora (rejeição)--> alarme REJEIÇÃO (o que se perdeu)
                                        \--fecha ALÉM da invalidação-------> alarme ROMPIMENTO (tese morta)

Cada transição relevante: toca som local 4x + escreve no log (o monitor/vela faz tail → acorda o Claude).
Estado persistido em zone_watch_state.json (sobrevive entre execuções do launchd). py3 stdlib, local-only.
Uma execução = um "tick" (lê último 5M bar, avança FSM, sai). O launchd repete.

READ_OB_ZONES — os níveis de ZONES NÃO são inventados: derivam da OB Detector v11 LIDA por MCP nesta sessão
(SOURCE: SUPPLY 15M 4408.57-4416.06 id 4314 + SUPPLY 1H/15M 4418.12-4435.2 id 4300). Editáveis quando a OB
mudar; a máquina só executa o FSM sobre zonas de proveniência-real.
"""
import json, subprocess, sys, time
from pathlib import Path

STORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_5m.jsonl")
STATE = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/zone_watch_state.json")
LOG = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/zone_watch.jsonl")
SOUND = "/System/Library/Sounds/Sosumi.aiff"

# Zonas vigiadas. side: 'short' (rejeição no topo) | 'long' (rejeição no fundo).
# SOURCE=OB Detector v11 lida por MCP (READ_OB_ZONES) — NÃO hardcode inventado.
# entrar = preço ALCANÇA [lo,hi]; rejeição = fecha DE VOLTA fora; invalidação = fecha ALÉM.
# AUDIT-FIX 19/08 (D7): "expires" (epoch) obrigatório — zona vencida é ignorada no tick (antes as zonas
# datadas ficavam armadas para sempre; ex.: zonas de 18/08 ainda vivas a 19/08 pós-rally).
ZONES = [
    # READ_OB_ZONES 2026-08-18 (Cris: 'avisa qualquer rejeição impressa'; ~11:55 'PL 1H 4405/4410 + FVG = reteste').
    # SOURCE: polaridade 1H topos 4404.34/4411.42/4413.72 + FVG 15M 4408.3-4411.7 (dentro do FVG 1H 4408.3-4419)
    # + ex-demanda 15M 4398.35-4406.2 quebrada 03:30. lo=4404.3 evita falso-alarme no chop 4396-4399.
    {"id": "short_retest_4404_4413", "side": "short", "lo": 4404.3, "hi": 4413.7, "inval": 4419.0, "expires": 1787263200},
    # SOURCE: OB supply 15M 4428.5-4436.2 (rejeição impressa 02:00 de 18/08); inval=topo supply 4441-4449.7.
    {"id": "short_supply_4428_4436", "side": "short", "lo": 4428.5, "hi": 4436.2, "inval": 4449.7, "expires": 1787263200},
    # Fundo do range: OB 1H 4377.2-4394.3 base + inval do reader 4386.20. Rejeição=long configurou;
    # DONE_BREAK (fecho <4375.2 = topo OB 15M 4367.2-4375.2) = DESCEU DIRETO, short de reteste perdeu o comboio.
    {"id": "floor_4377_4386", "side": "long", "lo": 4377.2, "hi": 4386.2, "inval": 4375.2, "expires": 1787263200},
]


def last_bar():
    try:
        for ln in reversed(STORE.read_text().splitlines()):
            ln = ln.strip()
            if ln:
                return json.loads(ln)
    except Exception:
        return None
    return None


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(s):
    try:
        STATE.write_text(json.dumps(s))
    except Exception:
        pass


def alarm(msg):
    for _ in range(4):
        subprocess.run(["afplay", SOUND], check=False)
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps({"msg": msg}) + "\n")
    except Exception:
        pass
    print("🔔 " + msg)


def step(zone, bar, st):
    """Avança o FSM de UMA zona. Devolve (novo_estado, alarme_ou_None). Puro (sem I/O)."""
    zid = zone["id"]
    side = zone["side"]
    state = st.get(zid, "ARMED")
    h, l, c = bar["h"], bar["l"], bar["c"]

    # --- MODO break_retest_long (Cris 12/08): romper B -> alarme; voltar a tocar B (retest) -> alarme ENTRADA ---
    if side == "break_retest_long":
        B = zone["B"]                    # nivel de rompimento (topo da supply, SOURCE OB)
        fail = zone.get("fail", B - 8)   # fecho abaixo disto = rompimento falhou
        if state == "ARMED":
            if c > B:
                return "BROKEN", f"{zid}: 🚀 ROMPEU {B} (c={c}) — vigia o RETEST para entrar LONG (nao perseguir o rip)"
            return "ARMED", None
        if state == "BROKEN":
            if c < fail:                 # PRIMEIRO: fechou de volta abaixo = rompimento falhou (nao segurou)
                return "DONE_FAIL", f"{zid}: rompimento de {B} FALHOU (fechou {c} < {fail}). Sem retest-long; volta a vigiar."
            if l <= B:                   # voltou a tocar o nivel rompido E segurou (close>=fail) = RETEST
                return "DONE_RETEST", f"{zid}: 🎯 RETEST de {B} (l={l}, fechou {c}) — ZONA DE ENTRADA LONG. entry ~{B} · SL abaixo do retest · alvo 4435->4450."
            return "BROKEN", None
        return state, None               # DONE_* terminal

    lo, hi, inval = zone["lo"], zone["hi"], zone["inval"]
    entered = (h >= lo) if side == "short" else (l <= hi)   # tocou a zona
    if state == "ARMED":
        if entered:
            return "TAGGED", f"{zid}: PRECO NA ZONA {lo}-{hi} (c={c}) — vigia ARMADA (nao desligar ate fechar alem de {inval})"
        return "ARMED", None
    if state == "TAGGED":
        if side == "short":
            if c > inval:
                return "DONE_BREAK", f"{zid}: ROMPIMENTO — fechou {c} > {inval}. Tese SHORT morta (SO AQUI se desarma)."
            if c < lo:
                return "DONE_REJECT", f"{zid}: 🎯 REJEICAO IMPRESSA — tocou {hi}+, fechou {c} < {lo}. SHORT CONFIGUROU (o alarme que se perdeu)."
        else:  # long
            if c < inval:
                return "DONE_BREAK", f"{zid}: ROMPIMENTO p/ baixo — fechou {c} < {inval}. Tese LONG morta."
            if c > hi:
                return "DONE_REJECT", f"{zid}: 🎯 REJEICAO IMPRESSA — tocou {lo}-, fechou {c} > {hi}. LONG CONFIGUROU."
        return "TAGGED", None                    # continua dentro da zona: MANTEM ARMADO (o fix)
    return state, None                            # DONE_* = terminal


def tick():
    bar = last_bar()
    if not bar:
        return
    t = bar.get("t") or 0
    if t and (time.time() - t) > 900:            # store velho (>15min) → nao age em dado morto
        return
    st = load_state()
    for z in ZONES:
        if z.get("expires") and time.time() > z["expires"]:
            continue                                     # AUDIT-FIX D7: zona vencida não arma nem alarma
        new, al = step(z, bar, st)
        if new != st.get(z["id"], "ARMED"):
            st[z["id"]] = new
            if al:
                alarm(al)
    save_state(st)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        Z = {"id": "z", "side": "short", "lo": 4408.0, "hi": 4420.0, "inval": 4435.0}
        t = []
        s, a = step(Z, {"h": 4390, "l": 4385, "c": 4388}, {})
        t.append(("longe → ARMED", s == "ARMED" and a is None))
        s, a = step(Z, {"h": 4411, "l": 4405, "c": 4410}, {})
        t.append(("entra → TAGGED+alarme", s == "TAGGED" and a and "NA ZONA" in a))
        # sobe MAIS dentro da zona (4416) sem fechar alem inval → MANTEM TAGGED (o fix do erro!)
        s, a = step(Z, {"h": 4416, "l": 4410, "c": 4414}, {"z": "TAGGED"})
        t.append(("sobe dentro da zona → MANTEM (nao desliga!)", s == "TAGGED" and a is None))
        # tocou 4416 e FECHOU de volta abaixo de lo → REJEICAO (o alarme perdido)
        s, a = step(Z, {"h": 4416, "l": 4400, "c": 4405}, {"z": "TAGGED"})
        t.append(("rejeicao (fecha<lo) → DONE_REJECT+alarme", s == "DONE_REJECT" and a and "REJEICAO" in a))
        s, a = step(Z, {"h": 4440, "l": 4430, "c": 4438}, {"z": "TAGGED"})
        t.append(("fecha>inval → DONE_BREAK", s == "DONE_BREAK" and a and "ROMPIMENTO" in a))
        L = {"id": "l", "side": "long", "lo": 4360.0, "hi": 4372.0, "inval": 4350.0}
        s, a = step(L, {"h": 4375, "l": 4368, "c": 4370}, {})
        t.append(("long entra → TAGGED", s == "TAGGED"))
        s, a = step(L, {"h": 4380, "l": 4365, "c": 4378}, {"l": "TAGGED"})
        t.append(("long rejeicao (fecha>hi) → DONE_REJECT", s == "DONE_REJECT" and a and "REJEICAO" in a))
        s, a = step(L, {"h": 4358, "l": 4345, "c": 4348}, {"l": "TAGGED"})
        t.append(("long rompe (fecha<inval) → DONE_BREAK", s == "DONE_BREAK"))
        # break_retest_long: ainda abaixo de B → ARMED
        BR = {"id": "br", "side": "break_retest_long", "B": 4416.06, "fail": 4408.0}
        s, a = step(BR, {"h": 4412, "l": 4405, "c": 4410}, {})
        t.append(("br: abaixo de B → ARMED", s == "ARMED" and a is None))
        # fecha acima de B → BROKEN + alarme rompeu
        s, a = step(BR, {"h": 4422, "l": 4409, "c": 4419}, {})
        t.append(("br: fecha>B → BROKEN+alarme", s == "BROKEN" and a and "ROMPEU" in a))
        # BROKEN + segue a subir sem voltar → MANTEM BROKEN (nao perde o retest)
        s, a = step(BR, {"h": 4430, "l": 4420, "c": 4428}, {"br": "BROKEN"})
        t.append(("br: sobe sem voltar → MANTEM BROKEN", s == "BROKEN" and a is None))
        # BROKEN + volta a tocar B (low<=B) → DONE_RETEST + alarme ENTRADA
        s, a = step(BR, {"h": 4425, "l": 4415, "c": 4420}, {"br": "BROKEN"})
        t.append(("br: retest (low<=B) → DONE_RETEST+alarme", s == "DONE_RETEST" and a and "RETEST" in a))
        # BROKEN + fecha de volta abaixo do fail → DONE_FAIL
        s, a = step(BR, {"h": 4418, "l": 4402, "c": 4405}, {"br": "BROKEN"})
        t.append(("br: rompimento falha (c<fail) → DONE_FAIL", s == "DONE_FAIL"))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    tick()
