#!/usr/bin/env python3
"""A1/A2 PULLBACK RUNTIME — XAU 15M LONG (ordem Cris 2026-08-05 ~07:0x: "A1 e A2 precisam ser resolvidos
URGENTE, estamos a perder trades e a virada BULL pode concretizar-se").

CONSOME o módulo-mãe aprovado `a1_causal_entry.causal_entry` (MB3 + SL low-real, commit 2f829d3) — NÃO
reinventa a régua. Este runtime só faz o que faltava (task #35): DETETAR automaticamente o fundo de
pullback candidato (antes era input discricionário do GT) e correr o entry causal no live.

DETETOR (causal, por fecho 15M do store):
  1) HH recente = max high em [i-96, i-8] (a perna que puxa)
  2) pullback = HH - min low das últimas 24b >= 1.0×ATR14 (profundidade mínima; A2 raso <=2×ATR, A1 mais fundo)
  3) j = barra do min-low (fundo candidato) → delega a causal_entry(S, j): swing-low fractal m=3 CONFIRMADO
     + MB3 (1ª verde a fechar acima do high anterior). Sinal SÓ se a barra de entrada (ei) == última fechada.
  4) SL = low real do pullback − 0.1ATR · alvo = 3R (tudo do módulo-mãe). Zero lookahead.

GATES:
  - macro: structural_1d == BULL (spec aprovada) — destravável por env A1A2_REGIME_GATE_OFF=1 (mesma
    decisão do L1 05/08: o rótulo atrasa nas viragens; default = gate ON até ordem do Cris).
  - Telegram (GRUPO — "15M BULL" qualificado pelo Cris 05/08) atrás de A1A2_PRODUCTION_AUTHORIZED=1.
  - dedup por barra de entrada; forward: cada sinal é REGISTADO p/ o a1_forward_score resolver (árbitro).
py3.9 stdlib."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import a1_causal_entry as ACE                       # módulo-mãe aprovado (causal_entry)

LX = ZoneInfo("Europe/Lisbon")
STORE = REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl"
E0 = REPO / "external_factors_v2/snapshots/market_context.json"
STATE = HERE / ".a1a2_state"
STATE.mkdir(exist_ok=True)
DEDUP = STATE / "alerted.jsonl"
LOGF = STATE / "a1a2_cycle.log"

HH_WIN, HH_GAP, PB_WIN = 96, 8, 24                  # perna: high em [i-96,i-8]; fundo: min low últimas 24b
PB_MIN_ATR = 1.0                                    # profundidade mínima do pullback
A2_MAX_ATR = 2.0                                    # <=2×ATR = raso (A2); mais fundo = A1
GATE_OFF = os.environ.get("A1A2_REGIME_GATE_OFF", "") == "1"
PROD = os.environ.get("A1A2_PRODUCTION_AUTHORIZED", "") == "1"


def log(obj):
    line = json.dumps(obj, ensure_ascii=False)
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


def store_series(n=300):
    """Constrói S no formato do módulo-mãe a partir do store live (bars fechadas)."""
    try:
        rows = [json.loads(l) for l in open(STORE) if l.strip() and l[0] == "{"]
    except Exception:
        return None
    rows = [b for b in rows if all(k in b for k in ("t", "o", "h", "l", "c"))][-n:]
    if len(rows) < 120:
        return None
    T = [b["t"] for b in rows]; O = [b["o"] for b in rows]; H = [b["h"] for b in rows]
    L = [b["l"] for b in rows]; C = [b["c"] for b in rows]
    N = len(T); EMA = [None]*N; ATR = [None]*N; ema = None; kE = 2/22; trs = []
    for i in range(N):
        ema = C[i] if ema is None else C[i]*kE + ema*(1-kE); EMA[i] = ema
        if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
        ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
    return dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)


def macro_gate():
    """(passa: bool, rótulo). Agilidade na transição (Cris 2026-08-17): elegível se 1D NÃO-BEAR (caso-base,
    inclui BULL e RANGE) OU caminho-rápido = v5_4h BULL + legs 1H e 4H ambos 'up' (dois rápidos a concordar,
    proxy de cruzamento). Assim A1/A2 apanha a viragem sem esperar o 1D lento, mas exige confirmação dupla no
    rápido para não comprar falso-BULL. env A1A2_REGIME_GATE_OFF=1 destrava tudo."""
    try:
        d = json.load(open(E0))
        ax = d.get("axes", {})
        reg1d = (ax.get("regime", {}).get("structural_1d") or {}).get("regime")
        reg4h = (ax.get("regime", {}).get("v5_4h") or {}).get("regime")
        mtf = ax.get("mtf", {})
        leg1h = ((mtf.get("60") or {}).get("leg") or {}).get("dir")
        leg4h = ((mtf.get("240") or {}).get("leg") or {}).get("dir")
    except Exception:
        reg1d = reg4h = leg1h = leg4h = None
    if GATE_OFF:
        return True, f"{reg1d or '?'} (gate OFF por env)"
    base = reg1d in ("BULL", "RANGE")
    fast = (reg4h == "BULL") and (leg1h == "up") and (leg4h == "up")
    if base:
        return True, f"1D {reg1d} (não-BEAR)"
    if fast:
        return True, f"rápido: 4H BULL + legs 1H/4H up (1D {reg1d})"
    return False, f"1D {reg1d or '?'} · 4H {reg4h or '?'} · leg1h {leg1h or '?'} leg4h {leg4h or '?'}"


def detect(S):
    """Fundo de pullback candidato -> causal_entry. Sinal só se entrada == ÚLTIMA barra fechada."""
    N, H, L, ATR = S["N"], S["H"], S["L"], S["ATR"]
    i = N - 1
    atr = ATR[i] or 5.0
    if i - HH_GAP <= 0:
        return None, "sem HH"
    hh_win = range(max(0, i-HH_WIN), i-HH_GAP)
    hh_i = max(hh_win, key=lambda z: H[z])
    hh = H[hh_i]
    # FIX 05/08 (2ª perna do bug do SL-94pts): o fundo do pullback é o min low DEPOIS do topo da perna —
    # nunca uma barra do rally (o min-24b cego caía no rally e inflava depth/SL).
    j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
    if i - j > PB_WIN:
        return None, f"fundo do pullback velho ({i-j}b atrás)"
    depth = (hh - L[j]) / atr
    if depth < PB_MIN_ATR:
        return None, f"pullback raso demais ({depth:.1f}ATR)"
    # FIX 05/08 (bug apanhado pelo Cris: SL 94pts): a âncora do módulo-mãe olha j-16 barras — num rally
    # vertical isso agarra o low do RALLY, não do pullback. Fatiar a série a partir de j-3 prende a âncora
    # ao fundo real do pullback (espec: "SL = low REAL do pullback").
    start = max(0, j - 3)
    Sx = {k: (v[start:] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = ACE.causal_entry(Sx, j - start, kind="MB3")
    if not r:
        return None, f"fundo@{j} sem MB3 ainda (depth {depth:.1f}ATR)"
    r["ei"] += start
    if r["ei"] != N - 1:
        return None, f"MB3 antigo (ei={r['ei']} != {N-1}) — não é a barra corrente"
    # GUARDA DE ESCALA 15M (Cris 05/08: "SL gigantesco = estratégia de 4H, não 15M"): risco > 2.5×ATR
    # descaracteriza o A1/A2 — sem sinal.
    if r["R"] > 2.5 * atr:
        return None, f"R {r['R']:.1f}pts > 2.5×ATR({atr:.1f}) — escala de 4H, não é A1/A2 15M"
    layer = "A2" if depth <= A2_MAX_ATR else "A1"
    r["layer"], r["depth_atr"] = layer, round(depth, 2)
    # LOCALIZAÇÃO (lição Cris 05/08: MB3 pode imprimir com o bounce quase corrido = compra no topo do
    # retrace; a entrada ideal era o retest ~4155). Reportar no sinal: % do bounce já corrido + zona de
    # entrada LIMITE (retest do high rompido ↔ 50% do bounce). Advisory — não muda a mecânica aprovada.
    pb_low = L[j]
    bounce = r["ent"] - pb_low
    r["bounce_pct"] = round(100 * bounce / (hh - pb_low)) if hh > pb_low else None
    broken_h = H[r["ei"] - 1] if r["ei"] >= 1 else None
    mid_b = round(pb_low + 0.5 * bounce, 2)
    r["retest_zone"] = (min(mid_b, broken_h), max(mid_b, broken_h)) if broken_h else (mid_b, mid_b)
    return r, "SINAL"


def already(entry_t):
    try:
        return any(json.loads(l).get("entry_t") == entry_t for l in open(DEDUP) if l.strip())
    except Exception:
        return False


def cycle():
    ok_gate, reg = macro_gate()
    S = store_series()
    if S is None:
        log({"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "SEM_STORE"}); return
    last_t = S["T"][-1]
    r, why = detect(S)
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
           "last_bar": dt.datetime.fromtimestamp(last_t, LX).strftime("%d/%m %H:%M"),
           "regime": reg, "gate": "PASS" if ok_gate else "BLOCK", "detect": why}
    if r and ok_gate and not already(last_t):
        ts = dt.datetime.fromtimestamp(last_t, LX).strftime("%d/%m %H:%M")
        # formato único notify.py (Cris 2026-08-19) — retest ideal vira tag curta; resto vive no ledger
        import notify as NF
        txt = NF.build_signal("ENTRADA", f"A1/A2 {r['layer']}", "15M", "LONG",
                              r["ent"], r["sl"], r["tgt"], r=3,
                              event=f"MB3 · retest ideal {r['retest_zone'][0]:.1f}-{r['retest_zone'][1]:.1f}")
        out["signal"] = {k: r[k] for k in ("layer", "ent", "sl", "tgt", "R", "depth_atr")}
        with open(DEDUP, "a") as f:
            f.write(json.dumps({"entry_t": last_t, **out["signal"]}) + "\n")
        print(txt, flush=True)
        if PROD:
            try:
                # GUARD-CHoCH ATIVO (Cris 2026-08-14): A1/A2 é LONG — não enviar se CHoCH-down 4H+1H (faca).
                import choch_guard as CHG
                if CHG.blocks_long():
                    out["tg"] = "choch-blocked (dn 4H+1H)"
                    print("(CHoCH-guard: A1/A2 LONG bloqueado — choch_dn 4H+1H, não enviado)", flush=True)
                else:
                    out["tg"] = NF._send(txt, "group")        # GRUPO (sinal qualificado 15M BULL)
            except Exception as e:
                out["tg"] = f"erro:{type(e).__name__}"
        else:
            out["tg"] = "hard-lock (A1A2_PRODUCTION_AUTHORIZED!=1)"
    elif r and not ok_gate:
        out["blocked_signal"] = {k: r[k] for k in ("layer", "ent", "sl", "tgt")}
    log(out)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        # série sintética: perna de subida -> pullback 1.5ATR -> fundo fractal -> MB3 na última barra
        import math
        T=[]; O=[]; H=[]; L=[]; C=[]
        px = 4000.0; t = 1785000000
        seq = [+2]*60 + [-1.2]*10 + [0.2, -0.4, -0.6, 0.3, 0.5] + [3.0]   # sobe, cai, fundo, MB3 forte
        prev_h = None
        for d in seq:
            o = px; c = px + d; h = max(o, c) + 0.6; l = min(o, c) - 0.6
            T.append(t); O.append(o); H.append(h); L.append(l); C.append(c)
            px = c; t += 900
        N=len(T); EMA=[None]*N; ATR=[None]*N; ema=None; kE=2/22; trs=[]
        for i in range(N):
            ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i]=ema
            if i>0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
            ATR[i]=sum(trs[-14:])/14 if len(trs)>=14 else None
        S = dict(T=T,O=O,H=H,L=L,C=C,EMA=EMA,ATR=ATR,N=N)
        r, why = detect(S)
        ok1 = r is not None and r["ei"] == N-1
        ok2 = r is not None and r["sl"] < r["ent"] < r["tgt"]
        # sem MB3 (última barra vermelha) -> não dispara
        C2 = C[:]; C2[-1] = O[-1] - 1.0; S2 = dict(S, C=C2)
        r2, _ = detect(S2)
        ok3 = r2 is None
        for lab, ok in (("MB3 no fecho corrente dispara", ok1), ("níveis coerentes ent/sl/tgt", ok2),
                        ("última barra vermelha NÃO dispara", ok3)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        print("selftest", "PASS" if all([ok1, ok2, ok3]) else "FAIL")
        sys.exit(0 if all([ok1, ok2, ok3]) else 1)
    cycle()
