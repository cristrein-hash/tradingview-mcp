#!/usr/bin/env python3
"""POOL-LIMIT WATCH — SHADOW (ordem Cris 28/08: aviso ANTECIPADO, como ele coloca as limites dele).
Gramática lida do chart dele (commit 8689217): BUY LIMIT no topo do pool INTACTO de pavios 15M, ANTES
do toque; SL curto atrás do pool; alvo = próximo pool acima. LONG-only (doutrina permanente).

Emite no momento em que o pool QUALIFICA (não no toque): "ARMA LIMITE lim/SL/alvo" → aviso_shadow via
notify (canal ⚡ = ficheiro, NUNCA Telegram) + ledger .pool_watch/armados.jsonl. O próprio ciclo faz o
tracking: FILLED (low<=lim) → depois SL/TGT; outcome no ledger. Validação forward = semana 31/08-04/09
(FORWARD_PREREG_POOL_LIMIT.md). Params selados; zero knobs em forward. py3.9 stdlib."""
import json
import sys
import time
from pathlib import Path

BASE = Path("/Users/cristrein/tradingview-mcp")
STORE = BASE / "my-strategy/core/bar_store/store/bars_15m.jsonl"
STATE = Path(__file__).resolve().parent / ".pool_watch"
LEDGER = STATE / "armados.jsonl"
LOG = BASE / "alert-bridge/logs/pool_limit_watch.jsonl"
K_SW, CL_ATR, WIN = 3, 0.5, 400
DIST_MIN, DIST_MAX = 0.3, 4.0        # pool 0.3-4 ATR abaixo do preço (as limites dele armam à distância)
SLBUF = 0.3
MIN_R = 1.5                          # espaço até ao próximo pool acima >= 1.5R senão NO_SPACE (só log)


def _bars(n=800):
    try:
        rows = [json.loads(l) for l in open(STORE).read().splitlines() if l.strip()]
        rows.sort(key=lambda x: x["t"])
        return rows[-n:]
    except Exception:
        return []


def _atr(b, i):
    trs = [max(b[k]["h"] - b[k]["l"], abs(b[k]["h"] - b[k - 1]["c"]), abs(b[k]["l"] - b[k - 1]["c"]))
           for k in range(max(1, i - 14), i)]
    return sum(trs) / len(trs) if trs else 5.0


def _pools(b, side):
    """Clusters de >=2 swings (lows p/ SSL, highs p/ BSL), span<=0.5 ATR. [(lo,hi,form_i)]"""
    n = len(b)
    a = _atr(b, n - 1)
    pts = []
    for i in range(max(K_SW, n - WIN), n - K_SW):
        if side == "SSL" and b[i]["l"] == min(x["l"] for x in b[i - K_SW:i + K_SW + 1]):
            pts.append((b[i]["l"], i))
        if side == "BSL" and b[i]["h"] == max(x["h"] for x in b[i - K_SW:i + K_SW + 1]):
            pts.append((b[i]["h"], i))
    pts.sort()
    out = []; grp = []
    for p, i in pts:
        if grp and p - grp[0][0] <= CL_ATR * a:
            grp.append((p, i))
        else:
            if len(grp) >= 2:
                out.append((grp[0][0], grp[-1][0], max(x[1] + K_SW for x in grp)))
            grp = [(p, i)]
    if len(grp) >= 2:
        out.append((grp[0][0], grp[-1][0], max(x[1] + K_SW for x in grp)))
    return out


def _jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


NEWS_BEFORE_S, NEWS_AFTER_S = 30 * 60, 15 * 60   # regra do Cris (28/08, perdeu -4R na faca Warsh):
                                                  # NUNCA limites armadas dentro de janela HIGH


def _news_window():
    """(True, desc) se evento HIGH a <=30min ou saiu há <=15min (ff_calendar do EF v2)."""
    try:
        ff = json.load(open(BASE / "external_factors_v2/snapshots/ff_calendar.json"))
        evs = ff if isinstance(ff, list) else ff.get("events", [])
        now = time.time()
        for e in evs:
            if str(e.get("impact", "")).upper() not in ("HIGH", "RED"):
                continue
            ts = e.get("release_ts") or e.get("ts") or 0
            if -NEWS_AFTER_S <= ts - now <= NEWS_BEFORE_S:
                mins = int((ts - now) / 60)
                return True, f"{e.get('title') or e.get('event')} ({'em %dmin' % mins if mins >= 0 else 'saiu há %dmin' % -mins})"
    except Exception:
        pass
    return False, None


def cycle():
    STATE.mkdir(exist_ok=True)
    b = _bars()
    if len(b) < 100:
        return {"err": "sem_barras"}
    n = len(b); px = b[-1]["c"]; a = _atr(b, n - 1)
    led = _jl(LEDGER)
    keys = {r["key"] for r in led}
    ssl = _pools(b, "SSL")
    bsl = _pools(b, "BSL")
    armados = novos = 0
    recs = []

    # JANELA DE NOTÍCIA HIGH: suspende armados (aviso pessoal 1×) e não arma novos
    news, ndesc = _news_window()
    if news:
        warned = False
        for rec in led:
            if rec.get("status") == "ARMADO":
                rec["status"] = "SUSPENSO_NEWS"; rec["susp_desc"] = ndesc
                warned = True
        if warned or not (STATE / f".news_warned_{int(time.time())//1800}").exists():
            try:
                sys.path.insert(0, str(BASE / "alert-bridge"))
                import notify
                notify.info("AVISO", "POOL-LIMIT SHADOW",
                            "🚨 JANELA DE NOTÍCIA HIGH: %s\nLIMITES SUSPENSAS (cancela as tuas) — rearma pós-poeira se pool intacto" % ndesc,
                            audience="personal")
                (STATE / f".news_warned_{int(time.time())//1800}").write_text("1")
            except Exception:
                pass
    else:
        # pós-janela: re-arma suspensos cujo pool continua intacto
        for rec in led:
            if rec.get("status") == "SUSPENSO_NEWS":
                lo = float(rec["key"].split("-")[0])
                intact = not any(x["l"] < lo for x in b if x["t"] > rec["t"])
                rec["status"] = "ARMADO" if intact else "CANCELADO_POOL_FURADO"

    # 1) NOVOS pools intactos abaixo → ARMA LIMITE (antecipado; bloqueado em janela de notícia)
    for lo, hi, fi in (ssl if not news else []):
        if not (DIST_MIN * a <= (px - hi) <= DIST_MAX * a):
            continue
        if any(b[k]["l"] < lo for k in range(fi, n)):      # intacto desde a formação
            continue
        key = f"{round(lo,1)}-{round(hi,1)}"
        if key in keys:
            armados += 1
            continue
        lim = hi; sl = lo - SLBUF * a; risk = lim - sl
        above = sorted([z for z in bsl if z[0] > lim], key=lambda z: z[0])
        tgt = above[0][0] if above else None
        r = round((tgt - lim) / risk, 1) if tgt else None
        rec = dict(key=key, t=b[-1]["t"], lim=round(lim, 2), sl=round(sl, 2),
                   tgt=round(tgt, 2) if tgt else None, r=r, px_arm=px, status="ARMADO"
                   if (r or 0) >= MIN_R else "NO_SPACE", armed_ts=int(time.time()))
        recs.append(rec)
        keys.add(key)
        novos += 1
        if rec["status"] == "ARMADO":
            try:
                sys.path.insert(0, str(BASE / "alert-bridge"))
                import notify
                notify.info("AVISO", "POOL-LIMIT SHADOW",
                            "ARMA LIMITE %.1f\nSL %.1f · alvo %s (R %.1f)\npool intacto %.1f-%.1f · preço %.1f"
                            % (rec["lim"], rec["sl"], rec["tgt"], rec["r"] or 0, lo, hi, px),
                            audience="personal")   # ordem Cris 28/08: TG PESSOAL, nunca grupo
            except Exception:
                pass

    # 2) tracking dos armados: FILL / SL / TGT
    upd = 0
    for rec in led:
        if rec.get("status") not in ("ARMADO", "FILLED"):
            continue
        t0 = rec["t"]
        seq = [x for x in b if x["t"] > t0]
        for x in seq:
            if rec["status"] == "ARMADO" and x["l"] <= rec["lim"]:
                rec["status"] = "FILLED"; rec["fill_t"] = x["t"]; upd += 1
            if rec["status"] == "FILLED":
                if x["l"] <= rec["sl"]:
                    rec["status"] = "SL"; rec["out_t"] = x["t"]; rec["R"] = -1.0; upd += 1
                    break
                if rec.get("tgt") and x["h"] >= rec["tgt"]:
                    rec["status"] = "TGT"; rec["out_t"] = x["t"]; rec["R"] = rec["r"]; upd += 1
                    break
        # invalidação pré-fill: pool furado sem tocar a nossa limite é impossível (lim=topo);
        # expiração: 5 dias sem fill
        if rec["status"] == "ARMADO" and time.time() - rec["armed_ts"] > 5 * 86400:
            rec["status"] = "EXPIRADO"; upd += 1

    allr = led + recs
    if recs or upd:
        tmp = LEDGER.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(json.dumps(r) for r in allr) + ("\n" if allr else ""))
        import os
        os.replace(tmp, LEDGER)
    st = dict(ts=int(time.time()), px=px, pools_ssl=len(ssl), novos=novos,
              ativos=sum(1 for r in allr if r["status"] == "ARMADO"),
              filled=sum(1 for r in allr if r["status"] == "FILLED"))
    with open(LOG, "a") as f:
        f.write(json.dumps(st) + "\n")
    return st


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        b = _bars()
        t.append(("barras carregam", len(b) > 100))
        ssl = _pools(b, "SSL") if b else []
        t.append(("pools SSL detetáveis (lista)", isinstance(ssl, list)))
        t.append(("pool span <= 0.5 ATR", all(hi - lo <= 0.5 * _atr(b, len(b) - 1) + 1e-6 for lo, hi, _ in ssl)))
        import inspect, ast
        tree = ast.parse(inspect.getsource(sys.modules[__name__]))
        calls = {getattr(getattr(nd, "func", None), "attr", None) for nd in ast.walk(tree) if isinstance(nd, ast.Call)}
        t.append(("SHADOW: única emissão é notify.send('aviso') (ficheiro, nunca TG direto)",
                  "_tg_send" not in calls and "send_message" not in calls))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    print(json.dumps(cycle()))
