"""Forward Outcome Layer — MVP Fase 2: match live signals <-> candidatos L1 (read-only, SEM R).

Pergunta: quando a L1 emite (ou emitiria) um candidato OPERACIONAL, conseguimos localizar
no event store live os sinais/indicadores correspondentes na mesma janela de bar/símbolo/tf?

XAU-only, L1-only, read-only. NÃO calcula R, NÃO compara backtest, NÃO envia Telegram,
NÃO muta event store/journal/runtime.

Identidades (SPEC §B) — NUNCA confundir:
  - `signal_hash` (log L1 / runtime) = identidade ESTRATÉGICA do candidato.
  - `ingestion_hash` (event store) = identidade do EVENTO BRUTO.
  O matching é por bar/símbolo/tf/janela temporal — os dois hashes vivem em namespaces
  diferentes e NÃO são comparados entre si (só exibidos como rótulos).

Fontes (read-only):
  - candidatos forward L1: `.runtime_state/l1_cycle.log` (saída persistente do runner) e,
    opcionalmente, um journal JSONL via --journal-path (signal_emitted events).
  - live signals: event store via ingest_live_signals (XAU, timeframe 240).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import timedelta

import ingest_live_signals as ing

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# janela tolerante de match: um bar 4H (240 min) + folga de 10 min (atraso de ingestão/cron).
MATCH_WINDOW = timedelta(minutes=240 + 10)

DEFAULT_L1_LOG = os.path.join(
    ing._repo_root(), "my-strategy", "strategies", "xau_4h_long", "continuation",
    "L1_EMA21_CONTINUATION", ".runtime_state", "l1_cycle.log",
)


def load_l1_candidates(log_path=None, journal_path=None):
    """Carrega registros forward da L1 (read-only).

    Retorna (evaluations, operational, meta). `operational` = subconjunto com
    state == 'operational_candidate'. Cada registro: {ts_cycle, state, signal_hash,
    telegram_real, notify_sent, bar_ts(None se não persistido), source}.
    """
    log_path = log_path or DEFAULT_L1_LOG
    evals = []
    parse_errors = 0
    read_paths = []

    if os.path.isfile(log_path):
        read_paths.append(log_path)
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                evals.append({
                    "ts_cycle": r.get("ts"),
                    "ts_cycle_dt": ing._parse_ts(r.get("ts")),
                    "state": r.get("state"),
                    "signal_hash": r.get("signal_hash"),  # ESTRATÉGICO
                    "telegram_real": r.get("telegram_real"),
                    "notify_sent": r.get("notify_sent"),
                    "bar_ts": r.get("candidate_timestamp"),  # não persistido hoje -> None
                    "source": "l1_cycle.log",
                })

    # journal opcional (signal_emitted events) — só se path fornecido e existir
    if journal_path and os.path.isfile(journal_path):
        read_paths.append(journal_path)
        with open(journal_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                if r.get("event_type") != "signal_emitted":
                    continue
                cand = r.get("candidate", {}) if isinstance(r.get("candidate"), dict) else {}
                bar_ts = cand.get("candidate_timestamp") or r.get("candidate_timestamp")
                evals.append({
                    "ts_cycle": r.get("emitted_at") or r.get("ts"),
                    "ts_cycle_dt": ing._parse_ts(r.get("emitted_at") or r.get("ts")),
                    "state": cand.get("state") or r.get("state") or "signal_emitted",
                    "signal_hash": r.get("signal_hash") or cand.get("signal_hash"),
                    "telegram_real": r.get("signal_sent"),
                    "notify_sent": r.get("signal_sent"),
                    "bar_ts": bar_ts,
                    "source": "journal",
                })

    operational = [e for e in evals if e["state"] == "operational_candidate"]
    meta = {"log_path": log_path, "journal_path": journal_path,
            "read_paths": read_paths, "parse_errors": parse_errors,
            "total_evaluations": len(evals)}
    return evals, operational, meta


def load_xau_240(event_store=None):
    """Live signals XAU timeframe 240 (read-only via ingest_live_signals)."""
    recs, meta = ing.load_signals(event_store, symbol="XAUUSD")
    xau240 = [r for r in recs if (r.get("timeframe") == "240")]
    return xau240, meta


def _match_anchor(cand):
    """Âncora temporal do candidato: bar_ts se existir, senão ts do ciclo (proxy documentado)."""
    if cand.get("bar_ts"):
        dt = ing._parse_ts(cand["bar_ts"])
        if dt:
            return dt, "bar_ts"
    return cand.get("ts_cycle_dt"), "cycle_ts_proxy"


def match(operational, xau240):
    """Classifica cada candidato operacional vs live signals XAU 240 na janela."""
    results = []
    matched_signal_ids = set()
    for cand in operational:
        anchor, anchor_kind = _match_anchor(cand)
        if anchor is None:
            results.append({"candidate": cand, "classification": "candidate_missing_fields",
                            "matches": [], "anchor_kind": anchor_kind})
            continue
        lo = anchor - MATCH_WINDOW
        hits = [s for s in xau240 if s["ts_signal_dt"] and lo <= s["ts_signal_dt"] <= anchor]
        for s in hits:
            matched_signal_ids.add(id(s))
        if not hits:
            cls = "unmatched_no_live_signal"
        else:
            exact = any(s["ts_signal_dt"] == anchor for s in hits)
            cls = "matched_exact_bar" if exact else "matched_within_window"
        results.append({"candidate": cand, "classification": cls,
                        "matches": [{"ts_signal": s["ts_signal"], "indicator": s["indicator_name"],
                                      "signal_type": s["signal_type"], "ingestion_hash": s["ingestion_hash"]}
                                     for s in hits[:10]],
                        "anchor": anchor.isoformat(), "anchor_kind": anchor_kind})
    live_only = [s for s in xau240 if id(s) not in matched_signal_ids]
    return results, live_only


def compute(operational, xau240, results, live_only, l1_meta, es_meta):
    import collections
    by_class = collections.Counter(r["classification"] for r in results)
    anchor_kinds = collections.Counter(r.get("anchor_kind") for r in results)
    by_ind = collections.Counter(s.get("indicator_name") or "(vazio)" for s in xau240)
    by_prov = collections.Counter(s.get("provider") or "(nenhum)" for s in xau240)
    by_state = collections.Counter(e["state"] for e in (operational or []))
    dts = [s["ts_signal_dt"] for s in xau240 if s["ts_signal_dt"]]
    insufficient = len(operational) == 0
    return {
        "verdict": "insufficient_forward_sample" if insufficient else "matched_some",
        "l1": {"total_evaluations": l1_meta["total_evaluations"],
                "operational_candidates": len(operational),
                "read_paths": l1_meta["read_paths"], "parse_errors": l1_meta["parse_errors"]},
        "xau240_live": {"n": len(xau240),
                          "range": {"min": min(dts).isoformat() if dts else None,
                                     "max": max(dts).isoformat() if dts else None},
                          "by_indicator": dict(by_ind.most_common()),
                          "by_provider": dict(by_prov.most_common())},
        "match_classification": dict(by_class),
        "timestamp_anchor": {
            "candidates_with_candidate_timestamp": sum(1 for c in operational if c.get("bar_ts")),
            "candidates_using_cycle_proxy": sum(1 for c in operational if not c.get("bar_ts")),
            "anchor_kinds_used": {k: v for k, v in anchor_kinds.items() if k},
        },
        "live_signal_no_strategy_candidate": len(live_only),
        "match_window_minutes": int(MATCH_WINDOW.total_seconds() // 60),
        "event_store_total_lines": es_meta["total_lines"],
    }


def render_md(m, evals_states, evals_bar_ts):
    L = []
    L.append("# Forward Candidate Matching — MVP Fase 2 (read-only, SEM R)")
    L.append("")
    L.append("> Junta candidatos OPERACIONAIS da L1 com live signals XAU 240 do event store, por "
             "bar/símbolo/tf/janela. **Sem R, sem backtest, sem Telegram.** `signal_hash` (estratégico) "
             "e `ingestion_hash` (evento) NÃO são comparados entre si.")
    L.append("")
    L.append(f"## Veredito: `{m['verdict']}`")
    if m["verdict"] == "insufficient_forward_sample":
        L.append("- **`no_l1_candidates_yet`** — a L1 ainda não emitiu candidato OPERACIONAL forward "
                 "(regime D-1 BEAR → todos os ciclos = `no_candidate`). Sem amostra para matar/confirmar match.")
        L.append("- O lado live está disponível e é mostrado abaixo (todos contam como "
                 "`live_signal_no_strategy_candidate`).")
    L.append("")
    L.append("## L1 (lado estratégico)")
    L.append(f"- Ciclos/avaliações lidos: **{m['l1']['total_evaluations']}**  ·  "
             f"candidatos OPERACIONAIS: **{m['l1']['operational_candidates']}**")
    L.append(f"- Estados vistos: {evals_states}")
    L.append(f"- Fontes lidas: {', '.join(os.path.basename(p) for p in m['l1']['read_paths']) or '(nenhuma)'}  ·  "
             f"parse errors: {m['l1']['parse_errors']}")
    L.append("")
    x = m["xau240_live"]
    L.append("## XAU 240 (lado live / event store)")
    L.append(f"- Sinais XAU tf=240: **{x['n']}**  ·  range {x['range']['min']} → {x['range']['max']}")
    L.append("- Por indicador:")
    L.append("| indicador | sinais |")
    L.append("|---|---|")
    for k, v in x["by_indicator"].items():
        L.append(f"| {k} | {v} |")
    L.append("- Por provider:")
    L.append("| provider | sinais |")
    L.append("|---|---|")
    for k, v in x["by_provider"].items():
        L.append(f"| {k} | {v} |")
    L.append("")
    L.append("## Classificação de match")
    L.append(f"- Janela tolerante: **{m['match_window_minutes']} min** (1 bar 4H + 10 min de folga), "
             "ancorada no `bar_ts` se persistido, senão no `ts` do ciclo (proxy documentado).")
    L.append("| classe | n |")
    L.append("|---|---|")
    for k, v in (m["match_classification"] or {"(sem candidatos)": 0}).items():
        L.append(f"| {k} | {v} |")
    L.append(f"- `live_signal_no_strategy_candidate`: **{m['live_signal_no_strategy_candidate']}**")
    ta = m["timestamp_anchor"]
    L.append("")
    L.append("## Qualidade do timestamp de match")
    L.append(f"- Candidatos operacionais com **`candidate_timestamp` (bar exato):** {ta['candidates_with_candidate_timestamp']}  ·  "
             f"usando **fallback `cycle_timestamp` (proxy):** {ta['candidates_using_cycle_proxy']}")
    L.append(f"- Tipos de âncora usados: {ta['anchor_kinds_used'] or '(nenhum — sem candidatos operacionais)'}")
    L.append(f"- Cobertura de `candidate_timestamp` nas avaliações L1 lidas: **{evals_bar_ts}/{m['l1']['total_evaluations']}** "
             "(campo persistido a partir de 2026-06-16; ciclos antigos podem não tê-lo).")
    L.append("")
    L.append("## Limitações")
    L.append("- **Amostra forward insuficiente:** 0 candidatos operacionais (regime BEAR). Match real só "
             "será exercitado em janela BULL.")
    L.append("- **`bar_ts` não persistido:** o `l1_cycle.log` grava o `ts` do ciclo, não o timestamp do bar "
             "do candidato. Quando houver candidatos, recomenda-se estender o log com `candidate_timestamp` "
             "(mudança de runtime — fora do escopo deste bloco read-only).")
    L.append("- **Log raso/rotacionável:** histórico forward começa com o scheduler recém-ativado; o log rotaciona.")
    L.append("- **Sem R / sem edge:** este bloco só localiza correspondência operacional, não mede resultado.")
    L.append("")
    L.append("_Gerado por `match_candidates.py` (read-only). Não altera event store, journal nem runtime._")
    return "\n".join(L)


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Forward candidate matching (read-only, no R)")
    ap.add_argument("--path", default=None, help="event store path")
    ap.add_argument("--l1-log", default=None, help="l1_cycle.log path")
    ap.add_argument("--journal-path", default=None, help="optional L1 journal jsonl (signal_emitted)")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    es = args.path or ing.default_event_store()
    if not os.path.isfile(es):
        raise SystemExit(f"HARD STOP: event store não encontrado: {es}")

    evals, operational, l1_meta = load_l1_candidates(args.l1_log, args.journal_path)
    import collections
    evals_states = dict(collections.Counter(e["state"] for e in evals))
    evals_bar_ts = sum(1 for e in evals if e.get("bar_ts"))
    xau240, es_meta = load_xau_240(es)
    results, live_only = match(operational, xau240)
    m = compute(operational, xau240, results, live_only, l1_meta, es_meta)
    md = render_md(m, evals_states, evals_bar_ts)

    if args.no_write:
        print(md)
        return
    os.makedirs(REPORTS_DIR, exist_ok=True)
    md_path = os.path.join(REPORTS_DIR, "candidate_match_latest.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    out = {"md": md_path}
    if args.json:
        js_path = os.path.join(REPORTS_DIR, "candidate_match_latest.json")
        with open(js_path, "w", encoding="utf-8") as fh:
            json.dump({"metrics": m, "evals_states": evals_states,
                        "results": results}, fh, default=str, indent=2)
        out["json"] = js_path
    print(json.dumps({"written": out, "verdict": m["verdict"],
                      "operational_candidates": m["l1"]["operational_candidates"],
                      "xau240_live": m["xau240_live"]["n"]}, default=str, indent=2))


if __name__ == "__main__":
    _main()
