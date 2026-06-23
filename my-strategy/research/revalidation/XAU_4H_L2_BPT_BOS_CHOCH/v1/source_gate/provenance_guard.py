#!/usr/bin/env python3
"""PROVENANCE GUARD — constricao ESTRUTURAL (substitui memoria passiva, que falhou 2x em 2026-06-23).

Regra mecanica: NENHUM signal pode ficar com status bloqueado (UNKNOWN_BLOCKED / UNMAPPED_DERIVED_DISALLOWED /
DERIVED_ARTIFACT_BUG) se JA EXISTE extracao/derivacao dele no repo. O guard faz uma BUSCA REAL (codigo extract_*
+ arquivos de dados com a chave/coluna) e FALHA (exit 1) se achar evidencia — apontando o arquivo. Assim o autor
e OBRIGADO a confrontar a extracao existente antes de declarar 'blocked'. Isto teria pego o erro do dia: marcar
svp_poc_val_vah=UNKNOWN_BLOCKED enquanto svp_bars.jsonl + extract_svp.py + DSPA F6 ja existiam e estavam validados.

Importado e chamado por check_reader_sources.py. Rodavel standalone: python3 source_gate/provenance_guard.py
Verified at: 2026-06-23."""
import os, glob, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(V1, "..", "..", "..", ".."))
# So UNKNOWN_BLOCKED: a alegacao perigosa = "ausente/nao-serializado/nao-reconstruivel". UNMAPPED_DERIVED_DISALLOWED
# ja reconhece que existe como derivado (disallow proposital ate RAW-map), entao nao e o alvo deste guard.
BLOCKED_STATUS = {"UNKNOWN_BLOCKED"}

# Tokens ESPECIFICOS por signal (curados p/ evitar match generico tipo 'val'/'vp').
# Cada token: substring que, se aparecer como CHAVE de dado ou em codigo de extracao, prova que a fonte NAO esta bloqueada.
SIGNAL_KEYWORDS = {
    "svp_poc_val_vah": ["dist_poc", "svp_state", "svp_bars", "above_value", "below_value", "value_area", "f6_svp"],
    "custom_ob_boxes": ["custom ob detector", "sup_cat", "dist_supply", "supply_demand_raw_mapped"],
    "smc_boxes_lines": ["smc_box", "smc_line", "order_block_box", "smc_order_block"],
    "acceptance": ["f6_svp_state", "svp_state", "acceptance_state"],
    "pol_cat": ["pol_cat"],
    "bubbles_recent_derived": ["bubble_cluster_summary", "market_order_bubbles"],
}
# signals derivado-bug: a extracao RAW CORRETA conta como evidencia de que o bloqueio do DERIVADO e ok,
# entao excluimos os *_derived da regra (o bloqueio deles e proposital: usar o RAW). So nao-derived sao checados.
SKIP_SIGNALS = {"nas_recent_derived", "smc_recent_derived", "bubbles_recent_derived"}

DATA_GLOBS = [os.path.join(V1, "results", "**", "*.jsonl"), os.path.join(V1, "results", "**", "*.csv"),
              os.path.join(V1, "repro_recovery", "*.jsonl"), os.path.join(V1, "repro_recovery", "*.csv"),
              os.path.join(V1, "results", "*.jsonl"), os.path.join(V1, "results", "*.csv")]
CODE_GLOBS = [os.path.join(V1, "*.py"), os.path.join(V1, "**", "*.py")]


def _data_head(fp, n=2):
    try:
        with open(fp, errors="ignore") as f:
            return "\n".join(f.readline() for _ in range(n)).lower()
    except Exception:
        return ""


def search_extraction(keywords):
    """Busca evidencia de extracao p/ os keywords. Retorna lista (kw, path, kind)."""
    hits, seen = [], set()
    kws = [k.lower() for k in keywords]
    # 1. arquivos de DADOS com a chave/coluna no cabecalho (jsonl 1a linha / csv header)
    for pat in DATA_GLOBS:
        for fp in glob.glob(pat, recursive=True):
            head = _data_head(fp)
            for kw in kws:
                if kw in head and (fp, kw) not in seen:
                    seen.add((fp, kw)); hits.append((kw, os.path.relpath(fp, V1), "data-key"))
    # 2. codigo de EXTRACAO (arquivo cujo conteudo associa o kw a extract/parse/def)
    for pat in CODE_GLOBS:
        for fp in glob.glob(pat, recursive=True):
            if os.path.basename(fp).startswith("provenance_guard"): continue
            try: txt = open(fp, errors="ignore").read().lower()
            except Exception: continue
            for kw in kws:
                if kw in txt and any(v in txt for v in ("extract", "def ", "parse", "vp=[", "[poc")):
                    if (fp, kw) not in seen:
                        seen.add((fp, kw)); hits.append((kw, os.path.relpath(fp, V1), "extract-code"))
    return hits


def check(entries):
    """Retorna lista de violacoes (str). Vazio = PASS."""
    viol = []
    for e in entries:
        sig = e.get("signal_name"); st = e.get("source_status")
        if st not in BLOCKED_STATUS or sig in SKIP_SIGNALS:
            continue
        kws = SIGNAL_KEYWORDS.get(sig)
        if not kws:
            viol.append(f"PROVENANCE: signal '{sig}' BLOQUEADO ({st}) SEM keywords de busca curados — "
                        f"adicione SIGNAL_KEYWORDS['{sig}'] e prove a busca antes de bloquear")
            continue
        hits = search_extraction(kws)
        if hits:
            top = hits[:4]
            viol.append(f"PROVENANCE: '{sig}' marcado {st} MAS existe extracao/derivacao: {top} "
                        f"-> NAO esta bloqueado; reclassifique (busca de proveniencia obrigatoria antes de BLOCKED)")
    return viol


def _parse(path):
    ents, cur = [], None
    for raw in open(path):
        s = raw.strip()
        if not s or s.startswith("#") or s == "signals:":
            continue
        if s.startswith("- "):
            if cur: ents.append(cur)
            cur = {}; s = s[2:]
        if ": " in s and cur is not None:
            k, _, v = s.partition(": "); cur[k.strip()] = v.strip().strip("'\"")
    if cur: ents.append(cur)
    return ents


if __name__ == "__main__":
    import sys
    man = os.path.join(HERE, "reader_raw_source_manifest.yaml")
    v = check(_parse(man))
    print("PROVENANCE GUARD:", "PASS" if not v else "FAIL")
    for x in v: print("  X", x)
    sys.exit(1 if v else 0)
