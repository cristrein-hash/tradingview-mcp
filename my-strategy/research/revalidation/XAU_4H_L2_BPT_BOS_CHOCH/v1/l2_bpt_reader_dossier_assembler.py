#!/usr/bin/env python3
"""READER DOSSIER ASSEMBLER — monta o DOSSIÊ vivo/contrastivo por episódio (276), compondo as Camadas 0,1,2,3a,3b.

CANON (docs/XAU_4H_L2_BPT_READER_LAYER2_EVIDENCE_LIBRARY.md §GUARDRAIL + §fecho):
  fixe a Camada 1 (weekly+cascade+leg-state) -> puxe os CORE_CONTEXT como dossiê -> consulte
  CONDITIONAL/CONTRAST/POLARITY como hipóteses e precedentes -> respeite os WARNING como erros já cometidos
  -> leia o episódio livremente e responda às 6 perguntas.

ESTE CÓDIGO MONTA CONTEXTO, NÃO JULGA. A biblioteca (Camada 2) é anexada como EVIDÊNCIA CONDICIONAL,
roteada por RELEVÂNCIA de contexto (cada lente registra why_attached), NUNCA como voto/score/gate.
SEM backtest. SEM policy TAKE/SKIP. SEM score. Outcome SÓ em _AUDIT_outcome_NOT_FOR_READING (nunca input da leitura).

Reutiliza (NÃO re-deriva):
  - results/l2_bpt_episode_context_packets_276.jsonl  (Camada 1 backbone + forma 4H + DSPA path + engine states + indicadores)
  - results/l2_bpt_reader_layer2_evidence_inventory.csv (Camada 2 — 92 lentes catalogadas)
  - results/l2_bpt_sosia_clusters.csv                  (Camada 3a — sósias de superfície + discriminadores fora do match)
  - results/l2_bpt_continuation_movements.csv          (Camada 3b — origem de perna / irmãos de movimento)
  - results/l2_bpt_microstructure_feature_values_62.csv (Camada 0 rica — subset 62, anexa quando presente)
  - results/l2_bpt_swing_anatomy.csv                   (Camada 0 swing anatomy — subset 41, anexa quando presente)
  - repro_recovery/qual_packets.jsonl                  (Camada 0 micro fields no escopo 276)
  - results/l2_bpt_episode_readings_276.jsonl          (leitura viva PRÉVIA — anexada como contexto, NUNCA autoridade)

Uso:
  python3 l2_bpt_reader_dossier_assembler.py                 # monta os 276 dossiês + CSV de transparência de routing
  python3 l2_bpt_reader_dossier_assembler.py --render BARIDX  # imprime 1 dossiê como markdown p/ leitura caso-a-caso
  python3 l2_bpt_reader_dossier_assembler.py --render-contrast# imprime o set contrastivo runner/loser bear (sósias)
"""
import json, csv, sys
from collections import defaultdict

D = "results"
RR = "repro_recovery"

# ----------------------------------------------------------------------------- loaders (read-only)
def load_jsonl(path, key):
    out = {}
    for l in open(path):
        l = l.strip()
        if not l:
            continue
        r = json.loads(l)
        out[int(r[key])] = r
    return out

def load_csv_by(path, key, sep=","):
    out = {}
    for r in csv.DictReader(open(path), delimiter=sep):
        try:
            out[int(r[key])] = r
        except (ValueError, KeyError, TypeError):
            continue
    return out

PK   = load_jsonl(f"{D}/l2_bpt_episode_context_packets_276.jsonl", "episode_id")   # base (Camadas 1 + forma + path + engine + indic)
RD   = load_jsonl(f"{D}/l2_bpt_episode_readings_276.jsonl", "episode_id")          # leitura viva prévia (contexto, não autoridade)
QP   = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
SOS  = load_csv_by(f"{D}/l2_bpt_sosia_clusters.csv", "bar_idx")
CONT = load_csv_by(f"{D}/l2_bpt_continuation_movements.csv", "bar_idx")
MIC62 = load_csv_by(f"{D}/l2_bpt_microstructure_feature_values_62.csv", "bar_idx")  # subset rico (key=bar_idx)
# swing_anatomy é indexado por E# curado (não bar_idx) — junta por DATA (não fabrica mapping):
SWING = {}
for _r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv")):
    _ts = (_r.get("timestamp") or "")[:10]
    if _ts:
        SWING.setdefault(_ts, _r)  # primeiro vence; colisões raras de data ignoradas
# sósias: agrupar bar_idx por cluster
SOS_CLUSTERS = defaultdict(list)
for b, r in SOS.items():
    SOS_CLUSTERS[r["cluster_id"]].append(b)

# Camada 2 — biblioteca de lentes (separador '|')
LENSES = list(csv.DictReader(open(f"{D}/l2_bpt_reader_layer2_evidence_inventory.csv"), delimiter="|"))

def fn(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

# ----------------------------------------------------------------------------- Camada 1: flags de contexto (causais, sem outcome)
def context_flags(b):
    """Deriva os flags de contexto do episódio a partir do packet (Camada 1 + path/forma). SEM outcome.
    Estes flags só ROTEIAM quais lentes da Camada 2 ganham relevância — não decidem nada."""
    p = PK[b]
    sd = p.get("supply_demand", {})
    dp = p.get("dspa_path", {})
    eng = p.get("macro_engine_states", {})
    rb = p.get("regime_B", {})
    wk = p.get("weekly_1d_context", {})
    leg = str(sd.get("macro_reader_leg") or "").upper()
    regime = str(eng.get("regime") or "").upper()
    wkslope = fn(wk.get("weekly_slope_decisions"))
    if wkslope is None:
        wkslope = fn(wk.get("weekly_slope_20pct"))
    casc = fn(rb.get("cascade_score"))
    if casc is None:
        casc = fn(dp.get("cascade_now"))
    flush = str(dp.get("flush") or "").upper()
    capit = str(eng.get("capit") or "").upper()
    accept = str(dp.get("acceptance") or "").upper()
    sup_cat = str(sd.get("sup_cat") or "").upper()
    eng_supply = str(eng.get("supply") or "").upper()

    # leg ANCORADA no backbone Camada-1 (macro_reader_leg) como PRIMÁRIO. Canon: "fixe a Camada 1 primeiro";
    # "nunca regimeB sobrepor bull-leg". regimeB/weekly só entram como FALLBACK quando o backbone não declara leg.
    leg_bear = "BEAR" in leg
    leg_bull = "BULL" in leg
    if not leg_bear and not leg_bull:  # backbone silencioso -> fallback (NÃO override)
        leg_bear = ("BEAR" in regime) or (wkslope is not None and wkslope < 0 and casc is not None and casc <= -2)
        leg_bull = (("BULL" in regime) or (wkslope is not None and wkslope > 0)) and not leg_bear
    # macro_broken/distribution = AVISO SEPARADO (não re-decide a leg): adiciona a pergunta topo/range, NÃO remove o lado bull.
    regime_distribution_warning = str(rb.get("macro_broken")) in ("1", "True", "true") \
                                  or str(rb.get("distribution_flag")) in ("1", "True", "true")
    capit_or_flush = ("FLUSH_V" in flush) or ("CLIMAX" in capit) or ("RECLAIM" in capit) \
                     or str(dp.get("sweep")) in ("1", "True", "true") or str(sd.get("bottom_turn")) in ("1", "True", "true")
    # supply_threat = oferta overhead AMEAÇANDO (near/rejeitando/bloqueando) — discriminante, não "campo populado"
    supply_threat = sup_cat in ("SUPPLY_NEAR_AND_REJECTING", "SUPPLY_FRESH_DANGEROUS", "SUPPLY_BLOCKS_TARGET") \
                    or eng_supply == "SUPPLY_REJECTING_RISK"
    # markup_context = rompendo/aceitando acima da oferta (clean-sky bullish ou supply quebrada + aceitação)
    markup_context = sup_cat in ("SUPPLY_NEAR_BUT_BROKEN",) or eng_supply == "MARKUP_BREAKING" \
                     or (sup_cat == "CLEAN_SKY" and accept == "ACCEPTED_ABOVE_RES")
    clean_sky = (sup_cat == "CLEAN_SKY") or (eng_supply == "CLEAN_SKY_BULLISH")
    cont = CONT.get(b, {})
    has_sibling = (fn(cont.get("movement_size")) or 1) > 1
    # legpos / topo: usa qual_packets/mic62 quando houver
    q = QP.get(b, {})
    legpos = fn(q.get("legpos90"))
    if legpos is None:
        legpos = fn((MIC62.get(b) or {}).get("legpos90"))
    late_top = (legpos is not None and legpos >= 80)

    return {
        "leg_bear": bool(leg_bear),
        "leg_bull": bool(leg_bull),
        "regime_distribution_warning": bool(regime_distribution_warning),
        "range_or_chop": bool(not leg_bear and not leg_bull),
        "capit_or_flush": bool(capit_or_flush),
        "supply_threat": bool(supply_threat),
        "markup_context": bool(markup_context),
        "clean_sky": bool(clean_sky),
        "has_continuation_sibling": bool(has_sibling),
        "late_top_or_high_legpos": bool(late_top),
    }

# ----------------------------------------------------------------------------- Camada 2: routing por OBJETIVO de leitura
# A biblioteca taggeia cada lente por `helps` = objetivo de leitura que ela serve. Roteamos pelas PERGUNTAS VIVAS do
# episódio (objetivos ATIVOS dado o contexto), NÃO por soma de fatores. Cada lente cai sob o objetivo ativo de maior
# prioridade que ela serve (dedup) — foco, não lista plana. Os 2 meta-objetivos do programa (recuperar-skip-winners /
# cortar-take-losers) NÃO roteiam (não discriminam contexto — são o objetivo do programa, presentes em quase tudo).
OBJECTIVES = [  # ordem de prioridade = pergunta primária do episódio
    "bear-buy-legitimo-vs-trap",
    "reversao/fundo/capitulacao",
    "markup-through-supply-vs-supply-rejection",
    "topo/range/chop",
    "continuacao-estrutural",
    "preservar-monumentais",
]

# vocabulário fechado de razões p/ uma lente NÃO estar em foreground (presta contas; nunca esconde sem motivo).
NOT_FOREGROUND_REASONS = (
    "not_triggered_by_current_question",   # pergunta que a lente serve não está viva neste episódio
    "context_only",                        # status DEAD_AS_AUTHORITY — vocabulário/contexto, não autoridade
    "redundant_with_backbone",             # já representada no backbone always-on
    "known_failure_mode",                  # precedente de erro (estes ficam SEMPRE visíveis, não aqui)
    "polarity_requires_contrast",          # polaridade (sempre visível, não aqui)
    "requires_visual_confirmation",        # só lê no chart, não no dossiê
)

def active_objectives(flags):
    """As perguntas de leitura que o CONTEXTO deste episódio levanta (Camada 1+0 condicionam)."""
    o = set()
    if flags["leg_bear"]:
        o.add("bear-buy-legitimo-vs-trap")
    if flags["capit_or_flush"]:
        o.add("reversao/fundo/capitulacao")
    if flags["supply_threat"] or flags["markup_context"]:
        o.add("markup-through-supply-vs-supply-rejection")
    if flags["late_top_or_high_legpos"] or flags["range_or_chop"] or flags["supply_threat"] \
            or flags.get("regime_distribution_warning"):
        o.add("topo/range/chop")  # distribution/macro_broken levanta a pergunta topo SEM remover o lado bull
    if flags["has_continuation_sibling"] or (flags["leg_bull"] and flags["markup_context"]):
        o.add("continuacao-estrutural")
    if flags["leg_bear"] or flags["capit_or_flush"] or flags["has_continuation_sibling"]:
        o.add("preservar-monumentais")
    return o

def route_camada2(flags, hard_cluster=False):
    """FOREGROUND REVERSÍVEL (Opção 1 modificada, Cris). NÃO descarta, NÃO ranqueia, NÃO decide. 4 zonas:
      - always_on: famílias que NUNCA somem do dossiê principal (impedem loops antigos), mesmo sem gatilho:
        CORE_CONTEXT · POLARITY · DO_NOT_USE_AS_GATE · WARNING/FAILURE_MODE.
      - foreground_by_objective: poucas lentes 'inicialmente em foreground' porque respondem a uma PERGUNTA VIVA
        (CONDITIONAL_EVIDENCE / REQUIRES_CASE_READING). Agrupadas por pergunta. SEM 'top/best/score/strongest'.
      - contradiction_probes: CONTRAST_LENS — lentes que podem INVERTER/invalidar a leitura ingênua.
        OBRIGATÓRIAS quando há sósia conflitante (hard cluster: runner E loser na mesma superfície).
      - also_available: o resto, PRESERVADO, cada lente com not_foreground_reason explícito (presta contas).
    JSONL guarda 100% das lentes — also_available é renderizável sob demanda, não cemitério."""
    objs = active_objectives(flags)
    core, polarity, do_not_gate, warnings = [], [], [], []
    foreground = {o: [] for o in OBJECTIVES if o in objs}
    probes, also_available = [], []

    def mk(L, st, fam):
        return {"family": fam, "name": L.get("evidence_name"), "status": st,
                "reader_use": L.get("reader_use"), "reader_not_use": L.get("reader_not_use"),
                "helps": L.get("helps")}

    for L in LENSES:
        st = (L.get("status") or "").strip()
        fam = (L.get("family") or "").strip().upper()
        e = mk(L, st, fam)
        # ---- ALWAYS-ON families (nunca somem) ----
        if st == "CORE_CONTEXT":
            e["role"] = "backbone — o dossiê sempre carrega"; core.append(e); continue
        if st == "POLARITY_DEPENDS_ON_CONTEXT":
            e["role"] = "polaridade — o MESMO sinal inverte de sentido conforme contexto (segurar ambas)"
            polarity.append(e); continue
        if st == "DO_NOT_USE_AS_GATE":
            e["role"] = "rica como contexto, fatal como gate — sempre visível p/ não virar gate escondido"
            do_not_gate.append(e); continue
        if st == "WARNING_FAILURE_MODE":
            e["role"] = ("guard-rail de método — erro de processo a nunca repetir" if fam == "FOUNDATION"
                         else "precedente de erro neste eixo — respeitar, não repetir")
            e["is_method_guardrail"] = (fam == "FOUNDATION")
            warnings.append(e); continue
        # ---- CONTRADICTION / INVALIDATION PROBES ----
        if st == "CONTRAST_LENS":
            e["role"] = "contrast/invalidation probe — pode inverter a leitura ingênua; discrimina ENTRE casos"
            e["mandatory_due_to_conflicting_sosias"] = bool(hard_cluster)
            probes.append(e); continue
        # ---- CONDITIONAL_EVIDENCE / REQUIRES_CASE_READING / DEAD_AS_AUTHORITY ----
        if st == "DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT":
            e["not_foreground_reason"] = "context_only"; also_available.append(e); continue
        lens_helps = {t.strip() for t in (L.get("helps") or "").split(";")}
        matched = next((o for o in OBJECTIVES if o in objs and o in lens_helps), None)
        if matched:
            e["foreground_because"] = matched  # responde a uma pergunta viva (NÃO é 'mais importante')
            e["role"] = "initially foregrounded — relevante a uma pergunta viva do caso (não ranking, não decisão)"
            foreground[matched].append(e)
        else:
            e["not_foreground_reason"] = "not_triggered_by_current_question"; also_available.append(e)

    return {
        "always_on": {"core_context": core, "polarity_hold": polarity,
                      "do_not_use_as_gate": do_not_gate, "failure_mode_warnings": warnings},
        "foreground_by_objective": foreground,
        "contradiction_probes": probes,
        "also_available": also_available,
        "active_objectives": [o for o in OBJECTIVES if o in objs],
    }

# ----------------------------------------------------------------------------- Camada 0: forma viva (276 + subset rico)
def camada0(b):
    p = PK[b]
    q = QP.get(b, {})
    dp = p.get("dspa_path", {})
    out = {
        "price_sequence_4h": p.get("price_sequence_4h"),   # a FORMA real (14 barras 4H até a entrada)
        "path_form_276": {  # forma derivada do path contíguo — disponível p/ todos os 276
            "sweep_low_reclaim": dp.get("sweep"), "sweep_depth_atr": dp.get("sweep_depth"),
            "swept_high_reject": dp.get("swept_high"), "flush": dp.get("flush"),
            "flush_velocity_atr_bar": dp.get("flush_velocity"), "drop_atr": dp.get("drop_atr"),
            "acceptance": dp.get("acceptance"), "closes_above_res": dp.get("closes_above_res"),
            "rejections_at_res": dp.get("rejections"), "structure": dp.get("structure"),
            "BOS": dp.get("BOS"), "CHoCH": dp.get("CHoCH"),
        },
        "micro_fields_276": {  # campos micro do qual_packet (escopo 276)
            "rsi": q.get("rsi"), "rsi_1d": q.get("rsi_1d"), "rsi_min8": q.get("rsi_min8"),
            "dist_4h_supply_low_atr": q.get("dist_4h_supply_low_atr"),
            "dist_4h_demand_low_atr": q.get("dist_4h_demand_low_atr"),
            "demand_origin_leg": q.get("demand_origin_leg"), "demand_touched_on_retest": q.get("demand_touched_on_retest"),
        },
    }
    # subset rico: anexa só quando presente; declara cobertura (honestidade, não fabrica)
    m = MIC62.get(b)
    if m:
        out["micro_rich_62"] = {k: m.get(k) for k in (
            "legpos30", "legpos90", "va_state", "below_VAL", "dist_POC_atr", "dist_VAL_atr", "va_width_atr",
            "reclaim_body_atr", "drop20_atr", "rise20_atr", "micro_bottom_reclaim", "micro_top_chase",
            "supply_rejected_before", "supply_broken_before", "bear_div", "sup_cat", "pol_cat", "demand_cat",
            "swept_prior_high", "bars_since_swing", "net_micro_location")}
        out["micro_rich_62_coverage"] = "present"
    else:
        out["micro_rich_62_coverage"] = "ABSENT (subset 62 — fora dele a forma rica vem só do path_form_276/micro_fields_276)"
    s = SWING.get((PK[b].get("timestamp") or "")[:10])  # swing_anatomy junta por DATA (E# != bar_idx)
    if s:
        out["swing_anatomy_41"] = {k: s.get(k) for k in (
            "low_seq(recent)", "low_seq(prior)", "high_seq", "polarity_is_LH", "sweep",
            "bos_down_recent", "sl_origin_dist_atr", "leg10_atr", "slope20_atr", "annot")}
        out["swing_anatomy_41_coverage"] = "present"
    else:
        out["swing_anatomy_41_coverage"] = "ABSENT (subset 41)"
    return out

# ----------------------------------------------------------------------------- Camada 3a: sósias (contraste)
def camada3a(b):
    r = SOS.get(b)
    if not r:
        return {"available": False}
    cid = r["cluster_id"]
    sig = {"flush": r.get("flush"), "clean_sky": r.get("clean_sky"),
           "demand": r.get("demand"), "acceptance": r.get("acceptance")}
    sosias = []
    for x in SOS_CLUSTERS.get(cid, []):
        if x == b:
            continue
        xr = SOS.get(x, {})
        sosias.append({  # o que VARIA fora do match de superfície = o contraste a ler
            "bar_idx": x, "datetime": xr.get("datetime"),
            "weekly": xr.get("weekly"), "cascade": xr.get("cascade"),
            "block_type": xr.get("block_type"), "block_decision": xr.get("block_decision"),
            "_AUDIT_mfe_R": xr.get("mfe_R"), "_AUDIT_mfe_R_source": "sosia_clusters.csv",
        })
    return {
        "available": True, "cluster_id": cid, "surface_signature_matched": sig,
        "is_hard_cluster": r.get("is_hard_cluster") in ("1", 1, "True", "true"),
        "this_episode": {"weekly": r.get("weekly"), "cascade": r.get("cascade")},
        "sosias_same_surface": sosias,
        "discriminators_to_read": "weekly_slope + cascade + FORMA — variam DENTRO do cluster (ficam fora do match). "
                                  "Se HARD (runner E loser na mesma superfície): a leitura tem que discriminar pela dinâmica, não pela superfície.",
    }

# ----------------------------------------------------------------------------- Camada 3b: continuação estrutural
def camada3b(b):
    r = CONT.get(b)
    if not r:
        return {"available": False}
    sibs = [int(x) for x in str(r.get("movement_siblings") or "").split() if x.strip().isdigit()]
    sib_info = []
    for x in sibs:
        xr = CONT.get(x, {})
        pk = PK.get(x, {})
        sib_info.append({"bar_idx": x, "datetime": xr.get("datetime"),
                         "_AUDIT_mfe_R": pk.get("_AUDIT_outcome_NOT_FOR_READING", {}).get("mfe_R"),
                         "_AUDIT_mfe_R_source": "context_packets _AUDIT"})
    return {
        "available": True,
        "anchor_swinghigh_bar": r.get("anchor_swinghigh_bar"), "anchor_date": r.get("anchor_date"),
        "anchor_high": r.get("anchor_high"), "movement_size": r.get("movement_size"),
        "siblings": sib_info,
        "note": "Irmãos partem do MESMO swing-high de origem (perna). NÃO cortar o 2º evento da mesma perna só pela "
                "superfície local; 'mesmo movimento' NÃO é runner garantido (não vira gate de TAKE).",
    }

# ----------------------------------------------------------------------------- montagem do dossiê
SIX_QUESTIONS = [
    "1) Que episódio está em andamento?",
    "2) Qual o papel deste trade nele?",
    "3) Que fatores mudam de significado pelo contexto (Camada 1)?",
    "4) Que precedentes/sósias (3a) e continuação (3b) ajudam?",
    "5) É continuação, fundo legítimo, trap, rejeição, absorção, markup ou conflito?",
    "6) O que faria a leitura estar errada (gatilhos de invalidação)?",
]
DISCLAIMER = ("A biblioteca (Camada 2) NÃO decide. Cada lente é evidência condicional/lente/precedente/alerta. "
              "O Reader interpreta o episódio livremente e dialoga com as lentes — nunca soma, vota ou pontua. "
              "Se a conclusão puder ser reduzida a uma soma de fatores, a leitura foi mal executada.")

def build_dossier(b):
    p = PK[b]
    flags = context_flags(b)
    c3a = camada3a(b)  # precisa vir antes da Camada 2: hard-cluster torna contradiction probes OBRIGATÓRIAS
    hard = bool(c3a.get("available") and c3a.get("is_hard_cluster"))
    c2 = route_camada2(flags, hard_cluster=hard)
    return {
        "episode_id": b, "bar_idx": b, "timestamp": p.get("timestamp"),
        "_READER_INSTRUCTIONS": {"disclaimer": DISCLAIMER, "six_questions": SIX_QUESTIONS,
                                 "order": "fixe Camada 1 -> leia Camada 0 (forma) -> consulte Camada 2 (lentes) -> "
                                          "contraste 3a (sósias) e 3b (continuação) -> responda às 6 perguntas."},
        # Camada 1 — eixo condicionante, fixado PRIMEIRO
        "camada_1_backbone": {
            "weekly_1d_context": p.get("weekly_1d_context"),
            "regime_B": p.get("regime_B"),
            "macro_reader_leg": p.get("supply_demand", {}).get("macro_reader_leg"),
            "sup_cat": p.get("supply_demand", {}).get("sup_cat"),
            "pol_cat": p.get("supply_demand", {}).get("pol_cat"),
            "clean_sky": p.get("supply_demand", {}).get("clean_sky"),
            "bottom_turn": p.get("supply_demand", {}).get("bottom_turn"),
        },
        # Camada 0 — forma viva do preço
        "camada_0_form": camada0(b),
        # Camada 2 — biblioteca como evidência condicional (FOREGROUND REVERSÍVEL — 4 zonas; JSONL = 100% das lentes)
        "camada_2_evidence": {
            "disclaimer": DISCLAIMER,
            "structure_note": ("4 zonas: always_on (famílias que NUNCA somem) · foreground_by_objective (poucas "
                               "lentes p/ perguntas vivas, sem ranking) · contradiction_probes (podem inverter a "
                               "leitura) · also_available (preservado, com not_foreground_reason). Reversível e auditável."),
            "not_foreground_reason_vocabulary": list(NOT_FOREGROUND_REASONS),
            "active_context_flags": [f for f, v in flags.items() if v],
            "active_reading_objectives": c2["active_objectives"],
            "always_on": c2["always_on"],
            "foreground_by_objective": c2["foreground_by_objective"],
            "contradiction_probes": c2["contradiction_probes"],
            "contradiction_probes_mandatory": hard,
            "also_available": c2["also_available"],
        },
        # Camada 3a — sósias (motor de contraste)
        "camada_3a_sosias": c3a,
        # Camada 3b — continuação estrutural
        "camada_3b_continuation": camada3b(b),
        # Referência: estados dos engines + indicadores (evidência, não autoridade)
        "engine_states_reference": {
            "macro_engine_states": p.get("macro_engine_states"),
            "dspa_path": p.get("dspa_path"),
            "dspa_intermediate": p.get("dspa_intermediate"),
            "indicators": p.get("indicators"),
        },
        # Leitura viva PRÉVIA (contexto, NUNCA autoridade — pode ser re-lida do zero)
        "prior_living_reading": {k: RD.get(b, {}).get(k) for k in (
            "episode_type", "trade_role", "narrative", "conditioning_principal",
            "factors_meaning_changed", "provisional_decision", "qualitative_confidence",
            "invalidation_triggers", "uncertainty_notes")} if b in RD else {"available": False},
        # Outcome — SÓ auditoria, NUNCA input da leitura
        "_AUDIT_outcome_NOT_FOR_READING": p.get("_AUDIT_outcome_NOT_FOR_READING"),
    }

# ----------------------------------------------------------------------------- markdown renderer (leitura caso-a-caso)
def render_md(b):
    d = build_dossier(b)
    L = []
    a = L.append
    a(f"# DOSSIÊ DO READER — episódio {b}  ({d['timestamp']})")
    a(f"\n> {d['_READER_INSTRUCTIONS']['disclaimer']}\n")
    c1 = d["camada_1_backbone"]; rb = c1["regime_B"] or {}; wk = c1["weekly_1d_context"] or {}
    a("## Camada 1 — backbone condicionante (fixar PRIMEIRO)")
    a(f"- leg: **{c1['macro_reader_leg']}** | weekly_slope={wk.get('weekly_slope_decisions') or wk.get('weekly_slope_20pct')} | "
      f"cascade={rb.get('cascade_score')} | combined={rb.get('combined_score')} | macro_broken={rb.get('macro_broken')} | v3={rb.get('v3_state')}")
    a(f"- sup_cat={c1['sup_cat']} | pol_cat={c1['pol_cat']} | clean_sky={c1['clean_sky']} | bottom_turn={c1['bottom_turn']}")
    c0 = d["camada_0_form"]; pf = c0["path_form_276"]
    a("\n## Camada 0 — forma viva")
    a(f"- path: flush={pf['flush']} (vel={pf['flush_velocity_atr_bar']}, drop={pf['drop_atr']}) | sweep_low_reclaim={pf['sweep_low_reclaim']} "
      f"depth={pf['sweep_depth_atr']} | acceptance={pf['acceptance']} | structure={pf['structure']} BOS={pf['BOS']} CHoCH={pf['CHoCH']}")
    a(f"- micro276: rsi={c0['micro_fields_276']['rsi']} rsi_min8={c0['micro_fields_276']['rsi_min8']} "
      f"dist_supply_atr={c0['micro_fields_276']['dist_4h_supply_low_atr']} dist_demand_atr={c0['micro_fields_276']['dist_4h_demand_low_atr']}")
    a(f"- subset rico 62: {c0['micro_rich_62_coverage']} | swing anatomy 41: {c0['swing_anatomy_41_coverage']}")
    seq = c0["price_sequence_4h"] or []
    a("- forma 4H (últimas barras até a entrada):")
    for bar in seq[-8:]:
        mk = "ENTRY>" if bar.get("entry") else "      "
        a(f"    {mk} {bar['t']}  O{bar['o']} H{bar['h']} L{bar['l']} C{bar['c']}  rng{bar['rng']} body{bar['body']:+}")
    c2 = d["camada_2_evidence"]
    ao = c2["always_on"]
    a("\n## Camada 2 — evidência condicional (foreground reversível; JSONL = 100% das lentes; NÃO ranking, NÃO decisão)")
    a(f"- flags de contexto ativos: {', '.join(c2['active_context_flags'])}")
    a(f"- perguntas de leitura ativas: {', '.join(c2['active_reading_objectives']) or '(nenhuma específica)'}")
    a("\n### ALWAYS-ON (famílias que nunca somem do dossiê principal)")
    a(f"- CORE_CONTEXT ({len(ao['core_context'])}): " + " · ".join(x["name"] for x in ao["core_context"]))
    a(f"- POLARITY — sentido inverte ({len(ao['polarity_hold'])}): " + " · ".join(x["name"] for x in ao["polarity_hold"]))
    a(f"- DO_NOT_USE_AS_GATE ({len(ao['do_not_use_as_gate'])}): " + " · ".join(x["name"] for x in ao["do_not_use_as_gate"]))
    a(f"- WARNING/FAILURE_MODE ({len(ao['failure_mode_warnings'])}): "
      + " · ".join((x["name"] + ("*" if x.get("is_method_guardrail") else "")) for x in ao["failure_mode_warnings"])
      + "   (*=guard-rail de método)")
    nfg = sum(len(v) for v in c2["foreground_by_objective"].values())
    a(f"\n### FOREGROUND — lentes inicialmente relevantes às perguntas vivas ({nfg}; relevância, NÃO importância/ranking)")
    a("_ordem = ordem da biblioteca, NÃO força; o 1º item não é o mais forte. Foreground ≠ 'as que importam'._")
    if nfg == 0:
        a("_0 perguntas específicas ativas: leia pela FORMA (Camada 0) + backbone + probes + also-available. "
          "Ausência de foreground NÃO é dossiê pobre nem simplificação — é episódio sem pergunta-eixo disparada._")
    for obj, lst in c2["foreground_by_objective"].items():
        if not lst:
            continue
        a(f"\n  #### pergunta viva: {obj}  ({len(lst)})")
        for x in lst:
            a(f"    - [{x['status']}] **{x['name']}** ({x['family']})")
            a(f"        usar: {x['reader_use']}")
            if x.get("reader_not_use"):
                a(f"        NÃO: {x['reader_not_use']}")
    pr = c2["contradiction_probes"]
    a(f"\n### CONTRADICTION / INVALIDATION PROBES ({len(pr)}) — podem INVERTER a leitura ingênua"
      + ("  **[OBRIGATÓRIAS — sósia conflitante neste cluster]**" if c2["contradiction_probes_mandatory"] else ""))
    for x in pr:
        a(f"    - **{x['name']}** ({x['family']})")
        a(f"        usar: {x['reader_use']}")
        if x.get("reader_not_use"):
            a(f"        NÃO: {x['reader_not_use']}")
    aa = c2["also_available"]
    a(f"\n### ALSO-AVAILABLE ({len(aa)}) — preservadas, renderizáveis sob demanda (não descartadas)")
    a("_consulte estas livremente — não-foreground ≠ irrelevante; só não foi disparada por uma pergunta viva deste caso._")
    for x in aa:
        a(f"    - {x['name']} ({x['family']}) — _não-foreground: {x['not_foreground_reason']}_")
    s3a = d["camada_3a_sosias"]
    a("\n## Camada 3a — sósias (contraste de superfície)")
    if s3a.get("available"):
        a(f"- cluster {s3a['cluster_id']} | superfície={s3a['surface_signature_matched']} | HARD={s3a['is_hard_cluster']} | "
          f"este: weekly={s3a['this_episode']['weekly']} cascade={s3a['this_episode']['cascade']}")
        for x in s3a["sosias_same_surface"][:10]:
            a(f"    - {x['bar_idx']} {x['datetime']} weekly={x['weekly']} cascade={x['cascade']} "
              f"[{x['block_type']}/{x['block_decision']}] (mfe_R audit={x['_AUDIT_mfe_R']})")
        a(f"  > {s3a['discriminators_to_read']}")
    else:
        a("- (sem sósia disponível)")
    s3b = d["camada_3b_continuation"]
    a("\n## Camada 3b — continuação estrutural")
    if s3b.get("available") and s3b.get("siblings"):
        a(f"- anchor swing-high bar {s3b['anchor_swinghigh_bar']} ({s3b['anchor_date']}, high {s3b['anchor_high']}) | movimento={s3b['movement_size']} entradas")
        for x in s3b["siblings"]:
            a(f"    - irmão {x['bar_idx']} {x['datetime']} (mfe_R audit={x['_AUDIT_mfe_R']})")
        a(f"  > {s3b['note']}")
    else:
        a("- (sem irmão de movimento — entrada isolada nesta perna)")
    pr = d["prior_living_reading"]
    if pr.get("episode_type"):
        a("\n## Leitura viva PRÉVIA (contexto, não autoridade)")
        a(f"- tipo={pr['episode_type']} | papel={pr['trade_role']} | decisão_prov={pr['provisional_decision']} | conf={pr['qualitative_confidence']}")
        a(f"- narrativa: {pr['narrative']}")
        a(f"- condicionante: {pr['conditioning_principal']}")
        a(f"- invalidação: {pr['invalidation_triggers']}")
    a("\n## As 6 perguntas da leitura")
    for q in d["_READER_INSTRUCTIONS"]["six_questions"]:
        a(f"- {q}")
    au = d["_AUDIT_outcome_NOT_FOR_READING"] or {}
    a(f"\n_(audit, não-input: mfe_R={au.get('mfe_R')} runner={au.get('is_runner')} monumental={au.get('is_monumental')})_")
    return "\n".join(L)

# ----------------------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    if args and args[0] == "--render":
        print(render_md(int(args[1])))
        return
    if args and args[0] == "--render-contrast":
        # set contrastivo bear (do reading_context_dump): runners vs losers de superfície parecida
        bydate = {PK[b]["timestamp"][:10]: b for b in PK}
        RUN = ["2023-03-08", "2023-03-09", "2021-08-13", "2020-12-02"]
        LOS = ["2021-01-28", "2021-02-22", "2022-06-23", "2021-03-10"]
        for tag, lst in (("RUNNER", RUN), ("LOSER", LOS)):
            for s in lst:
                if s in bydate:
                    print("\n" + "#" * 100 + f"\n### {tag}\n")
                    print(render_md(bydate[s]))
        return

    # montagem completa dos 276
    EP = sorted(PK)
    dossiers = [build_dossier(b) for b in EP]
    with open(f"{D}/l2_bpt_reader_dossier_276.jsonl", "w") as f:
        for d in dossiers:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # CSV de transparência (auditável: por que cada lente ficou foreground vs also_available; cauda saturada)
    FG_DIAG = 25  # diagnóstico §6 (NÃO cap): foreground alto = pergunta ainda genérica demais, não regra dura
    with open(f"{D}/l2_bpt_reader_dossier_camada2_routing.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["bar_idx", "timestamp", "active_flags", "active_objectives", "n_always_on", "n_foreground",
                    "foreground_per_objective", "n_probes", "probes_mandatory", "n_also_available",
                    "foreground_large_diag", "n_sosias", "has_continuation", "micro62", "swing41"])
        for d in dossiers:
            c2 = d["camada_2_evidence"]; c0 = d["camada_0_form"]
            s3a = d["camada_3a_sosias"]; s3b = d["camada_3b_continuation"]
            fbo = c2["foreground_by_objective"]
            n_ao = sum(len(v) for v in c2["always_on"].values())
            n_fg = sum(len(v) for v in fbo.values())
            per_obj = " ".join(f"{o.split('-')[0].split('/')[0]}:{len(v)}" for o, v in fbo.items() if v)
            w.writerow([d["bar_idx"], d["timestamp"], "|".join(c2["active_context_flags"]),
                        "|".join(c2["active_reading_objectives"]), n_ao, n_fg, per_obj,
                        len(c2["contradiction_probes"]), int(c2["contradiction_probes_mandatory"]),
                        len(c2["also_available"]), int(n_fg > FG_DIAG),
                        len(s3a.get("sosias_same_surface", [])) if s3a.get("available") else 0,
                        int(bool(s3b.get("available") and s3b.get("siblings"))),
                        int(c0["micro_rich_62_coverage"] == "present"),
                        int(c0["swing_anatomy_41_coverage"] == "present")])

    # resumo da run (materializado no stdout do script salvo)
    nfg = [sum(len(v) for v in d["camada_2_evidence"]["foreground_by_objective"].values()) for d in dossiers]
    nobj = [len(d["camada_2_evidence"]["active_reading_objectives"]) for d in dossiers]
    ao0 = dossiers[0]["camada_2_evidence"]["always_on"]
    n_mand = sum(1 for d in dossiers if d["camada_2_evidence"]["contradiction_probes_mandatory"])
    n_diag = sum(1 for x in nfg if x > FG_DIAG)
    n62 = sum(1 for d in dossiers if d["camada_0_form"]["micro_rich_62_coverage"] == "present")
    n41 = sum(1 for d in dossiers if d["camada_0_form"]["swing_anatomy_41_coverage"] == "present")
    nsos = sum(1 for d in dossiers if d["camada_3a_sosias"].get("available") and d["camada_3a_sosias"].get("sosias_same_surface"))
    ncont = sum(1 for d in dossiers if d["camada_3b_continuation"].get("available") and d["camada_3b_continuation"].get("siblings"))
    print(f"READER DOSSIER ASSEMBLER — {len(dossiers)}/276 dossiês montados (Camadas 0,1,2,3a,3b).")
    print(f"  saída: {D}/l2_bpt_reader_dossier_276.jsonl  +  {D}/l2_bpt_reader_dossier_camada2_routing.csv")
    print(f"  biblioteca Camada 2: {len(LENSES)} lentes — TODAS preservadas no JSONL (foreground reversível, 4 zonas).")
    print(f"  ALWAYS-ON (nunca somem): core={len(ao0['core_context'])} polarity={len(ao0['polarity_hold'])} "
          f"do_not_gate={len(ao0['do_not_use_as_gate'])} warnings={len(ao0['failure_mode_warnings'])} = {sum(len(v) for v in ao0.values())}")
    print(f"  CONTRADICTION PROBES: 6 sempre presentes; OBRIGATÓRIAS em {n_mand}/276 (cluster sósia conflitante).")
    print(f"  perguntas de leitura ATIVAS/episódio: min={min(nobj)} max={max(nobj)} média={sum(nobj)/len(nobj):.1f} (de 6).")
    print(f"  FOREGROUND/episódio (superfície de leitura): min={min(nfg)} max={max(nfg)} média={sum(nfg)/len(nfg):.1f}.")
    print(f"  DIAGNÓSTICO §6 — episódios com foreground>{FG_DIAG} (pergunta ainda genérica demais): {n_diag}/276.")
    print(f"  cobertura Camada 0 rica: micro62 {n62}/276, swing41 {n41}/276 (resto = path_form_276 — declarado, não fabricado).")
    print(f"  sósias ≥1 par mesma superfície: {nsos}/276 | continuação ≥1 irmão de perna: {ncont}/276.")
    print("  Outcome SÓ em _AUDIT_outcome_NOT_FOR_READING. SEM score, SEM TAKE/SKIP, SEM backtest. Código montou, NÃO julgou.")

if __name__ == "__main__":
    main()
