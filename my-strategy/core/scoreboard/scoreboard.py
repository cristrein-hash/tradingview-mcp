#!/usr/bin/env python3
"""SCOREBOARD forward das linhas live (Cris 2026-08-18). Uma página: por linha, N·WR·sumR(3R)·DD·streak +
RESULTADO REAL DE SEGURAR (não só o 3R fixo): MFE em R (quanto o trade deu antes de morrer/agora) e R-se-segurasse
(SL nunca tocado -> marcação ao preço atual; SL tocado -> -1R). Fontes = os ledgers que JÁ existem (consumir, não
reconstruir). Resolução SL-first contra bars_15m do store (retenção 30d — sinais mais velhos ficam UNRESOLVED).
Corre à mão ou semanal (domingo). Sem Telegram — output = stdout + reports/scoreboard_<data>.txt. py3 stdlib."""
import json, sys, time
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
STORE15 = REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl"
OUT = Path(__file__).resolve().parent / "reports"
OUT.mkdir(exist_ok=True)

# metas de fecho (prereg onde existe; veredito GO/KILL ao atingir)
N_TARGET = {"reclaim": 20, "a1a2": 15, "cp": 20, "e2_reader": 20, "b_range": 20}


def _jl(p):
    try:
        return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
    except Exception:
        return []


def load_signals():
    """Normaliza cada ledger -> {src, t(entry unix), dir, entry, sl, tgt}. Só sinais ENVIADOS/registados."""
    S = []
    for r in _jl(REPO / "my-strategy/strategies/xau_15m_long/ENTRY_ROUTER/.router_state/reclaim_ledger.jsonl"):
        if r.get("gate_pass") is False:
            continue                                   # suprimidos não foram enviados
        S.append({"src": "reclaim", "t": r.get("etime"), "dir": "LONG",
                  "entry": r.get("entry"), "sl": r.get("sl"), "tgt": r.get("tgt")})
    for r in _jl(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl"):
        S.append({"src": "a1a2", "t": r.get("entry_t"), "dir": "LONG",
                  "entry": r.get("ent"), "sl": r.get("sl"), "tgt": r.get("tgt")})
    for r in _jl(REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/alerted.jsonl"):
        S.append({"src": "cp", "t": r.get("etime") or r.get("entry_t"), "dir": "LONG",
                  "entry": r.get("entry") or r.get("ent"), "sl": r.get("sl"), "tgt": r.get("tgt")})
    for r in _jl(REPO / "alert-bridge/logs/e2_verdicts.jsonl"):
        if not r.get("surfaced"):
            continue                                   # só o que foi notificado
        lv = r.get("levels") or {}
        t = r.get("bar_time")
        S.append({"src": "e2_reader", "t": t, "dir": r.get("direction"),
                  "entry": lv.get("entry"), "sl": lv.get("sl"), "tgt": lv.get("target")})
    return [s for s in S if s["t"] and s["entry"] and s["sl"]]


def resolve(sig, T, H, L, C):
    """SL-first 3R + métricas de SEGURAR. Devolve dict ou None (sem barras)."""
    i0 = next((i for i, t in enumerate(T) if t > sig["t"]), None)
    if i0 is None:
        return None
    e, sl = sig["entry"], sig["sl"]
    long = (sig.get("dir") or "LONG") == "LONG"
    risk = (e - sl) if long else (sl - e)
    if risk <= 0:
        return None
    tgt = sig.get("tgt") or (e + 3 * risk if long else e - 3 * risk)
    out3, mfe, sl_hit = "OPEN", 0.0, False
    for i in range(i0, len(T)):
        fav = (H[i] - e) / risk if long else (e - L[i]) / risk
        if not sl_hit:
            mfe = max(mfe, fav)
        hit_sl = (L[i] <= sl) if long else (H[i] >= sl)
        hit_tg = (H[i] >= tgt) if long else (L[i] <= tgt)
        if out3 == "OPEN":
            if hit_sl:
                out3 = "LOSS"
            elif hit_tg:
                out3 = "WIN"
        if hit_sl:
            sl_hit = True
            break                                       # depois do SL o trade "seguro" morreu
    r3 = {"WIN": 3.0, "LOSS": -1.0}.get(out3)
    # segurar: SL nunca tocado -> marca ao último fecho; tocado -> -1R (mas mfe mostra o que DEU antes)
    r_hold = -1.0 if sl_hit else ((C[-1] - e) / risk if long else (e - C[-1]) / risk)
    return {"out3": out3, "r3": r3, "mfe": round(mfe, 2), "r_hold": round(r_hold, 2), "sl_hit": sl_hit}


def panel():
    bars = sorted(_jl(STORE15), key=lambda x: x["t"])
    T = [b["t"] for b in bars]; H = [b["h"] for b in bars]
    L = [b["l"] for b in bars]; C = [b["c"] for b in bars]
    lines = {}
    unresolved = 0
    for s in load_signals():
        r = resolve(s, T, H, L, C)
        if r is None:
            unresolved += 1
            continue
        lines.setdefault(s["src"], []).append({**s, **r})
    rows = []
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows.append(f"SCOREBOARD FORWARD — {now} Lisboa (janela = store 15M ~30d; SL-first)")
    rows.append("linha       N   W-L-O(3R)   sumR(3R)  streak  |  SEGURAR: mediana MFE  sum R-hold  |  falta p/ N")
    for src, sig in sorted(lines.items()):
        n = len(sig)
        w = sum(1 for x in sig if x["out3"] == "WIN"); l = sum(1 for x in sig if x["out3"] == "LOSS")
        o = n - w - l
        sum3 = sum(x["r3"] for x in sig if x["r3"] is not None)
        stk = 0
        for x in sorted(sig, key=lambda z: z["t"], reverse=True):
            if x["out3"] == "LOSS":
                stk += 1
            elif x["out3"] == "WIN":
                break
        mfes = sorted(x["mfe"] for x in sig)
        med_mfe = mfes[len(mfes) // 2] if mfes else 0
        sumhold = sum(x["r_hold"] for x in sig)
        tgt_n = N_TARGET.get(src, 20)
        rows.append(f"{src:<10} {n:>3}   {w}-{l}-{o:<7} {sum3:>+7.1f}  {stk:>5}L  |  {med_mfe:>10.2f}R  {sumhold:>+9.1f}R  |  {max(0, tgt_n-n)}")
    if unresolved:
        rows.append(f"(unresolved fora da janela do store: {unresolved})")
    rows.append("nota: R-hold = SL nunca tocado marca ao preço atual; SL tocado = -1R. MFE = máximo que o trade DEU antes de morrer.")
    txt = "\n".join(rows)
    (OUT / f"scoreboard_{dt.date.today().isoformat()}.txt").write_text(txt + "\n")
    return txt, lines


if __name__ == "__main__":
    txt, lines = panel()
    print(txt)
    if "--detail" in sys.argv:
        for src, sig in sorted(lines.items()):
            print(f"\n== {src} ==")
            for x in sorted(sig, key=lambda z: z["t"]):
                print(" %s %-5s e%.1f sl%.1f -> %s r3=%s mfe=%.2fR hold=%.2fR" % (
                    dt.datetime.utcfromtimestamp(x["t"]).strftime("%d/%m %H:%M"), x.get("dir"),
                    x["entry"], x["sl"], x["out3"], x["r3"], x["mfe"], x["r_hold"]))
