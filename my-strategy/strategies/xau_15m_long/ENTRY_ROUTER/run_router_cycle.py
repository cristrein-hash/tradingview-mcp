#!/usr/bin/env python3
"""ENTRY ROUTER 15M — ciclo LIVE em modo DRY (Cris 2026-07-19). Roteia, por REGIME MACRO (autoridade
única = Layer1 1D, current_layer1.json escrito pelo regime-engine), qual camada de entry é ELEGÍVEL:
  BEAR  -> Cp (capitulação profunda, já live — não duplica) + RETOMA v1 DRY (higher-low em demanda,
           camada órfã; Cris 2026-07-27): só entrada fresca <=2 barras (zonas as-of deste ciclo = sem a
           circularidade retro apanhada pelo DA), ledger próprio, 0 Telegram.
  RANGE -> engine de B v1.1 via b_forward_score (deep loader gz+store) — DRY: pontua+loga+resolve, 0 Telegram.
  BULL  -> A1/A2 (pullback) — SEM detetor de fundo automático ainda (task #35) -> só regista pendência.
Roteamento (elegibilidade por contexto), NÃO hard-gate/veto. Store-first (bar-store, zero CDP próprio).
Fail-closed. py3.9 stdlib. SEM Telegram nesta versão (dry puro).

CONSOLIDAÇÃO (feedback 2026-07-19): o ramo B DELEGA ao coletor forward existente b_forward_score (fonte
única do ledger, prereg §6, resolve SL-first) — não duplica. Injeta a autoridade fresca no macro antes de
o importar (Conexão 3). O deep loader load_series_live (gz desde o onset + cauda do store) RESOLVE o antigo
'band_truncated' — PARIDADE PROVADA 15/15 byte-a-byte vs in-sample (parity_b_live.py). Go-live do B ainda
exige: prereg N>=20 forward (b_forward_score --status §6) + só então B_PRODUCTION_AUTHORIZED. Dormente BEAR."""
import os, sys, json, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
CORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core")
REV = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
sys.path.insert(0, str(CORE)); sys.path.insert(0, str(CORE / "layer1_service"))
sys.path.insert(0, str(REV))                      # macro_structural_v3 + b_engine_v1 vivem aqui
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
LAYER1 = CORE / "layer1_service/.layer1_state/current_layer1.json"
STATE = HERE / ".router_state"; STATE.mkdir(exist_ok=True)
LOG = STATE / "router_cycle.log"
# NOTA: o ledger forward do B vive em b_forward_score (my-strategy/research/revalidation/b_forward/) —
# fonte única, reusada (feedback consolidar-nao-proliferar 2026-07-19). O router só o alimenta/resolve.
BAR_S = 900
FRESH_BARS = 2
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def read_regime():
    try:
        d = json.loads(LAYER1.read_text())
        return d.get("regime"), d.get("as_of")
    except Exception:
        return None, None


def _inject_fresh_macro():
    """Injeta 1D/DXY frescos nos globais de macro_structural_v3 ANTES de importar o b_forward_score/b_engine
    (que computa _reg no import) — assim o gate/banda do B leem a AUTORIDADE fresca (Conexão 3). Matemática
    intocada. Tem de correr antes do 1º import de b_engine_v1 no processo."""
    import macro_structural_v3 as M
    import layer1_cycle as L1
    xau = L1._merge_xau_1d()
    dxy = L1._jl(REV / "raw_dxy_1d.jsonl")
    if len(xau) < 400 or len(dxy) < 400:
        return False
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    return True


def run_B(rows, out):
    """Ramo RANGE: DELEGA ao coletor forward existente b_forward_score (não duplica ledger — feedback
    consolidar 2026-07-19). Injeta a autoridade fresca -> pontua o último 15M fechado via BF.score (deep
    loader gz+store) -> upsert no forward log SE engine ON -> resolve PENDING. DRY (0 Telegram)."""
    if not _inject_fresh_macro():
        out["b"] = "SKIP: macro fresco insuficiente"; return
    import b_forward_score as BF                              # importa DEPOIS da injeção (b_engine _reg fresco)
    t0 = rows[-1]["t"]; fundo_dt = BF.ds(t0)                  # UTC (casa com BF.ep)
    logged = {r.get("fundo_dt") for r in BF.load_log()}
    if fundo_dt in logged:
        out["b"] = f"já pontuado {fundo_dt}"
    else:
        rec = BF.score(fundo_dt)                              # deep gz+store + b_signal + null
        if rec.get("engine"):
            BF.upsert(rec)
            e = rec.get("entry", {})
            out["b"] = f"B ON -> forward log {fundo_dt} entry {e.get('ent')} SL {e.get('sl')} [{rec.get('status')}]"
        else:
            out["b"] = f"off: {rec.get('reason') or rec.get('status')}"
    out["resolved"] = BF.resolve_pending()                   # árbitro forward: resolve OPEN->WIN/LOSS SL-first


RETOMA_LEDGER = STATE / "retoma_ledger.jsonl"
RECLAIM_LEDGER = STATE / "reclaim_ledger.jsonl"
# RECLAIM Telegram (Cris 2026-08-16): PESSOAL esta semana p/ observar forward; grupo só quando o Cris ativar
# a semana que vem se correr bem. Modos: personal (chat privado/AUTHORIZED_CHAT_ID) | group | off.
RECLAIM_TG = os.environ.get("RECLAIM_TELEGRAM", "personal")


def run_reclaim(rows, out):
    """Motor RETOMADA (reclaim-sequence) — reversão-long que preenche o buraco Cp/A1A2 (Cris 2026-08-15).
    Corre em BEAR E RANGE (o 1D NÃO fecha a direção; reversão-long elegível fora de BULL). Forward-ledger
    próprio (resolve SL-first, como RETOMA/B) — forward=árbitro, NÃO shadow. Group Telegram só com
    RECLAIM_PRODUCTION_AUTHORIZED=1. Só regista fire FRESCO (<=FRESH_BARS). NÃO é edge provado. Fail-closed."""
    import reclaim_engine as RE
    import reclaim_location_gate as RLG              # HTF LOCATION GATE (Cris 2026-08-17 APROVADO)
    dossier, stale = RLG.load_dossier()              # E0 canónico as-of (consumir, não reconstruir)
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    fires = RE.scan(T, O, H, L, C)
    fresh = [f for f in fires if f["etime"] >= T[-1] - FRESH_BARS * BAR_S]
    led = [json.loads(l) for l in RECLAIM_LEDGER.read_text().splitlines() if l.strip()] if RECLAIM_LEDGER.exists() else []
    known = {r.get("reclaim_t") for r in led}
    added = 0; sent = 0; suppressed = 0
    with open(RECLAIM_LEDGER, "a") as fh:
        for f in fresh:
            if f["reclaim_t"] in known:
                continue
            # GATE: enforcing em localização+posição (parte PROVADA); fail-open se dossier stale/ausente
            if dossier is not None and not stale:
                g = RLG.gate(f, dossier)
            else:
                g = {"pass": True, "reason": "fail-open: dossier stale/ausente (não enforça)"}
            rec = dict(f); rec["ts"] = out["ts"]; rec["outcome"] = "OPEN"; rec["regime"] = out.get("regime")
            rec["gate_pass"] = g["pass"]; rec["gate_reason"] = g["reason"]; rec["gate_cluster"] = g.get("cluster")
            rec["gate_pos"] = g.get("pos")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); added += 1; known.add(f["reclaim_t"])
            led.append(rec)
            # ENFORCING: só envia ao Telegram se o gate passar (corta alto-no-ar/topo). Reprovados ficam
            # no ledger (com gate_reason) para auditoria forward, mas NÃO poluem o Telegram.
            if g["pass"] and RECLAIM_TG in ("personal", "group"):
                try:
                    import notify as NF                       # formato único (Cris 2026-08-19)
                    aud = "group" if RECLAIM_TG == "group" else "personal"
                    if NF.signal("ENTRADA", "RECLAIM", "15M", "LONG",
                                 f["entry"], f["sl"], f["tgt"], r=3,
                                 event=f"reclaim-and-go [{f['mode']}] · forward", audience=aud) is True:
                        sent += 1
                except Exception:
                    pass
            elif not g["pass"]:
                suppressed += 1
    # resolve OPEN -> WIN/LOSS SL-first (árbitro forward)
    resolved = 0; chg = False
    for r in led:
        if r.get("outcome") != "OPEN":
            continue
        i0 = next((i for i, t in enumerate(T) if t > r["etime"]), None)
        if i0 is None:
            continue
        for i in range(i0, len(T)):
            if L[i] <= r["sl"]:
                r["outcome"] = "LOSS"; chg = True; resolved += 1; break
            if H[i] >= r["tgt"]:
                r["outcome"] = "WIN"; chg = True; resolved += 1; break
    if chg:
        tmp = RECLAIM_LEDGER.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in led))
        os.replace(tmp, RECLAIM_LEDGER)
    out["reclaim"] = "frescos %d · registados %d · enviados %d · suprimidos-gate %d(%s) · resolvidos %d%s" % (
        len(fresh), added, sent, suppressed, RECLAIM_TG, resolved, " · dossier-stale(fail-open)" if stale else "")


# RETOMA v1 = ARQUIVADA (Cris 2026-08-02, avaliação da semana): prereg REPROVADO (streak 8L > baliza 5;
# painel N=10 1W/9L −6R). A experiência cumpriu o propósito de contraste mecânico-vs-reader; a classe
# estrutural (comprar NO OB) herda no E1 R9 ob_touch_hold. ARQUIVO = não regista candidatos NOVOS;
# a resolução SL-first continua até os OPEN restantes fecharem (2 à data do arquivo).
RETOMA_ARCHIVED = True


def run_retoma(rows, out):
    """Ramo BEAR: RETOMA v1 DRY (prereg RETOMA_ENGINE_V1_PREREG_FORWARD_20260727). Forward-only limpo:
    zonas AS-OF do store agora, e SÓ regista candidato cuja ENTRADA acabou de acontecer (<=2 barras) —
    o passado nunca é varrido com zonas de hoje. Ledger próprio + resolve SL-first. 0 Telegram."""
    import store_reader as SR
    import retoma_engine_v1 as re1
    import cp_engine_live as cp
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    # bubbles do store (mesma fonte do Cp/E0)
    bp = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bubbles_15m.jsonl")
    pairs = [(x["t"], x["plot"]) for x in (json.loads(l) for l in bp.read_text().splitlines() if l.strip())]
    BUYS, SELLS = cp.bubbles_from_pairs(pairs)
    # zonas AS-OF (snapshot do store NESTE ciclo — registadas no ledger p/ auditoria)
    zones, seen = [], set()
    for tf in ("15", "60", "240"):
        pb, _ = SR.pine_boxes(tf)
        for st in (pb or {}).get("studies", []):
            for z in st.get("zones", []):
                k = (round(z["low"], 1), round(z["high"], 1))
                if k not in seen:
                    seen.add(k); zones.append({"low": z["low"], "high": z["high"]})
    t_lo = T[-1] - 96 * BAR_S                                 # fundo recente (<=1 dia)
    led = [json.loads(l) for l in RETOMA_LEDGER.read_text().splitlines() if l.strip()] if RETOMA_LEDGER.exists() else []
    added = 0; cands = []; fresh = []
    if not RETOMA_ARCHIVED:                                   # arquivo: sem candidatos novos, só resolução
        cands = re1.retoma_scan(T, O, H, L, C, BUYS, SELLS, zones, t_lo=t_lo)
        fresh = [c for c in cands if c["etime"] >= T[-1] - FRESH_BARS * BAR_S]
        known = {r.get("fundo_t") for r in led}
        with open(RETOMA_LEDGER, "a") as fh:
            for c in fresh:
                if c["fundo_t"] in known:
                    continue
                rec = dict(c); rec["ts"] = out["ts"]; rec["outcome"] = "OPEN"; rec["zona_asof"] = c["zona"]
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); added += 1
    # resolve OPEN -> WIN/LOSS SL-first (árbitro forward)
    resolved = 0
    if led:
        chg = False
        for r in led:
            if r.get("outcome") != "OPEN":
                continue
            i0 = next((i for i, t in enumerate(T) if t > r["etime"]), None)
            if i0 is None:
                continue
            for i in range(i0, len(T)):
                if L[i] <= r["sl"]:
                    r["outcome"] = "LOSS"; chg = True; resolved += 1; break
                if H[i] >= r["tgt"]:
                    r["outcome"] = "WIN"; chg = True; resolved += 1; break
        if chg:
            tmp = RETOMA_LEDGER.with_suffix(".tmp")
            tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in led))
            os.replace(tmp, RETOMA_LEDGER)
    out["retoma"] = f"cands janela {len(cands)} · frescos {len(fresh)} · registados {added} · resolvidos {resolved}"


def main():
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {"ts": ts, "mode": "DRY"}
    # store-first (barras 15M do bar-store; zero CDP próprio)
    try:
        import store_reader as SR
        if not SR.fresh("15", mult=5):
            out["status"] = "SKIP: store 15M não-fresco (no-op)"; _log(out); print(json.dumps(out)); return
        rows = SR.bars("15")
    except Exception as e:
        out["status"] = f"SKIP: store indisponível ({type(e).__name__})"; _log(out); print(json.dumps(out)); return
    if not rows or len(rows) < 60:
        out["status"] = f"SKIP: 15M insuficiente (n={len(rows) if rows else 0})"; _log(out); print(json.dumps(out)); return
    regime, as_of = read_regime()
    out.update({"regime": regime, "as_of": as_of, "buf_bars": len(rows), "last_bar": iso(rows[-1]["t"])})
    if regime == "RANGE":
        out["route"] = "RANGE -> B (forward) + RECLAIM (reversão-long, 1D=contexto não veto)"
        run_B(rows, out)
        try:
            run_reclaim(rows, out)
        except Exception as e:
            out["reclaim"] = f"erro {type(e).__name__}:{str(e)[:60]}"
    elif regime == "BEAR":
        out["route"] = "BEAR -> Cp (live) + RETOMA v1 dry + RECLAIM (reversão-long, 1D=contexto não veto)"
        try:
            run_retoma(rows, out)
        except Exception as e:
            out["retoma"] = f"erro {type(e).__name__}:{str(e)[:60]}"
        try:
            run_reclaim(rows, out)
        except Exception as e:
            out["reclaim"] = f"erro {type(e).__name__}:{str(e)[:60]}"
    elif regime == "BULL":
        out["route"] = "BULL -> A1/A2 pendente detetor de fundo (task #35)"
    else:
        out["route"] = f"regime desconhecido ({regime})"
    out["status"] = "OK"
    _log(out); print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
