#!/usr/bin/env python3
"""Runtime XAU-only L1 (Production v2) — orquestração híbrida.

Lê o chart XAU 4H via MCP (tv_read_adapter), aplica o gate de exaustão RSI já existente,
e — só para candidato OPERACIONAL aprovado da L1 — dispara candidate notification Telegram.
A AUTORIDADE do gate-base é o scanner; este runtime ORQUESTRA (regime/precondição, dedup,
journal, notify). NÃO duplica a lógica do gate-base.

Modos: --dry-run (default) | --once | --send-telegram (opt-in real). XAU-only. Sem scheduler,
sem daemon, sem LaunchAgent, sem broker, sem MCP de gestão de trade.

Regime D-1 = regime_L1_v4 (fonte EXPLÍCITA nova; regime legacy v1 B/regime_B_v3 = IRRECUPERÁVEL,
não-autoridade). Se o feed regime_L1_v4 não cobrir D-1 recente → no_candidate/regime_l1_v4_stale.
Com regime_L1_v4 fresco, avalia normalmente (regime != BULL → no_candidate; BULL → segue gate).
"""
import json, sys, argparse, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
def _repo(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]
REPO = _repo(HERE)
CORE = REPO / "my-strategy" / "core"
sys.path.insert(0, str(CORE))
from group_model_xau import GROUPS, telegram_allowed  # noqa: E402

# Regime D-1 = regime_L1_v4 (fonte EXPLÍCITA nova). O regime legacy v1 B/regime_B_v3 foi
# declarado IRRECUPERÁVEL (ver core/regime/README.md) e NÃO é mais autoridade operacional.
REGIME_L1V4 = REPO / "my-strategy/core/regime_l1/regime_l1_v4_classifications.jsonl"
sys.path.insert(0, str(REPO / "my-strategy/core/regime_l1"))
from regime_l1_v4 import latest_state_before  # noqa: E402
CONSUMER = "L1_EMA21_CONTINUATION"
GROUP = "XAU_240"
RSI_VS_MA_THR = -9.35


def regime_d1_state(bar_time_unix):
    """Lê regime_L1_v4 p/ a última classificação ANTES de bar_time (D-1 causal).
    Retorna (state|None, stale: bool). stale se o feed não cobrir D-1 recente."""
    if bar_time_unix is None or not REGIME_L1V4.exists():
        return None, True
    cls = [json.loads(l) for l in REGIME_L1V4.read_text().splitlines() if l.strip()]
    return latest_state_before(cls, bar_time_unix)


def signal_hash(symbol, tf, ts_iso):
    base = symbol.split(":")[-1]
    key = f"{ts_iso}|{base}|{tf}|L1_EMA21_CONTINUATION|continuation"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def already_sent(dedup_path, sh):
    if not dedup_path or not Path(dedup_path).exists():
        return False
    return any(line.strip() == sh for line in Path(dedup_path).read_text().splitlines())


def mark_sent(dedup_path, sh):
    if dedup_path:
        with open(dedup_path, "a") as f:
            f.write(sh + "\n")


def evaluate(snapshot):
    """Decide o estado L1 a partir do snapshot live. Regime é PRÉ-CONDIÇÃO.
    Retorna dict com state/operational/exhaustion_gate/signal_hash/reason."""
    sym = snapshot["symbol"]; tf = snapshot["timeframe"]
    bt = snapshot.get("bar_time")
    ts_iso = datetime.utcfromtimestamp(bt).isoformat() if bt else "?"
    rvm = snapshot.get("rsi_vs_ma")
    sh = signal_hash(sym, tf, ts_iso)
    base = {"symbol": sym, "timeframe": tf, "candidate_timestamp": ts_iso,
            "signal_hash": sh, "strategy": "L1 · EMA21 CONTINUATION",
            "suite": "XAU 4H LONG — CONTINUATION", "strategy_route": CONSUMER,
            "rsi_vs_ma": round(rvm, 2) if rvm is not None else None}
    # PRÉ-CONDIÇÃO: regime D-1
    reg, stale = regime_d1_state(bt)
    if reg is None or stale:
        return {**base, "operational": False, "exhaustion_gate": None,
                "state": "no_candidate", "reason": f"regime_l1_v4_stale(last<{reg}>,stale={stale})"}
    if reg != "BULL":
        return {**base, "operational": False, "exhaustion_gate": None,
                "state": "no_candidate", "reason": f"regime_d1={reg}_not_BULL"}
    # GATE de exaustão RSI-only (faithful ao scanner)
    eg = (rvm is not None and round(rvm, 2) <= RSI_VS_MA_THR)
    if eg:
        return {**base, "operational": False, "exhaustion_gate": True, "state": "blocked_exhaustion"}
    # NOTA: a confirmação completa da regra-base (EMA/SMA/BOS/OB/F5) é AUTORIDADE do scanner.
    # Este runtime live confirma regime+RSI gate; a regra-base estrutural live entra quando
    # o snapshot trouxer histórico suficiente computado (próximo bloco). Por ora, sem regra-base
    # confirmada, marcamos needs_base_confirmation (NÃO operacional, sem Telegram) — honesto.
    return {**base, "operational": False, "exhaustion_gate": False,
            "state": "needs_base_confirmation",
            "reason": "regime=BULL + RSI gate ok; regra-base estrutural live pendente (autoridade=scanner)"}


def notify(cand, send, dedup_path):
    """Dispara candidate notification via telegram_notify.py se operacional+allowlist+não-dedup."""
    sh = cand["signal_hash"]
    if not cand.get("operational"):
        return {"sent": False, "skip": f"não-operacional ({cand.get('state')})"}
    if not telegram_allowed(GROUP, CONSUMER):
        return {"sent": False, "skip": "consumer fora da allowlist do grupo"}
    if already_sent(dedup_path, sh):
        return {"sent": False, "skip": f"dedup: signal_hash {sh} já enviado"}
    notifier = HERE / "telegram_notify.py"
    args = [sys.executable, str(notifier)] + (["--send"] if send else [])
    r = subprocess.run(args, input=json.dumps(cand), capture_output=True, text=True)
    sent = send and "SENT=True" in r.stdout
    if sent:
        mark_sent(dedup_path, sh)
    return {"sent": sent, "stdout": r.stdout.strip(), "dry_run": not send}


def main():
    ap = argparse.ArgumentParser(description="Runtime XAU-only L1 (hybrid MCP read).")
    ap.add_argument("--once", action="store_true", help="executa 1 ciclo e sai")
    ap.add_argument("--send-telegram", action="store_true", help="envio real (opt-in; default dry-run)")
    ap.add_argument("--dedup-path", default=None, help="arquivo de dedup de signal_hash (1 envio/sinal)")
    ap.add_argument("--snapshot-file", default=None, help="(teste) lê snapshot de arquivo em vez do MCP live")
    args = ap.parse_args()

    if args.snapshot_file:                       # modo teste: snapshot injetado
        snap = json.load(open(args.snapshot_file))
    else:                                        # modo live: lê o chart via MCP
        from tv_read_adapter import read_xau_snapshot
        snap = read_xau_snapshot("240")
    if not snap.get("ok") and "candidate" not in snap and "operational" not in snap:
        print(json.dumps({"runtime": "HARD_STOP", "reason": snap.get("hard_stop", snap)}, ensure_ascii=False, indent=2))
        return 2

    # snapshot do adapter -> evaluate; OU candidato já pronto (teste consumindo scanner)
    if "state" in snap and "signal_hash" in snap:   # já é um candidato (ex.: saída do scanner)
        cand = snap
    else:
        cand = evaluate(snap)

    res = notify(cand, send=args.send_telegram, dedup_path=args.dedup_path)
    out = {"group": GROUP, "consumer": CONSUMER, "candidate": cand, "notify": res,
           "telegram_real": bool(args.send_telegram)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
