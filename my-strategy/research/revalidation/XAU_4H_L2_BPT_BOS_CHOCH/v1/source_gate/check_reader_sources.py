#!/usr/bin/env python3
"""RAW SOURCE GATE — check executável (fail-fast). Exit 1 se qualquer violação da RAW SOURCE GATE POLICY.
Parser YAML-subset proprio (pyyaml ausente). Roda: python3 source_gate/check_reader_sources.py
Politica: docs/RAW_SOURCE_GATE_POLICY.md | manifest: source_gate/reader_raw_source_manifest.yaml"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "reader_raw_source_manifest.yaml")
LAYER = os.path.join(V1, "l2_bpt_causal_indicator_layer.py")
REQUIRED_KEYS = ["signal_name", "current_field", "current_source", "raw_original_field",
                 "raw_file_or_registry_source", "transform_method", "causal_timing_model", "no_future_guard",
                 "fidelity_check", "source_status", "allowed_in_blind_packet", "allowed_as_decision",
                 "known_bug", "action_required", "notes"]
VALID_STATUS = {"RAW_ORIGINAL_OK", "DERIVED_FROM_RAW_WITH_MAPPING", "VISUAL_AUX_ONLY", "HEURISTIC_ONLY_FLAGGED",
                "UNKNOWN_BLOCKED", "UNMAPPED_DERIVED_DISALLOWED", "DERIVED_ARTIFACT_BUG"}
BLOCKED_STATUS = {"UNKNOWN_BLOCKED", "UNMAPPED_DERIVED_DISALLOWED", "DERIVED_ARTIFACT_BUG"}
INDICATOR_OK = {"RAW_ORIGINAL_OK"}

def parse_manifest(path):
    entries, cur = [], None
    for raw in open(path):
        line = raw.rstrip("\n")
        s = line.strip()
        if not s or s.startswith("#") or s == "signals:":
            continue
        if s.startswith("- "):
            if cur:
                entries.append(cur)
            cur = {}
            s = s[2:]
        if ": " in s or s.endswith(":"):
            k, _, v = s.partition(": ")
            v = v.strip().strip("'").strip('"')
            if cur is not None:
                cur[k.strip()] = v
    if cur:
        entries.append(cur)
    return entries

viol = []
def fail(cond, msg):
    if cond:
        viol.append(msg)

# ---- 1. parse + schema ----
if not os.path.exists(MANIFEST):
    print("GATE FAIL: manifest ausente"); sys.exit(1)
entries = parse_manifest(MANIFEST)
for e in entries:
    miss = [k for k in REQUIRED_KEYS if k not in e]
    fail(bool(miss), f"[{e.get('signal_name','?')}] faltam chaves: {miss}")
    fail(e.get("source_status") not in VALID_STATUS, f"[{e.get('signal_name')}] status invalido: {e.get('source_status')}")

# ---- 1b. PROVENANCE GUARD (constricao estrutural; substitui memoria passiva, que falhou 2x) ----
# Nenhum signal pode ficar UNKNOWN_BLOCKED se ja existe extracao no repo. Busca REAL; falha apontando o arquivo.
# Provado: re-injetar svp_poc_val_vah=UNKNOWN_BLOCKED -> FALHA apontando svp_bars/F6 (o erro de 2026-06-23).
try:
    import provenance_guard as _pg
    for _v in _pg.check(entries):
        fail(True, _v)
except Exception as _e:
    fail(True, f"provenance_guard indisponivel/erro: {_e}")

# ---- 2. allowed_as_decision == NO para TODOS ----
for e in entries:
    fail(e.get("allowed_as_decision", "").upper() != "NO",
         f"[{e.get('signal_name')}] allowed_as_decision != NO (indicador nunca decide)")

# ---- 3. BLOCKED nao pode estar allowed_in_blind_packet=YES ----
for e in entries:
    if e.get("source_status") in BLOCKED_STATUS:
        fail(e.get("allowed_in_blind_packet", "").upper() == "YES",
             f"[{e.get('signal_name')}] {e.get('source_status')} com allowed_in_blind_packet=YES (deve ser NO)")

# ---- 4. indicador RAW_ORIGINAL_OK precisa de no_future_guard ----
for e in entries:
    if e.get("source_status") in INDICATOR_OK:
        fail(e.get("no_future_guard", "").upper() in ("", "NO", "UNKNOWN"),
             f"[{e.get('signal_name')}] RAW_ORIGINAL_OK sem no_future_guard")

# ---- 5. layer de indicador NAO le derivado como fonte de verdade ----
if os.path.exists(LAYER):
    src = open(LAYER).read()
    # so pode aparecer raw_features_2020_2026 no contexto de GUARD/FORBIDDEN, nunca como leitura de dados
    bad_lines = [ln for ln in src.splitlines()
                 if "raw_features_2020_2026" in ln and not any(t in ln.lower() for t in ("forbidden", "guard", "proibida", "incidente", "derivado", "nunca", "recusa"))]
    fail(bool(bad_lines), f"layer le derivado como fonte: {bad_lines[:2]}")
    fail("RAW_EVENTS" not in src or "raw_indicator_events" not in src, "layer nao aponta p/ artefato RAW (raw_indicator_events)")
    fail("RAW_SOURCE_PATTERN" not in src, "layer sem GUARD de pattern RAW (XAUUSD_*replay*.jsonl.gz)")
else:
    fail(True, "l2_bpt_causal_indicator_layer.py ausente")

# ---- 6. nenhum indicador como gate/score/veto (output do layer nao tem decisao) ----
if os.path.exists(LAYER):
    src = open(LAYER).read()
    # tokens de decisao so podem aparecer como PROIBICAO (NAO classifica / nunca)
    for tok in ("TAKE_CANDIDATE", "return.*score", "def gate", "veto"):
        for ln in src.splitlines():
            if re.search(tok, ln) and not any(t in ln for t in ("NAO", "nunca", "não", "#", '"""')):
                fail(True, f"layer com possivel decisao/gate: {ln.strip()[:70]}")

# ---- 7. pacotes cegos nao contem OUTCOME estruturado (mfe/_audit/is_runner/...) ----
OUT_TOK = re.compile(r"_audit|mfe_r|mfe=|is_runner|is_loser|is_monumental|\b\d+\.?\d*\s*R\b", re.I)
for pk in glob.glob(os.path.join(V1, "results", "blind_pack_*", "reading_packet_BLIND.md")):
    blob = open(pk).read()
    hits = set(m.group(0).lower() for m in OUT_TOK.finditer(blob))
    fail(bool(hits), f"pacote cego {os.path.basename(os.path.dirname(pk))} com outcome estruturado: {hits}")

# ---- 8. SISTEMICO (content-driven, rename-proof): pacote cego de INPUT nao pode embutir campo de fonte BLOQUEADA ----
# O DA mostrou que scan por NOME de builder tem furo (rename-and-escape). Enforcement correto = no ARTEFATO DE INPUT
# que o Reader cego le (reading_packet_BLIND.md + *agent_input*.json). QUALQUER builder (qualquer nome) que produza um
# pacote cego com campo bloqueado e pego AQUI. RATCHET: baseline = inputs existentes (debito declarado); input NOVO
# (cluster futuro) com campo bloqueado = FALHA. Acao: mapear Camada-1 ao RAW antes do proximo cluster.
import glob as _glob
BLOCKED_FIELD_NAMES = ["nas_recent", "smc_recent", "bubbles_recent", "sup_cat", "pol_cat", "clean_sky",
                       "dist_4h_supply", "dist_4h_demand", "dist_poc", "above_value", "below_value"]
RES = os.path.join(V1, "results")
# RECURSIVO por NOME (*blind*) em results/** — pega input cego em QUALQUER localizacao, nao so blind_pack_/
# (fecha HOLE A do DA: agent inputs *_blind.json em results/ root tambem sao varridos).
blind_inputs = []
for dp, _dn, fns in os.walk(RES):
    for fn in fns:
        if "blind" in fn.lower() and fn.lower().rsplit(".", 1)[-1] in ("md", "json", "txt"):
            blind_inputs.append(os.path.join(dp, fn))
BASELINE_INPUTS = {  # 6 inputs cegos PRE-GATE existentes (debito declarado; acao=mapear Camada-1 ao RAW)
    "_structural_agent_input_blind.json", "_microstructure_agent_input_blind.json",
    "_deep_eracontrol_blind.json", "_structural_blind_compact.json",
    os.path.join("blind_pack_cluster4918", "reading_packet_BLIND.md"),
    os.path.join("blind_pack_cluster2", "reading_packet_BLIND.md"),
}
# fontes UPSTREAM que emitem Camada-1 derivada (debito declarado p/ honestidade; enforcement real e no input acima)
UPSTREAM_DEBT = []
for fp in (_glob.glob(os.path.join(V1, "l2_bpt_episode_context_assembler.py")) +
           _glob.glob(os.path.join(V1, "l2_bpt_reader_dossier_assembler.py")) +
           _glob.glob(os.path.join(V1, "l2_bpt_reading_packet_blind_*.py")) +
           _glob.glob(os.path.join(V1, "l2_bpt_blind_pack_*.py"))):
    txt = open(fp, errors="ignore").read()
    h = sorted({f for f in BLOCKED_FIELD_NAMES if f in txt})
    if h:
        UPSTREAM_DEBT.append((os.path.basename(fp), h))
debt_found, new_violations = [], []
for fp in blind_inputs:
    rel = os.path.relpath(fp, RES)
    hits = sorted({fld for fld in BLOCKED_FIELD_NAMES if fld in open(fp, errors="ignore").read()})
    if not hits:
        continue
    (debt_found if rel in BASELINE_INPUTS else new_violations).append((rel, hits))
fail(bool(new_violations), f"NOVO pacote cego de INPUT com campo BLOQUEADO (fora do baseline): {new_violations}")

# ---- 9. INPUT MANIFEST (FASE 6): contrato explicito de input cego; elimina o furo "input nao listado" ----
# O gate antigo dava PASS com debito baseline e dependia da convencao de nome. Agora TODO input cego/raw-clean em
# results/** TEM de estar listado no reader_input_manifest.yaml; inputs RAW_CLEAN_ALLOWED nao podem conter campo
# derivado nem valor SVP (so BLOCKED_UNMAPPED). Legacy = HISTORICAL_BASELINE_DEBT/QUARANTINED (debito documentado).
INPUT_MANIFEST = os.path.join(HERE, "reader_input_manifest.yaml")
# above_value/below_value/dist_poc REMOVIDOS da lista de bloqueados em 2026-06-23: a VA de volume (POC/VAH/VAL)
# E RAW (session_vp.last3.v=[t,POC,VAH,VAL] via svp_bars.jsonl/DSPA F6, validada 7f3c852) -> DERIVED_FROM_RAW, nao blocked.
STILL_BLOCKED_FIELDS = ["nas_recent", "smc_recent", "bubbles_recent", "dist_4h_supply", "dist_4h_demand"]
INP_STATUS = {"RAW_CLEAN_ALLOWED", "HISTORICAL_BASELINE_DEBT", "QUARANTINED", "DISALLOWED",
              "PRE_FIX_HISTORICAL_REFERENCE_ONLY"}
inp_by_path = {}
if not os.path.exists(INPUT_MANIFEST):
    fail(True, "reader_input_manifest.yaml ausente (contrato de input cego obrigatorio — FASE 6)")
else:
    inp_entries = parse_manifest(INPUT_MANIFEST)
    inp_by_path = {e.get("input_path"): e for e in inp_entries}
    for e in inp_entries:
        fail(e.get("status") not in INP_STATUS, f"[input {e.get('input_id')}] status invalido: {e.get('status')}")
        # input listado deve existir em disco (manifest nao pode apontar p/ fantasma)
        fail(not os.path.exists(os.path.join(V1, e.get("input_path", "/x"))),
             f"[input {e.get('input_id')}] input_path inexistente: {e.get('input_path')}")
# 9b. todo input cego/raw-clean em disco DEVE estar no manifest; RAW_CLEAN sem campo derivado/SVP-valor
scan_inputs = []
# Patterns = nomes de ARTEFATO DE INPUT que o Reader cego consome. Inclui reading_packet/agent_input alem de
# blind/raw_clean para fechar a costura name-scoped do DA: um input futuro nomeado p.ex. reading_packet.md (sem
# token blind/raw_clean) passa a EXIGIR contrato no manifest. A defesa final continua sendo o manifest como allowlist.
INPUT_NAME_TOKENS = ("blind", "raw_clean", "reading_packet", "agent_input")
for dp, _dn, fns in os.walk(RES):
    for fn in fns:
        low = fn.lower()
        if (any(tok in low for tok in INPUT_NAME_TOKENS) and low.rsplit(".", 1)[-1] in ("md", "json", "txt")
                and not low.endswith("_entry.json")):
            scan_inputs.append(os.path.join(dp, fn))
raw_clean_ok = []
for fp in scan_inputs:
    rel = os.path.relpath(fp, V1)
    e = inp_by_path.get(rel)
    fail(e is None, f"INPUT cego NAO listado no input manifest: {rel} (todo input cego exige contrato)")
    if e and e.get("status") == "RAW_CLEAN_ALLOWED":
        blob = open(fp, errors="ignore").read()
        # word-boundary p/ NAO confundir o campo bloqueado 'above_value' com o rotulo TPO 'ACCEPTED_ABOVE_VALUE'
        bad = sorted({f for f in STILL_BLOCKED_FIELDS
                      if re.search(r"(?<![A-Za-z0-9_])" + re.escape(f) + r"(?![A-Za-z0-9_])", blob)})
        fail(bool(bad), f"INPUT RAW_CLEAN {rel} contem campo derivado/SVP-valor: {bad}")
        # SVP/acceptance citados: ou marcados bloqueados (BLOCKED_UNMAPPED/UNKNOWN_BLOCKED), OU com a VA REAL
        # RAW-mapeada (svp_state / value-area real / validacao 7f3c852). Senao seria valor de VA sem fonte.
        low = blob.lower()
        ok_marker = any(t in blob for t in ("BLOCKED_UNMAPPED", "UNKNOWN_BLOCKED")) or \
                    any(t in low for t in ("svp_state", "value-area real", "7f3c852"))
        fail(("svp" in low or "acceptance" in low) and not ok_marker,
             f"INPUT RAW_CLEAN {rel} cita SVP/acceptance sem marcador de bloqueio NEM VA real RAW-mapeada (svp_state/7f3c852)")
        raw_clean_ok.append(rel)

# ---- emite inventario CSV (FASE 5) ----
import csv as _csv
INV = os.path.join(V1, "results", "l2_bpt_reader_source_mapping_inventory.csv")
with open(INV, "w", newline="") as f:
    w = _csv.writer(f, lineterminator="\n")
    cols = ["signal_name", "current_field", "raw_original_field", "source_status", "transform_method",
            "causal_timing_model", "no_future_guard", "fidelity_check", "allowed_in_blind_packet",
            "allowed_as_decision", "known_bug", "action_required"]
    w.writerow(cols)
    for e in entries:
        w.writerow([e.get(c, "") for c in cols])

# ---- relatorio ----
from collections import Counter
st = Counter(e.get("source_status") for e in entries)
print("=" * 78)
print("RAW SOURCE GATE — check_reader_sources.py")
print(f"manifest: {len(entries)} signals | status: {dict(st)}")
print(f"  allowed_in_blind_packet=YES: {[e['signal_name'] for e in entries if e.get('allowed_in_blind_packet','').upper()=='YES']}")
print(f"  BLOQUEADOS (NO): {[e['signal_name'] for e in entries if e.get('source_status') in BLOCKED_STATUS]}")
print("\n  DEBITO DECLARADO (baseline) — INPUTS cegos existentes com Camada-1 derivada; ACAO=mapear ao RAW:")
for base, hits in debt_found:
    print(f"    DEBT-INPUT {base}: {hits}")
print("  fontes UPSTREAM que emitem Camada-1 derivada (debito declarado; enforcement real e no input cego):")
for base, hits in UPSTREAM_DEBT:
    print(f"    DEBT-SRC {base}: {hits}")
print("  RATCHET: gate FALHA em qualquer INPUT cego NOVO (cluster futuro) com campo bloqueado fora do baseline.")
print(f"\n  INPUT MANIFEST (FASE 6): {len(inp_by_path)} inputs sob contrato | RAW_CLEAN_ALLOWED limpos: {raw_clean_ok}")
print("  Todo input cego/raw-clean em results/** exige entrada no reader_input_manifest.yaml (fecha furo 'nao listado').")
if viol:
    print("\nGATE FAIL — violacoes:")
    for v in viol:
        print("  X", v)
    sys.exit(1)
print("\nGATE PASS — nenhum indicador depende de derivado nao auditado; allowed_as_decision=NO p/ todos; "
      "bloqueados fora do pacote; layer RAW com guard; pacotes cegos sem outcome estruturado.")
sys.exit(0)
