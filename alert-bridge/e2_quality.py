#!/usr/bin/env python3
"""E2 — QUALITY READER (Camada 2, P5). LIVE desde 2026-07-26 (ordem Cris): candidato SURFACED emite
alerta Telegram advisory (hard-lock E2_PRODUCTION_AUTHORIZED=1 no wrapper). Consome candidatos MATERIAIS
do E1 (logs/e1_candidates.jsonl, por byte-offset). FRAME-EXPLÍCITO: perna 1H no topo do briefing.

PARADIGMA (redesign 2026-07-17): as camadas NÃO criam confluências mecânicas — CONVERGEM numa visão ampla.
  1) GATE determinístico (binário-causal DURO, 0 tokens): 2 vetos de HIGIENE — bad_rr, stale.
     session_vacuum e chase foram REMOVIDOS do sistema (ordem Cris 2026-07-26): sessão e frescura são
     contexto que o READ pesa, nunca morte automática (a auditoria provou que matavam winners).
  2) READ contextual único (Opus, 1 chamada/candidato-sobrevivente): recebe a IMAGEM COMPOSTA COMPLETA
     (dossiê E0 inteiro renderizado como briefing) e julga se as leituras CONVERGEM numa tese de alta
     probabilidade — com raciocínio. NÃO é refutador, NÃO conta kills, NÃO pontua. Tese guardada VERBATIM.
O juízo de QUALIDADE é convergência de contexto, não aritmética. Ver memory:feedback_contextual_convergence_not_determinism.

Arquivamento: cada read grava em logs/e2_shadow.jsonl (candidato + imagem + tese + model-id + read_version +
outcome preenchido dias depois por e2_outcome_backfill.py). Árbitro = shadow multi-dia NÃO-VISTO (nunca afinar
ao dia visível). Read atrás de E2_READ_ENABLED (default 1). py3.9.
CLI: --once · --survey [--replay] · --anchors · --selftest · --read-smoke [--n K] · (default) daemon.
"""
import os, sys, json, time, datetime as dt
from pathlib import Path
BASE = Path(__file__).resolve().parent
REPO = BASE.parent
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
from bubble_polarity import BUBBLE_POLARITY_RULE   # fonte única — polaridade context-dependente das bubbles
DOSSIER = REPO / "external_factors_v2" / "snapshots" / "market_context.json"
CAND_F = LOGS / "e1_candidates.jsonl"
VERD_F = LOGS / "e2_verdicts.jsonl"
SHADOW_F = LOGS / "e2_shadow.jsonl"
OFFSET_F = LOGS / "e2_offset.json"
PIDFILE = LOGS / "e2_quality.pid"
PAUSE_LOCAL = LOGS / "monitor.pause"
PAUSE_GLOBAL = Path("/tmp/claude_recheck.paused")
FLOOR_S = 20

# GATE determinístico (só binário-causal duro). MIN_RR = PRINCÍPIO (definição), não fit ao dia.
CFG = {"MIN_RR_E2": 2.0, "DRIFT_MAX_CYCLES": 2, "CYCLE_S": 60}


def now_iso(): return dt.datetime.now(dt.timezone.utc).isoformat()
def fnum(x):
    try: return float(str(x).replace("−", "-").replace("K", "e3").replace(" ", ""))
    except Exception: return None
def fmt(x, nd=2):
    v = fnum(x)
    return f"{v:.{nd}f}" if v is not None else "—"


# ---------- helpers de dossiê ----------
def regime(dsr):
    mtf = dsr["axes"].get("mtf", {})
    ts = [mtf.get(t, {}).get("trend") for t in ("1D", "240")]
    if "DOWN" in ts and "UP" not in ts: return "DOWN"
    if "UP" in ts and "DOWN" not in ts: return "UP"
    return "RANGE"


def atr_of(leg):
    if not leg or not leg.get("mag_atr"): return None
    try: return (leg["high"] - leg["low"]) / leg["mag_atr"]
    except Exception: return None


# ---------- GATE: 2 vetos duros de higiene (binário-causal, puros) ----------
# session_vacuum e chase REMOVIDOS DO SISTEMA (ordem Cris 2026-07-26): blocks primitivos que matavam
# winners (auditoria semana 16-24/07: vacuum matou 4, chase matou 1). Sessão e frescura da entrada são
# CONTEXTO que o READ pesa na imagem composta — nunca morte automática.
def veto_bad_rr(cand, dsr):
    # RR-only: target 3R = runway limpo = POSITIVO. Só veta RR realmente pequeno (alvo perto demais).
    rr = fnum(cand.get("rr"))
    fired = rr is None or rr < CFG["MIN_RR_E2"]
    return {"name": "bad_rr", "hard": True, "fired": fired, "value": rr,
            "reason": f"RR {rr} < {CFG['MIN_RR_E2']} (alvo perto demais)" if fired else ""}


def veto_stale(cand, dsr, drift_c):
    sh = dsr.get("source_health", {})
    bad = []
    if sh.get("mtf", {}).get("status") != "fresh": bad.append("mtf")
    if sh.get("micro_15m", {}).get("status") != "fresh": bad.append("micro")
    if cand.get("rule") == "macro_event" and sh.get("macro", {}).get("status") != "fresh": bad.append("macro")
    if drift_c is not None and drift_c > CFG["DRIFT_MAX_CYCLES"]: bad.append(f"drift{drift_c}")
    fired = bool(bad)
    return {"name": "stale_dossier", "hard": True, "fired": fired, "value": bad,
            "reason": f"dossiê stale: {bad}" if fired else ""}


def evaluate_vetos(cand, dsr, drift_c):
    """GATE binário-causal duro = SÓ HIGIENE: bad_rr (geometria) + stale (dados podres). Todo juízo
    contextual (sessão, frescura/chase, catalisador, contra-regime) vive no READ, não em vetos."""
    vs = [veto_bad_rr(cand, dsr), veto_stale(cand, dsr, drift_c)]
    hard = [v for v in vs if v["fired"] and v["hard"]]
    grade = "discard" if hard else "survivor"
    return grade, vs, hard, []


# ---------- READ CONTEXTUAL ÚNICO (Opus, convergência) ----------
CLAUDE_EXE = os.environ.get("CLAUDE_EXE", "/Users/cristrein/.local/bin/claude")
READ_MODEL = os.environ.get("E2_READ_MODEL", "claude-opus-4-8")
READ_VERSION = "r1-convergence-opus"
READ_ENABLED = os.environ.get("E2_READ_ENABLED", "1") == "1"
READ_TIMEOUT = int(os.environ.get("E2_READ_TIMEOUT", "300"))

# --- SINAL DE CONTINUAÇÃO LONG -> Telegram (Cris 2026-08-05: "sinal legítimo ou nada", RR>=2) ---
# Gate DETERMINÍSTICO (independente do read LLM, para o regime atrasado não silenciar continuações).
CONT_SIGNAL = os.environ.get("E2_CONT_SIGNAL", "0") == "1"
CONT_RULES = {"bos_continuation", "ema_reclaim", "sweep_reclaim", "ob_touch_hold", "zone_reject"}
MIN_RR_SIGNAL = 2.0

# ---------- LIVE (Cris 2026-07-26: "VAMOS ACIONAR O E2 SEM SHADOW, EM LIVE") ----------
# Hard-lock padrão do stack: envio real exige E2_PRODUCTION_AUTHORIZED=1 (exportado no wrapper launchd).
E2_LIVE = os.environ.get("E2_PRODUCTION_AUTHORIZED", "") == "1"


def _tg_send(text, audience="group"):
    """Envio Telegram advisory (NUNCA ordem). Credenciais alert-bridge/.env.
    ROTEAMENTO (Cris 05/08 ~06:4x): audience="group" = TODOS os chat_ids (grupo LIMPO — só sinais
    qualificados: L1/L2/15M-BULL/validados-pelo-reader). audience="assistant" = SÓ o chat privado
    Trading Assistant Trein (AUTHORIZED_CHAT_ID): validador de regiões, leituras de vela, sentinela."""
    try:
        env = {}
        for line in (BASE / ".env").read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("="); env[k.strip()] = v.strip()
        tok = env.get("TELEGRAM_BOT_TOKEN"); chats = env.get("TELEGRAM_CHAT_ID", "")
        if audience == "assistant":
            chats = env.get("AUTHORIZED_CHAT_ID", "") or chats
        if not tok or not chats: return False
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        ok = False
        for cid in [c.strip() for c in chats.split(",") if c.strip()]:
            data = urlencode({"chat_id": cid, "text": text}).encode()
            with urlopen(Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=data), timeout=15) as r:
                ok = ok or (r.status == 200)
        return ok
    except Exception as e:
        print(f"{now_iso()} [tg-erro] {type(e).__name__}:{str(e)[:60]}", flush=True)
        return False


def recent_strategy_signal(direction, within_s=2700):
    """True se uma ESTRATÉGIA mecânica (A1/A2, Cp) emitiu sinal na MESMA direção há <within_s.
    Usado p/ a exceção do Cris (05/08): sinal LIVE do reader vai ao GRUPO só quando conflui com estratégia."""
    import time as _t, json as _j
    now = _t.time()
    try:
        p = REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl"
        for l in open(p):
            r = _j.loads(l)
            if now - r.get("entry_t", 0) < within_s and direction == "LONG":
                return True
    except Exception:
        pass
    try:
        p = REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/alerted.jsonl"
        for l in open(p):
            r = _j.loads(l)
            if now - r.get("etime", 0) < within_s and direction == "LONG":
                return True
    except Exception:
        pass
    return False


def notify_surfaced(cand, th):
    """Alerta LIVE de candidato surfaced (contexto converge no lado do candidato). Advisory curto.
    MAPA DO TRADER (Cris 2026-08-04): sinal CONTRA a tese declarada numa zona do mapa (<=1 ATR) leva
    prefixo de CONFLITO OBRIGATÓRIO — determinístico, independente do que o read declarou. Nunca mais
    um long 'limpo' para dentro da zona de venda declarada (a falha de 04/08 08:03)."""
    if not E2_LIVE: return
    # GUARD-CHoCH ATIVO (Cris 2026-08-14): não notificar candidato LONG se CHoCH-down (quebra do higher-low)
    # no 4H E 1H (consome dossiê E0). Impede induzir compra na faca (13/08). Fail-open (sem dossiê = passa).
    if cand.get("direction") == "LONG":
        try:
            import choch_guard as CHG
            if CHG.blocks_long():
                print("(CHoCH-guard: E1/E2 LONG bloqueado — choch_dn 4H+1H, não notificado)", flush=True)
                return
        except Exception:
            pass
        # SWEEP-REJECT 4H (Cris 2026-08-14, tripwire): vela 4H pavio-sup>50%corpo bloqueia long ate
        # quebra de estrutura 15M (HH+HL). Fail-open.
        try:
            import sweep_reject_guard as SRG
            if SRG.blocks_long():
                print("(sweep-reject-4H: E1/E2 LONG bloqueado — sweep>50%corpo sem quebra 15M)", flush=True)
                return
        except Exception:
            pass
    prefix = ""
    try:
        import trader_map as _TM
        z = _TM.conflict(cand, _TM.load_map(), atr=None)
        if z:
            prefix = (f"⚠️ CONTRA A TUA LEITURA DECLARADA — zona {z['low']:.2f}–{z['high']:.2f}, "
                      f"tese {z['tese']} (\"{z['nota'][:60]}\")\n")
    except Exception:
        pass
    txt = (f"🤖 LIVE SYSTEM · E1/E2 READER 15M\n"
           f"{prefix}🧠 E2 {cand.get('direction')} XAUUSD {cand.get('rule')}@{cand.get('tf')}\n"
           f"entry {cand.get('entry')} · SL {cand.get('sl')} · alvo {cand.get('target')} (RR {cand.get('rr')})\n"
           f"convergência {th.get('convergence')} · convicção {th.get('conviction')}\n"
           f"tese: {th.get('thesis')}\n"
           f"invalida se: {th.get('invalidation')}\n"
           f"(advisory — a decisão é tua, revê o chart)")
    _tg_send(txt, audience=("group" if recent_strategy_signal(cand.get("direction")) else "assistant"))

READ_SYS = (
    "És um trader XAUUSD discricionário EXPERIENTE a ler a fita COMPLETA de um candidato de trade já "
    "pré-filtrado por gates de higiene (R:R, frescura do dossiê). NÃO és um refutador nem um comité — és UM "
    "olhar a ler o TODO.\n"
    "FRAME (2026-07-26, regra do trader): o briefing abre com o FRAME — a PERNA 1H viva e a regra de zonas. "
    "O frame é o ENQUADRAMENTO contra o qual lês todas as outras vozes: não é mais um número no meio, e "
    "também não é veto — é a gramática. Com-perna nas zonas a favor = continuação (o caso-base). "
    "Supply/demand de 15M/1H CONTRA a perna = marcador de pullback, não reversão. Reversão contra a perna "
    "só é candidata a alta probabilidade em supply/demand de 4H/1D COM confluências de exaustão. O grau "
    "emerge da leitura do todo: com-perna sozinho = enquadramento (grau médio); com-perna + as outras vozes "
    "a encadearem na mesma história = alta convicção. Nunca por contagem.\n"
    "PERNA NOVA EM FORMAÇÃO (2026-08-02, auditoria zero-longs — 4 viragens vencedoras recusadas por isto): o "
    "rótulo da perna 1H é ATRASADO nas viragens — vira só depois de a subida/descida estar avançada. Uma "
    "SEQUÊNCIA DE RECLAIM CONFIRMADA — sweep do extremo + reclaim + higher-low (ou lower-high) a SEGURAR "
    "≥2-3 barras fechadas + CHoCH 15M no sentido novo — sobretudo com o fundo/topo apoiado em demanda/supply "
    "4H/1D, é evidência de PERNA NOVA em formação e deve ser pesada como tal, NÃO descartada automaticamente "
    "como 'contra a perna'. Atenção ao rigor: um verde/vermelho isolado, um reclaim sem hold multi-barra, ou "
    "um fundo fora de zona HTF NÃO são sequência confirmada — continuam a ser faca/pullback (a regra do frame "
    "aplica-se por inteiro). A sequência confirmada não obriga a aprovar: é uma voz forte que entra na "
    "convergência com as restantes (absorção, RSI reset, espaço até ao íman).\n"
    "FADE EM SUPPLY COM SEQUÊNCIA (2026-08-03, clarificação da simetria short da regra acima): o espelho "
    "short da sequência confirmada — sweep do TOPO + ≥2 rejeições confirmadas na supply 4H/1D + lower-high a "
    "segurar — vale como voz forte MESMO que o CHoCH 15M ainda não tenha impresso, QUANDO o rótulo da perna "
    "1H está em DESACORDO com os próprios dados 1H (cabeçalho BULL mas trend/perna 1H DOWN). Nesse desacordo, "
    "o rótulo é o dado atrasado: não recuses só por 'contra a perna' — pesa a sequência na convergência. "
    "Rigor mantido: sem sweep do topo, com uma só rejeição, ou com rótulo e dados 1H de acordo no sentido "
    "bull e iniciativa compradora viva, a regra do frame aplica-se por inteiro (pullback, não reversão).\n"
    "CONTEXTO ESTRUTURAL 4H = MOLDURA (2026-08-14, auditoria dos 2 misses de 14/08 — recusaste o short do "
    "retest pós-sweep como 'contra-perna/1ª correção de perna up' E chamaste 'chop/absorção' ao reclaim de "
    "retomada): a secção '# CONTEXTO ESTRUTURAL 4H' do briefing (consome market_context.json + sweep_reject_guard) "
    "é voz de 1ª classe sobre a moldura, NÃO mais um número. Quando ela diz SWEEP-REJECT 4H ATIVO (distribuição "
    "no topo): o veto 'contra-perna' sobre SHORTS está SUSPENSO — um short na rejeição de um lower-high QUALIFICA "
    "(o 4H já imprimiu distribuição; o rótulo 'perna up' 1H é o dado ATRASADO), e um LONG dentro dessa moldura é "
    "FACA, não pullback comprável, até à quebra. Quando ela diz QUEBRA 15M DADA (HH+HL após o sweep): é RETOMADA "
    "— um long de estrutura (reclaim + higher-low a segurar) é LEGÍTIMO, NÃO o descartes como 'chop/absorção'. "
    "Rigor mantido: SEM a moldura de distribuição impressa na secção, a regra do frame aplica-se por inteiro "
    "(contra-perna = pullback).\n"
    "CONTINUAÇÃO EM COMPRESSÃO (2026-08-03): numa continuação COM-perna (frame e candidato do mesmo lado), "
    "compressão nas EMAs com estrutura MTF alinhada NÃO exige agressão vendedora prévia nem ADX vivo — em "
    "compressão, a agressão imprime DEPOIS do rompimento, não antes; 'ADX morto + CHOP' é o estado ESPERADO "
    "da pré-quebra, não prova de ausência de edge. Distingue com rigor: AUSÊNCIA de agressão (aceitável em "
    "compressão; não é voz contra) vs AGRESSÃO CONTRÁRIA ativa (buy-bubbles, iniciativa compradora, janela "
    "auction do lado buy — essa SIM é voz de veto plena). Guardas: só com-perna (nunca contra-perna), fora "
    "de janelas de evento, e a distância/espaço até ao alvo continua a pesar normalmente.\n"
    "A tua tarefa: julgar se as leituras (estrutura MTF 1D→15M, micro, auction/bubbles, macro, zonas HTF) "
    "CONVERGEM numa história coerente de ALTA PROBABILIDADE — ou não. Convergência NÃO é 'nenhuma leitura "
    "objeta'; convergência = as leituras APONTAM PARA O MESMO LADO e encadeiam uma causa (ex.: fundo de perna "
    "fresco + regime HTF a favor + climax de absorção + RSI reset + reclaim + demanda HTF logo abaixo). "
    "Contradição entre leituras = baixa probabilidade.\n"
    "Método OBRIGATÓRIO: pensa em voz alta ANTES de concluir — percorre a fita secção a secção (raciocínio "
    "primeiro, veredito depois). Nomeia explicitamente as leituras que se ALINHAM e as que estão em CONFLITO. "
    "Declara para que lado o CONTEXTO pende (independente do candidato) e só depois se o candidato se alinha.\n"
    "EQUILÍBRIO (crítico): o regime/trend HTF é UMA leitura entre várias, NÃO um veredito automático. Não há "
    "default direcional. Uma REVERSÃO em exaustão CONTRA o regime pode ser ALTA probabilidade quando converge "
    "(clímax + absorção/iniciativa das velas no sentido novo + íman HTF não-testado a favor + 1º-pullback já "
    "maduro); e uma CONTINUAÇÃO a favor do regime pode ser BAIXA probabilidade quando não converge (velas sem "
    "iniciativa, a subir para um íman contrário não-testado, 1º pullback de perna fresca que raramente reverte). "
    "Ambas as direções podem ser alta OU baixa prob — decide pela CONVERGÊNCIA real da fita, nunca pelo regime "
    "por defeito. NÃO favoreças reversões nem continuações; descreve o que converge.\n"
    "Três desfechos são TODOS legítimos e verdadeiros consoante a fita: alta convicção (converge), "
    "sem-edge/incoerente, ou genuinamente misto. NÃO és pago para aprovar nem para reprovar — és pago para "
    "DESCREVER A REALIDADE da imagem. A convicção é TUA, com o porquê; não há tabela de pontos a somar. "
    "Usa só o dossiê dado; não inventes números. Advisory para um humano, NUNCA uma ordem. "
    "Devolve SÓ um objeto JSON, nada de texto à volta."
)
# polaridade context-dependente das bubbles (fonte única, partilhada com claude_recheck — não podem divergir)
READ_SYS = READ_SYS + "\n\n" + BUBBLE_POLARITY_RULE
# VOZ LIQUIDEZ/MANIPULAÇÃO (Cris 2026-08-04, VOZ ON imediata — desenho B pós 2 falhas 04/08).
# Flag E2_LIQUIDITY_VOICE (default ON por ordem; =0 restaura READ_SYS + briefing byte-idênticos).
E2_LIQUIDITY_VOICE = os.environ.get("E2_LIQUIDITY_VOICE", "1") == "1"
if E2_LIQUIDITY_VOICE:
    from context_liquidity import LIQUIDITY_RULE
    READ_SYS = READ_SYS + "\n\n" + LIQUIDITY_RULE
SCHEMA_HINT = (
    "\n\nDevolve SÓ este JSON (raciocínio primeiro):\n"
    '{"reasoning":"<percorre a fita: estrutura MTF, micro, auction, macro, zonas — o que cada uma diz e como '
    'encadeiam>","context_direction":"LONG|SHORT|NONE","converges":true,'
    '"convergence":"high|moderate|low|incoherent","conviction":<INTEIRO 0-100 (nunca 0-1)>,'
    '"aligned_readings":["..."],"conflicting_readings":["..."],'
    '"candidate_fit":"aligned|against|orthogonal","thesis":"<uma frase: a história de alta-prob, ou \'sem edge '
    'coerente\'>","invalidation":"<o que na fita quebra a tese>"}'
)


def _extract_json(text):
    import re
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None


def _z(z):
    if not z: return "—"
    return f"{fmt(z.get('low'))}–{fmt(z.get('high'))} ({z.get('src','?')})"


def _sw(s):
    if not s: return "—"
    return f"{fmt(s.get('price'))}@bar{s.get('bar')}(conf{s.get('confirm_bar')})"


def _frame_leg(ax):
    """PERNA 1H p/ o FRAME — CONSOME o leitor aprovado do price-shock (_leg_1h, Cris 2026-07-24: pivô 1H
    mais recente confirmado pelo reclaim/perda das EMAs; discórdia = mantém dominante). Fallback local
    fiel se o import falhar (mesma lógica, nunca outra)."""
    try:
        sys.path.insert(0, str(REPO / "my-strategy" / "core" / "price_shock"))
        from price_shock_cycle import _leg_1h
        return _leg_1h(ax)
    except Exception:
        m = (ax.get("mtf") or {}).get("60") or {}
        sw = m.get("swings") or {}
        lh = (sw.get("last_high") or {}).get("confirm_bar"); ll = (sw.get("last_low") or {}).get("confirm_bar")
        ema = ((ax.get("micro_15m") or {}).get("ema") or {}).get("pos")
        if lh is None or ll is None: return "RANGE", "sem swings 1H"
        pb = "up" if ll > lh else "down"
        ec = "up" if ema == "above" else ("down" if ema == "below" else None)
        if pb == "up" and ec == "up": return "BULL", "pivô-low + reclaim EMAs"
        if pb == "down" and ec == "down": return "BEAR", "pivô-high + perda EMAs"
        ld = (m.get("leg") or {}).get("dir")
        return ("BEAR", "dominante down") if ld == "down" else (("BULL", "dominante up") if ld == "up" else ("RANGE", "indefinido"))


def _swing_state(mtf):
    """ESTADO DA PERNA por TF via sequência LH/LL — INFORMAÇÃO PURA (Cris 2026-08-14), NÃO é gate/gatilho.
    Prioridade 1H→4H→15M. CONSOME axes.mtf[tf].swings (last/prev high/low do context_structure) — não
    recomputa nem inventa. Torna explícita a sequência (LOWER-HIGH/LOWER-LOW → DOWN) e os níveis de quebra,
    que hoje o reader recebe só como valores soltos. O read pesa isto contra o preço vivo (leitura holística)."""
    out = []
    for tf, lbl in (("60", "1H"), ("240", "4H"), ("15", "15M")):
        sw = (mtf.get(tf) or {}).get("swings") or {}
        lh = (sw.get("last_high") or {}).get("price"); ph = (sw.get("prev_high") or {}).get("price")
        ll = (sw.get("last_low") or {}).get("price"); pl = (sw.get("prev_low") or {}).get("price")
        if lh is None or ll is None:
            out.append(f"  [{lbl}] swings insuficientes"); continue
        hi_seq = "LOWER-HIGH" if (ph is not None and lh < ph) else ("higher-high" if (ph is not None and lh > ph) else "=")
        lo_seq = "LOWER-LOW" if (pl is not None and ll < pl) else ("higher-low" if (pl is not None and ll > pl) else "=")
        if ph is not None and pl is not None and lh < ph and ll < pl:
            st = "DOWN (LH+LL)"
        elif ph is not None and pl is not None and lh > ph and ll > pl:
            st = "UP (HH+HL)"
        else:
            st = "RANGE/misto"
        out.append(f"  [{lbl}] {st} | high {fmt(lh)} ({hi_seq} vs {fmt(ph)}) · low {fmt(ll)} ({lo_seq} vs {fmt(pl)}) "
                   f"| quebra↑ fechar>{fmt(lh)} · continua↓ perder {fmt(ll)}")
    return out


def _sweep_context():
    """CONTEXTO ESTRUTURAL 4H (Cris 2026-08-14) — INFORMAÇÃO pura (NÃO gate). Secção do render_composite, que
    CONSOME o dossiê E0 market_context.json; aqui consome o verdict de sweep_reject_guard (que lê o mesmo store
    nativo) — não reconstrói reader nem inventa. Dá ao reader a moldura HTF que faltava (2 misses de 14/08):
    sweep-reject 4H ATIVO = distribuição no topo (short na rejeição de lower-high legítimo, long=faca até
    quebra 15M); quebra de estrutura 15M dada = retomada (long estrutural). Fail-safe: erro/ausente = 0 linhas."""
    try:
        import sweep_reject_guard as SRG
        v = SRG.verdict()
    except Exception:
        return []
    if not v or v.get("sweep_t") is None:
        return ["  sem sweep-reject 4H recente — sem moldura de distribuição ativa."]
    import datetime as _dt
    def _h(t):
        try:
            return _dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
        except Exception:
            return "?"
    if v.get("block"):
        return [f"  ⚠️ SWEEP-REJECT 4H ATIVO (vela {_h(v.get('sweep_t'))}, high {v.get('sweep_high')}) = DISTRIBUIÇÃO no topo.",
                "     → SHORT na rejeição de lower-high = LEGÍTIMO (NÃO 'contra-perna'). LONG dentro disto = faca.",
                "     → ainda SEM quebra de estrutura 15M (HH+HL) desde o sweep — longs só após a quebra."]
    return [f"  SWEEP-REJECT 4H resolvido — 15M QUEBROU estrutura (HH+HL) em {_h(v.get('break15_t'))}.",
            "     → RETOMADA: long de estrutura legítimo; moldura de distribuição invalidada."]


def render_composite(dsr, cand):
    """Serializa o dossiê E0 INTEIRO como briefing rotulado top-down (NÃO json cru, NÃO migalha).
    O read lê isto como um trader lê a fita, secção a secção. FRAME-EXPLÍCITO no topo (Cris 2026-07-25/26):
    a perna 1H é o enquadramento de 1ª classe; as outras vozes leem-se CONTRA ela; grau = convergência."""
    ax = dsr.get("axes", {}); mtf = ax.get("mtf", {}) or {}
    micro = ax.get("micro_15m", {}) or {}; macro = ax.get("macro", {}) or {}
    # AGRESSÃO/LIQUIDEZ FRESCAS (Cris 2026-08-04): o dossiê pode estar 1 ciclo atrasado — isso atrasava
    # pontos de entrada/sinais. SÓ no caminho LIVE (dossiê com cycle_ts recente) recalculamos do store no
    # instante do read; em replay/selftest (cycle antigo/sintético) usa-se o dossiê = byte-idêntico.
    import time as _time
    _live_read = abs(_time.time() - float((dsr.get("_meta") or {}).get("cycle_ts", 0) or 0)) < 600
    conf = (ax.get("confluence") or {}).get("15", {}) or {}
    if _live_read:
        try:
            from context_confluence import read_confluence_store as _rcs
            _fresh_conf = _rcs("15")
            if _fresh_conf:
                conf = _fresh_conf
        except Exception:
            pass
    L = []
    d = cand.get("direction"); m = cand.get("materiality", {}) or {}
    leg, why = _frame_leg(ax)
    fav, pull = ("demandas", "supplies") if leg == "BULL" else (("supplies", "demandas") if leg == "BEAR" else ("—", "—"))
    L.append(f"# FRAME (lê TUDO contra isto): PERNA 1H = {leg} ({why})")
    if leg in ("BULL", "BEAR"):
        L.append(f"  regra das zonas: com-perna → {fav} = continuação (caso-base) · {pull} de 15M/1H contra-perna "
                 f"= pullback, NÃO reversão · reversão contra a perna SÓ em supply/demand 4H/1D com confluências de exaustão.")
    else:
        L.append("  perna indefinida (RANGE): sem caso-base direcional — exige convergência clara num dos lados.")
    # ESTADO DA PERNA — swings LH/LL por TF (Cris 2026-08-14): INFORMAÇÃO estrutural pura, prioridade
    # 1H→4H→15M. NÃO é gate. Torna explícita a sequência e os níveis de quebra que o reader hoje só recebe soltos.
    L.append("\n# ESTADO DA PERNA (swings LH/LL, prioridade 1H→4H→15M — informação, NÃO gate)")
    L.extend(_swing_state(mtf))
    # CONTEXTO ESTRUTURAL 4H (Cris 2026-08-14): moldura HTF de distribuição/retomada consumindo o
    # market_context.json + sweep_reject_guard — INFORMAÇÃO pura, não gate.
    L.append("\n# CONTEXTO ESTRUTURAL 4H (sweep-reject/distribuição/retomada — informação, NÃO gate)")
    L.extend(_sweep_context())
    # MAPA DO TRADER (Cris 2026-08-04): voz de 1ª classe logo após o FRAME. SEM mapa = zero linhas
    # (byte-idêntico ao anterior — regressão (d) do accept_mapa_trader_20260804).
    try:
        import trader_map as _TM
        _tmap = _TM.load_map()
        if _tmap:
            L.append(_TM.render_section(_tmap))
    except Exception:
        pass
    # LIQUIDEZ/MANIPULAÇÃO (Cris 2026-08-04): voz de 1ª classe. Sem flag = zero linhas.
    # FRESCA no instante do read (recalcula do store — bars + agressão frescas), NÃO o snapshot do dossiê
    # que estava 1 ciclo atrasado (o que te atrasava nos pontos de entrada). Fallback ao dossiê se store off.
    if E2_LIQUIDITY_VOICE:
        try:
            import context_liquidity as _CL
            _liq = None
            if _live_read:
                _liq = _CL.read_liquidity(magnets=ax.get("magnets"), mtf=mtf,
                                          amd=ax.get("amd_setup"), window=conf.get("window"))
            if _liq is None:
                _liq = (dsr.get("axes") or {}).get("liquidity")
            if _liq:
                L.append(_CL.render_section(_liq))
        except Exception:
            pass
    L.append(f"\n# CANDIDATO: {d} {cand.get('rule')} @TF{cand.get('tf')}")
    L.append(f"  entry {fmt(cand.get('entry'))} | SL {fmt(cand.get('sl'))} | alvo {fmt(cand.get('target'))} "
             f"| R:R {fmt(cand.get('rr'),1)} | SL {fmt(m.get('sl_atr'),1)}×ATR | regime HTF {regime(dsr)}")
    if cand.get("src"):
        # descritores do gatilho (ex. R9: perna→zona/toque#/janela buy-sell) — qualidade do setup p/ o read
        L.append(f"  gatilho: {cand['src']}")
    L.append(f"  (o E1 disparou por: confluência {m.get('confluence')} {m.get('confluence_breakdown', {})})")
    L.append("\n# ESTRUTURA MTF (top-down; pivots CONFIRMADOS confirm_bar≤i, close-only, NÃO repinta)")
    for tf, lbl in (("1D", "1D"), ("240", "4H"), ("60", "1H"), ("15", "15M")):
        t = mtf.get(tf, {}) or {}
        leg = t.get("leg", {}) or {}; ch = t.get("choch", {}) or {}
        sw = t.get("swings", {}) or {}; zo = t.get("zones", {}) or {}; svp = t.get("svp", {}) or {}
        L.append(f"  [{lbl}] trend {t.get('trend')} | perna {leg.get('dir')} {fmt(leg.get('low'))}→{fmt(leg.get('high'))} "
                 f"pos_na_perna {fmt(leg.get('pos_in_leg'),2)} ({fmt(leg.get('mag_atr'),1)}×ATR) | "
                 f"CHoCH up={ch.get('up')} dn={ch.get('dn')}")
        L.append(f"       swings: LH {_sw(sw.get('last_high'))} LL {_sw(sw.get('last_low'))} "
                 f"| zona acima {_z(zo.get('above'))} | zona abaixo {_z(zo.get('below'))}"
                 + (f" | svp {svp.get('pressure')}" if svp.get('pressure') else ""))
    L.append("\n# MICRO 15M")
    ema = micro.get("ema", {}) or {}; dmi = micro.get("dmi", {}) or {}; nas = micro.get("nas", {}) or {}
    L.append(f"  close {fmt(micro.get('close'))} | EMA9 {fmt(ema.get('ema9'))} EMA21 {fmt(ema.get('ema21'))} "
             f"EMA50 {fmt(ema.get('ema50'))} (preço {ema.get('pos')})")
    L.append(f"  RSI {fmt(micro.get('rsi'),1)} (MA {fmt(micro.get('rsi_ma'),1)}) | ADX {fmt(dmi.get('adx'),1)} "
             f"+DI {fmt(dmi.get('plus_di'),1)} -DI {fmt(dmi.get('minus_di'),1)} | CHOP {fmt(micro.get('chop'),1)}")
    L.append(f"  NAS bottom {nas.get('bottom')} top {nas.get('top')} dist_EMA {fmt(nas.get('dist_ema_atr'),2)}×ATR")
    cnd = micro.get("candles") or {}; vit = micro.get("vitality") or {}; vsn = micro.get("volume_session") or {}
    if cnd:
        seq = " ".join(f"{(b.get('dir') or '?')[:2]}{fmt(b.get('body_atr'),2)}" for b in (cnd.get("bars") or []))
        L.append(f"  velas(últ{cnd.get('window_bars')}): iniciativa {cnd.get('dominant')} | "
                 f"força ↑{fmt(cnd.get('up_force_atr'),2)} ↓{fmt(cnd.get('dn_force_atr'),2)} | {seq}")
    if vit:
        L.append(f"  vitalidade: ratio {fmt(vit.get('ratio'),2)} ({vit.get('label')}) — range recente vs ATR")
    if vsn:
        L.append(f"  vol sessão: up {fmt(vsn.get('up'),0)} / dn {fmt(vsn.get('dn'),0)} (ratio {fmt(vsn.get('ratio'),2)})")
    L.append("\n# AUCTION / CONFLUÊNCIA 15M (ativação de bubbles ao longo da perna)")
    L.append("  (lê a polaridade destas bubbles pela BUBBLE POLARITY RULE do sistema: em reversal-em-fundo/demanda "
             "SELL-absorvido = BULLISH e BUY = anti-padrão; em pullback-uptrend BUY = bullish; em reversal-em-topo "
             "BUY-absorvido = bearish. Exige reclaim/hold >=2 barras p/ 'absorção'; vertical news-driven = faca, não absorção.)")
    L.append(f"  perna {conf.get('leg_dur_bars','—')} barras | buy_dens {fmt(conf.get('buy_dens'),2)} "
             f"sell_dens {fmt((conf.get('sell') or {}).get('dens'),2)} | act_dens {fmt(conf.get('act_dens'),2)} "
             f"| leg_sell {conf.get('leg_sell','—')} | nas_n {conf.get('nas_n','—')}")
    win = conf.get("window") or {}
    if win:
        wb = win.get("buy", {}) or {}; ws = win.get("sell", {}) or {}
        L.append(f"  janela(últ{win.get('bars')} barras, iniciativa recente): buy {wb.get('n')}/{wb.get('weight')} · "
                 f"sell {ws.get('n')}/{ws.get('weight')} → lado {win.get('net_side')}")
    # ---- F-A2: mapa de ímanes (voz descritiva; NÃO sinal) ----
    mag = (dsr["axes"].get("magnets") or {})
    if mag:
        pb = mag.get("pullback") or {}
        def _mstr(items):
            return " · ".join(f"{m.get('type')} {fmt(m.get('dist_atr'),1)}ATR"
                              + (f"({m.get('touches')}t)" if m.get('touches') else "")
                              + (f"[{m.get('size_atr')}ATR]" if m.get('size_atr') else "")
                              for m in (items or [])) or "—"
        L.append("\n# ÍMANES (mapa acima/abaixo — vazios FVG não-mitigados + clusters liquidez + OB; distância em ATR)")
        L.append(f"  ACIMA: {_mstr(mag.get('above'))}")
        L.append(f"  ABAIXO: {_mstr(mag.get('below'))}")
        if pb:
            L.append(f"  perna: {pb.get('leg_dir')} · pullback #{pb.get('ordinal')} ({pb.get('maturity')})")
    L.append("\n# MACRO")
    reg = (dsr["axes"].get("regime") or {})
    v5 = reg.get("v5_4h") or {}; l1 = reg.get("structural_1d") or {}
    L.append(f"  regime (vozes convergentes — NÃO é veto, compõem UMA imagem): v5-4H={v5.get('regime')} "
             f"(as_of {v5.get('as_of')}) · Layer1-1D estrutural={l1.get('regime')} (as_of {l1.get('as_of')}) "
             f"· proxy-MTF={regime(dsr)}")
    amd = (dsr["axes"].get("amd_setup") or {})
    if amd.get("active"):
        cs = amd.get("candidates") or []
        L.append(f"  🎯 AMD SETUP ATIVO (H4 sweep, voz advisory NÃO-veto): {amd.get('dir','').upper()} · varreu "
                 f"{amd.get('level_kind')} {amd.get('level')} · bias {amd.get('bias')} · killzone {amd.get('killzone')} "
                 f"· {len(cs)} candidatos FVG/OB 1H" + (f" (melhor R {min((c.get('R') or 99) for c in cs)})" if cs else ""))
    ng = macro.get("news_gate", {}) or {}
    L.append(f"  sessão {ng.get('session')} | risco {macro.get('risk_level')} | real_yield10y "
             f"{fmt(macro.get('real_yield_10y'))} | USD {fmt(macro.get('usd_broad'))} | VIX {fmt(macro.get('vix'))}")
    L.append(f"  news_gate: HI_now={ng.get('high_impact_now')} ff_event_le_min={ng.get('ff_event_le_min')} "
             f"| {ng.get('advisory','')}")
    imm = macro.get("imminent_events", []) or []
    if imm: L.append(f"  eventos iminentes: {imm}")
    sh = dsr.get("source_health", {})
    L.append(f"\n# SAÚDE: " + " ".join(f"{k}={sh.get(k,{}).get('status')}(age{sh.get(k,{}).get('age_s','?')}s)"
             for k in ("mtf", "micro_15m", "macro", "confluence")))
    return "\n".join(L)


def _read_sdk(prompt, model=None):
    """FASE 3 (2026-07-18): leitura via Anthropic SDK direto (sem claude -p). SÓ ativa com
    E2_READ_VIA=sdk E ANTHROPIC_API_KEY presente — API paga à parte da sessão Max; decisão Cris.
    Retries/timeout nativos do SDK; adaptive thinking; mesma tese JSON."""
    import anthropic
    client = anthropic.Anthropic()          # exige ANTHROPIC_API_KEY no env do daemon
    msg = client.messages.create(
        model=model or READ_MODEL,
        max_tokens=2000,
        thinking={"type": "adaptive"},
        system=READ_SYS,
        messages=[{"role": "user", "content": prompt}],
    )
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    v = _extract_json(txt)
    if not v or "convergence" not in v:
        return {"error": "sem tese", "raw": txt[:300]}
    return v


def run_read(cand, dsr, timeout=None, model=None):
    """UMA leitura contextual (Opus) com RETRY (Cris 2026-07-24: 4 reads do dia-1 falharam por
    'claude is_error' transitório e escreveram branco). 3 tentativas com backoff; só devolve erro se todas
    falharem. Não agrega, não pontua."""
    last = {"error": "read não corrido"}
    for attempt in range(3):
        v = _read_once(cand, dsr, timeout, model)
        if isinstance(v, dict) and not v.get("error"):
            # normalização defensiva da convicção p/ escala única 0-100 (obs 2026-07-27: 33 vs 0.3)
            cv = fnum(v.get("conviction"))
            if cv is not None:
                v["conviction"] = int(round(cv * 100)) if 0 <= cv <= 1 else int(round(cv))
            return v
        last = v
        time.sleep(2 * (attempt + 1))          # backoff p/ erro transitório do SDK/CLI
    return last


def _read_once(cand, dsr, timeout=None, model=None):
    """Uma tentativa de leitura. Via: E2_READ_VIA=sdk (Anthropic SDK) | default cli (claude -p, sessão Max)."""
    import subprocess
    image = render_composite(dsr, cand)
    prompt = image + SCHEMA_HINT
    if os.environ.get("E2_READ_VIA") == "sdk" and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _read_sdk(prompt, model)
        except Exception as e:
            return {"error": f"sdk {type(e).__name__}:{str(e)[:100]}"}
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None)
    try:
        r = subprocess.run([CLAUDE_EXE, "-p", prompt, "--append-system-prompt", READ_SYS,
                            "--output-format", "json", "--model", model or READ_MODEL],
                           capture_output=True, text=True, timeout=timeout or READ_TIMEOUT, env=env)
        env_out = json.loads(r.stdout or "{}")
        if env_out.get("is_error"): return {"error": "claude is_error", "raw": (r.stderr or "")[:200]}
        v = _extract_json(env_out.get("result", ""))
        if not v or "convergence" not in v:
            return {"error": "sem tese", "raw": (env_out.get("result") or "")[:300]}
        return v
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:100]}"}


def surfaced(thesis, cand):
    """Rótulo binário a jusante = PASSTHROUGH PRINCÍPIO (definido 1×, nunca afinado a dado visível):
    o contexto converge E aponta para o mesmo lado do candidato. Advisory/shadow — 0 Telegram por agora."""
    if not isinstance(thesis, dict) or thesis.get("error"): return None
    return bool(thesis.get("converges")) and thesis.get("context_direction") == cand.get("direction")


def _buy_initiative(dsr):
    """Iniciativa compradora presente: janela F-A1 net buy (se disponível) OU fita da perna compradora
    (buy_dens>0 e sem venda). Lido do dossiê, nunca inventado."""
    cf = (dsr["axes"].get("confluence") or {}).get("15", {}) or {}
    win = cf.get("window") or {}
    if win:
        return (win.get("net_side") == "buy") or ((win.get("buy") or {}).get("weight", 0) > (win.get("sell") or {}).get("weight", 0))
    bd = fnum(cf.get("buy_dens")); sd = fnum((cf.get("sell") or {}).get("dens"))
    return bool(bd and bd > 0 and (sd is None or sd == 0))


def cont_signal_ok(cand, dsr):
    """Gate DETERMINÍSTICO do sinal de continuação LONG. TODOS obrigatórios: LONG · regra de continuação ·
    RR>=2 · 1H (ou 15M) UP · iniciativa BUY. NÃO usa o read LLM (o regime atrasado silenciaria continuações)."""
    if cand.get("direction") != "LONG" or cand.get("rule") not in CONT_RULES:
        return False
    if (fnum(cand.get("rr")) or 0) < MIN_RR_SIGNAL:
        return False
    mtf = dsr["axes"].get("mtf", {})
    if (mtf.get("60", {}) or {}).get("trend") != "UP" and (mtf.get("15", {}) or {}).get("trend") != "UP":
        return False
    return _buy_initiative(dsr)


def emit_cont_signal(cand, dsr, thesis):
    """Envia sinal LONG de continuação ao Telegram (alarme 3-5×). Alert-only. Loga em cont_signals.jsonl.
    Reusa tg_trade_signal (mesmo bot/chat; tokens no .env, nunca expostos)."""
    from tg_trade_signal import send_trade_signal
    e = fnum(cand.get("entry")); sl = fnum(cand.get("sl")); tgt = fnum(cand.get("target"))
    r = abs(e - sl); tp2 = round(e + 2 * r, 2)
    conv = (thesis or {}).get("convergence") if isinstance(thesis, dict) else None
    reason = (f"CONTINUACAO LONG {cand.get('rule')} {cand.get('tf')} | 1H UP + iniciativa BUY | RR {cand.get('rr')}"
              + (f" | read {conv}" if conv else ""))
    res = send_trade_signal("LONG", e, sl, tp2, tgt, reason, test=False, repeat=3)
    append(LOGS / "cont_signals.jsonl", {"ts": now_iso(), "candidate_id": cand.get("id"), "rule": cand.get("rule"),
           "tf": cand.get("tf"), "entry": e, "sl": sl, "target": tgt, "rr": cand.get("rr"), "tp2": tp2,
           "reason": reason, "read_convergence": conv, "telegram": res})
    return res


# ---------- veredito ----------
def make_verdict(cand, dsr, drift_c):
    grade, vs, hard, soft = evaluate_vetos(cand, dsr, drift_c)
    sh = dsr.get("source_health", {})
    return {"candidate_id": cand.get("id"), "ts": now_iso(), "cycle_ts": cand.get("cycle_ts"),
            "bar_time": cand.get("bar_time"), "direction": cand.get("direction"), "rule": cand.get("rule"),
            "tf": cand.get("tf"), "grade": grade, "veto": (hard[0]["name"] if hard else None),
            "vetos_all": vs, "read": None, "surfaced": None, "dossier_drift_cycles": drift_c,
            "source_health": {k: sh.get(k, {}).get("status") for k in ("mtf", "micro_15m", "macro")},
            "levels": {"entry": cand.get("entry"), "sl": cand.get("sl"), "target": cand.get("target"), "rr": cand.get("rr")}}


def archive_read(cand, dsr, image, thesis, drift_c, source):
    """Arquivamento append-only atómico: imagem + tese verbatim + model-id datado + read_version.
    outcome preenchido dias depois por e2_outcome_backfill.py. Substrato do painel de calibração."""
    rec = {"ts": now_iso(), "read_version": READ_VERSION, "model": READ_MODEL, "source": source,
           "candidate": {k: cand.get(k) for k in ("id", "rule", "tf", "direction", "entry", "sl", "target",
                                                  "rr", "bar_time", "cycle_ts", "materiality")},
           "dossier": dsr, "image": image, "drift_cycles": drift_c,
           "thesis": thesis, "surfaced": surfaced(thesis, cand), "outcome": None}
    with open(SHADOW_F, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def is_material(c):
    return c.get("suppressed") is None and c.get("materiality", {}).get("pass") is True


def load_dossier():
    try: return json.loads(DOSSIER.read_text())
    except Exception: return None


def drift_cycles(cand, dsr):
    dc = dsr.get("_meta", {}).get("cycle_ts"); cc = cand.get("cycle_ts")
    if dc and cc: return round((dc - cc) / CFG["CYCLE_S"])
    return None


def append(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ---------- CLI ----------
def cli_once():
    dsr = load_dossier()
    if not dsr: print("sem dossiê vivo"); return
    n = 0
    for line in CAND_F.read_text().splitlines() if CAND_F.exists() else []:
        try: c = json.loads(line)
        except Exception: continue
        if not is_material(c): continue
        v = make_verdict(c, dsr, drift_cycles(c, dsr)); append(VERD_F, v); n += 1
        print(f"  {v['direction']} {v['rule']} {v['tf']} -> {v['grade']}" + (f" [veto {v['veto']}]" if v['veto'] else ""))
    print(f"processados {n} materiais (nota: dossiê vivo pode ter derivado dos candidatos históricos)")


def cli_survey(use_replay):
    if not use_replay:
        print("--survey sem --replay: usa o dossiê vivo (deriva alta). Preferir --replay."); return
    import e1_replay, e1_detector as e1
    data = e1_replay.capture()
    d15 = data["15"]; N = len(d15["C"]); start = max(45, N - 120)
    from collections import Counter
    surv = Counter(); killed = Counter(); total = 0; prev = None
    for i in range(start, N):
        dsr = e1_replay.synth(data, i)
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr); c["cycle_ts"] = dsr["_meta"]["cycle_ts"]
            if not is_material(c): continue
            total += 1
            grade, vs, hard, soft = evaluate_vetos(c, dsr, 0)
            if grade == "survivor": surv[f"{c['direction']}/{c['rule']}"] += 1
            elif hard: killed[hard[0]["name"]] += 1
        prev = dsr
    print(f"=== SURVEY (replay de hoje, GATE 4 vetos) ===\n materiais: {total} | sobreviventes: {sum(surv.values())} | mortos: {sum(killed.values())}")
    print(" sobreviventes:", dict(surv), "\n mortos por veto:", dict(killed))
    print(f" -> ~{sum(surv.values())} reads Opus/dia neste dia (tendência forte).")


def cli_read_smoke(n_max):
    """SMOKE do read novo sobre sobreviventes do replay de HOJE. NÃO é validação (dia visível, imagem
    DEGRADADA pelo synth). Só confirma: (1) Opus devolve tese válida, (2) não colapsa em reject-all/pass-all.
    Arquiva em logs/e2_shadow.jsonl com source='replay-degraded' (separável do live no painel)."""
    import e1_replay, e1_detector as e1, bisect
    data = e1_replay.capture()
    d15 = data["15"]; T, H, L, C = d15["T"], d15["H"], d15["L"], d15["C"]; N = len(C); start = max(45, N - 120)
    state = {"cooldown": {}, "dedup": {}}; prev = None; surv = []
    for i in range(start, N):
        dsr = e1_replay.synth(data, i); t = dsr["_meta"]["cycle_ts"]
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr); c["cycle_ts"] = t; c["bar_time"] = t
            if not is_material(c): continue
            if e1.anti_spam(c, state, t): continue
            g, vs, hard, soft = evaluate_vetos(c, dsr, 0)
            if g != "survivor": continue
            state["cooldown"][f"{c['rule']}:{c['tf']}:{c['direction']}"] = t
            state["dedup"][e1.cand_hash(c)] = t
            surv.append((c, dsr))
        prev = dsr
    if n_max: surv = surv[:n_max]
    print(f"SMOKE: {len(surv)} sobreviventes (imagem DEGRADADA-replay) — a correr read Opus...\n")

    def outcome(dir_, entry, sl, tgt, t0, horizon=192):
        i0 = bisect.bisect_right(T, t0) - 1
        for k in range(i0 + 1, min(len(T), i0 + 1 + horizon)):
            if dir_ == "LONG":
                if L[k] <= sl: return "LOSS"
                if H[k] >= tgt: return "WIN"
            else:
                if H[k] >= sl: return "LOSS"
                if L[k] <= tgt: return "WIN"
        return "OPEN"
    from collections import Counter
    dist = Counter()
    for c, dsr in surv:
        o = outcome(c["direction"], c["entry"], c["sl"], c["target"], c["bar_time"])
        th = run_read(c, dsr)
        if th.get("error"):
            print(f"  ERR {c['direction']} {c['rule']}/{c['tf']}: {th['error']}"); continue
        archive_read(c, dsr, render_composite(dsr, c), th, 0, "replay-degraded")
        cv = th.get("convergence"); cn = th.get("conviction"); sf = surfaced(th, c)
        dist[(cv, o)] += 1
        print(f"  {c['direction']:5} {c['rule']:13}/{c['tf']:3} out={o:4} -> conv={cv:10} "
              f"convic={cn} dir={th.get('context_direction')} surf={sf}")
        print(f"        tese: {th.get('thesis','')[:150]}")
    print("\n=== distribuição convergence × outcome (SMOKE, NÃO valida — dia visível) ===")
    for k, n in sorted(dist.items()): print(f"  {k}: {n}")
    print("Sanidade: NÃO deve ser tudo 'high' (pass-all) nem tudo 'incoherent' (reject-all). Árbitro real = shadow-live multi-dia.")


def cli_anchors():
    import e1_replay, e1_detector as e1
    data = e1_replay.capture(); d15 = data["15"]; N = len(d15["C"]); start = max(45, N - 120)
    peak_i = max(range(start, N), key=lambda k: d15["C"][k]); prev = None; a_pass = False
    for i in range(start, N):
        dsr = e1_replay.synth(data, i)
        # replay = preço-only, sem bubbles; injeta atividade presente p/ o novo gate neutro act_dens (2026-07-18)
        dsr["axes"].setdefault("confluence", {}).setdefault("15", {}).setdefault("act_dens", 0.4)
        for c in e1.detect(dsr, prev):
            atr = e1.atr_of((dsr["axes"]["mtf"].get(c["tf"], {}) or {}).get("leg") or {})
            c["materiality"] = e1.materiality(c, dsr, atr); c["cycle_ts"] = dsr["_meta"]["cycle_ts"]
            if is_material(c) and c["direction"] == "SHORT" and i >= peak_i:
                grade, vs, hard, soft = evaluate_vetos(c, dsr, 0)
                if grade == "survivor": a_pass = True
        prev = dsr
    print(f"ANCHOR A (short-de-hoje sobrevive o GATE): {'PASS' if a_pass else 'FALHA'}")
    # ANCORA B (2026-07-26): candidato de sessão morta sobrevive o gate LIMPO — session_vacuum e chase
    # foram REMOVIDOS do sistema; nenhum registo deles pode existir nos vetos.
    b = {"direction": "LONG", "rule": "ema_reclaim", "tf": "15", "entry": 4035.3, "sl": 4027.0,
         "target": 4051.9, "rr": 2.0, "materiality": {"sl_atr": 1.0, "confluence": 3}}
    bd = {"_meta": {"cycle_ts": 1}, "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}, "macro": {"status": "fresh"}},
          "axes": {"mtf": {"1D": {"trend": "DOWN"}, "240": {"trend": "DOWN"}},
                   "micro_15m": {"close": 4035.3, "rsi": "45"},
                   "macro": {"risk_level": "normal", "imminent_events": [], "news_gate": {"session": "dead_zone", "high_impact_now": False, "ff_event_le_min": None}}}}
    grade, vs, hard, soft = evaluate_vetos(b, bd, 0)
    fired = [v["name"] for v in vs if v["fired"]]
    names = [v["name"] for v in vs]
    b_pass = grade == "survivor" and "session_vacuum" not in names and "chase" not in names
    print(f"ANCHOR B (sessão-morta sobrevive gate limpo, sem vacuum/chase no sistema): {'PASS' if b_pass else 'FALHA'} (grade {grade}, fired {fired})")
    ok = a_pass and b_pass
    print("ÂNCORAS:", "PASS" if ok else "FALHA")
    return 0 if ok else 1


def cli_selftest():
    base_d = {"_meta": {"cycle_ts": 1}, "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}, "macro": {"status": "fresh"}},
              "axes": {"mtf": {"1D": {"trend": "DOWN"}, "240": {"trend": "DOWN"}, "15": {"leg": {"low": 90, "high": 110, "mag_atr": 2.0, "pos_in_leg": 0.5}}},
                       "micro_15m": {"close": 100, "rsi": "45"},
                       "macro": {"risk_level": "normal", "imminent_events": [], "news_gate": {"session": "ny", "high_impact_now": False, "ff_event_le_min": None}}}}
    cand = {"direction": "LONG", "rule": "ema_reclaim", "tf": "15", "rr": 3.0, "materiality": {"sl_atr": 1.0, "confluence": 4}}
    r = []
    dv = json.loads(json.dumps(base_d)); dv["axes"]["macro"]["news_gate"]["session"] = "dead_zone"
    r.append(("bad_rr fire(rr1)", veto_bad_rr({**cand, "rr": 1.0}, base_d)["fired"] is True))
    r.append(("bad_rr no-fire(rr3)", veto_bad_rr(cand, base_d)["fired"] is False))
    ds = json.loads(json.dumps(base_d)); ds["source_health"]["mtf"]["status"] = "stale"
    r.append(("stale fire", veto_stale(cand, ds, 0)["fired"] is True))
    r.append(("GATE 2-vetos survivor(limpo)", evaluate_vetos(cand, base_d, 0)[0] == "survivor"))
    # 2026-07-26: session_vacuum e chase REMOVIDOS — sessão morta e SL largo passam o gate (juízo = READ)
    r.append(("GATE survivor(dead_zone, sem vacuum no sistema)", evaluate_vetos(cand, dv, 0)[0] == "survivor"))
    r.append(("GATE survivor(sl_atr 2.0, sem chase no sistema)",
              evaluate_vetos({**cand, "materiality": {"sl_atr": 2.0, "confluence": 4}}, base_d, 0)[0] == "survivor"))
    vetonames = [v["name"] for v in evaluate_vetos(cand, base_d, 0)[1]]
    r.append(("vetos = só bad_rr+stale", vetonames == ["bad_rr", "stale_dossier"]))
    # renderer não rebenta com dossiê real nem mínimo
    try:
        _ = render_composite(base_d, cand); _ = render_composite(load_dossier() or base_d, cand)
        r.append(("render_composite ok", True))
    except Exception as e:
        r.append((f"render_composite ok ({e})", False))
    # F-A1: renderer expõe candles/vitality/volume_session/window quando presentes
    try:
        de = json.loads(json.dumps(base_d))
        de["axes"]["micro_15m"]["candles"] = {"window_bars": 4, "up_force_atr": 0.2, "dn_force_atr": 1.1,
                                              "dominant": "sell", "bars": [{"dir": "down", "body_atr": 0.5, "range_atr": 0.8}]}
        de["axes"]["micro_15m"]["vitality"] = {"ratio": 0.5, "label": "low", "k": 4}
        de["axes"]["micro_15m"]["volume_session"] = {"up": 3.0, "dn": 6.0, "ratio": 0.5}
        de["axes"]["confluence"] = {"15": {"window": {"bars": 4, "buy": {"n": 0, "weight": 0},
                                                      "sell": {"n": 2, "weight": 3}, "net_side": "sell"}}}
        img = render_composite(de, cand)
        r.append(("render F-A1 fields ok", "velas(" in img and "vitalidade:" in img and "janela(" in img))
    except Exception as e:
        r.append((f"render F-A1 fields ({e})", False))
    # F-A2: renderer expõe o mapa de ímanes + pullback quando presente
    try:
        dm = json.loads(json.dumps(base_d))
        dm["axes"]["magnets"] = {"above": [{"type": "fvg", "dist_atr": 0.8, "size_atr": 0.4, "age": 5}],
                                 "below": [{"type": "liq_cluster", "dist_atr": 1.2, "touches": 3}],
                                 "pullback": {"leg_dir": "up", "ordinal": 1, "maturity": "continuação_provável"}}
        img2 = render_composite(dm, cand)
        r.append(("render F-A2 magnets ok", "ÍMANES" in img2 and "ACIMA:" in img2 and "pullback #" in img2))
    except Exception as e:
        r.append((f"render F-A2 magnets ({e})", False))
    # SINAL DE CONTINUAÇÃO LONG — gate determinístico
    dl = json.loads(json.dumps(base_d))
    dl["axes"]["mtf"]["60"] = {"trend": "UP"}; dl["axes"]["mtf"]["15"]["trend"] = "UP"
    dl["axes"]["confluence"] = {"15": {"buy_dens": 0.8, "sell": {"dens": 0.0}}}
    lc = {"direction": "LONG", "rule": "bos_continuation", "tf": "60", "rr": 2.3, "entry": 100, "sl": 99, "target": 103}
    r.append(("cont_signal LONG ok", cont_signal_ok(lc, dl) is True))
    r.append(("cont_signal SHORT rejeita", cont_signal_ok({**lc, "direction": "SHORT"}, dl) is False))
    r.append(("cont_signal RR<2 rejeita", cont_signal_ok({**lc, "rr": 1.8}, dl) is False))
    r.append(("cont_signal regra nao-cont rejeita", cont_signal_ok({**lc, "rule": "macro_event"}, dl) is False))
    dnoup = json.loads(json.dumps(dl)); dnoup["axes"]["mtf"]["60"] = {"trend": "DOWN"}; dnoup["axes"]["mtf"]["15"]["trend"] = "DOWN"
    r.append(("cont_signal sem 1H/15 UP rejeita", cont_signal_ok(lc, dnoup) is False))
    dnobuy = json.loads(json.dumps(dl)); dnobuy["axes"]["confluence"] = {"15": {"buy_dens": 0.0, "sell": {"dens": 0.5}}}
    r.append(("cont_signal sem iniciativa BUY rejeita", cont_signal_ok(lc, dnobuy) is False))
    allok = all(ok for _, ok in r)
    for name, ok in r: print(f"  {'OK' if ok else 'FALHA'} {name}")
    print("SELFTEST:", "PASS" if allok else "FALHA")
    return 0 if allok else 1


# ---------- daemon (GATE 0-tokens + READ Opus nos sobreviventes; SHADOW 0 Telegram) ----------
def paused(): return PAUSE_LOCAL.exists() or PAUSE_GLOBAL.exists()


def main_loop():
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            print(f"FATAL: já corre (pid {old})"); sys.exit(1)
        except (ProcessLookupError, ValueError): pass
    PIDFILE.write_text(str(os.getpid()))
    try: offset = json.loads(OFFSET_F.read_text()).get("offset", 0)
    except Exception: offset = 0
    print(f"[e2_quality] ativo | GATE higiene bad_rr+stale + FRAME perna-1H + READ "
          f"{READ_MODEL if READ_ENABLED else 'OFF'} | {'LIVE Telegram' if E2_LIVE else 'em validação (0 Telegram)'}", flush=True)
    retry_q = []   # [(cand, tentativas)] — leituras 'claude is_error' re-tentadas enquanto frescas (Cris 2026-07-17)
    try:
        while True:
            if paused(): time.sleep(FLOOR_S); continue
            try:
                # RETRY de leituras falhadas: gates re-avaliados com dossiê fresco (stale corta os velhos)
                if retry_q and READ_ENABLED:
                    dsr_r = load_dossier()
                    if dsr_r:
                        pend, retry_q = retry_q, []
                        for c, att in pend:
                            dc = drift_cycles(c, dsr_r)
                            v = make_verdict(c, dsr_r, dc)
                            if v["grade"] == "survivor":
                                image = render_composite(dsr_r, c)
                                th = run_read(c, dsr_r)
                                if th.get("error") and att < 2:
                                    retry_q.append((c, att + 1)); continue
                                v["read"] = th; v["surfaced"] = surfaced(th, c)
                                if v["surfaced"] and not th.get("error"): notify_surfaced(c, th)
                                archive_read(c, dsr_r, image, th, dc, f"live-retry{att}")
                                print(f"{now_iso()} [retry{att}|{'ERR' if th.get('error') else 'ok'}|surf {v['surfaced']}] "
                                      f"{v['direction']}/{v['rule']}/{v['tf']}", flush=True)
                            append(VERD_F, v)
                if CAND_F.exists():
                    sz = CAND_F.stat().st_size
                    if sz < offset: offset = 0
                    if sz > offset:
                        with open(CAND_F) as f:
                            f.seek(offset); new = f.read(); offset = f.tell()
                        dsr = load_dossier()
                        for line in new.splitlines():
                            try: c = json.loads(line)
                            except Exception: continue
                            if not is_material(c) or not dsr: continue
                            dc = drift_cycles(c, dsr)
                            v = make_verdict(c, dsr, dc)
                            if v["grade"] == "survivor" and READ_ENABLED:
                                image = render_composite(dsr, c)
                                th = run_read(c, dsr)
                                v["read"] = th; v["surfaced"] = surfaced(th, c)
                                if v["surfaced"] and not th.get("error"): notify_surfaced(c, th)
                                archive_read(c, dsr, image, th, dc, "live")
                                if th.get("error"):
                                    retry_q.append((c, 1))   # re-tenta no próximo ciclo enquanto fresco
                                tag = th.get("convergence", "err") if not th.get("error") else "ERR"
                                print(f"{now_iso()} [survivor|{tag}|convic {th.get('conviction','?')}|surf {v['surfaced']}] "
                                      f"{v['direction']}/{v['rule']}/{v['tf']}", flush=True)
                            elif v["grade"] != "discard":
                                print(f"{now_iso()} [survivor|read-off] {v['direction']}/{v['rule']}/{v['tf']}", flush=True)
                            if CONT_SIGNAL and v["grade"] == "survivor" and cont_signal_ok(c, dsr):
                                try:
                                    res = emit_cont_signal(c, dsr, v.get("read"))
                                    print(f"{now_iso()} [SINAL CONT LONG tg_ok={res.get('ok_all')}] {c['rule']}/{c['tf']} "
                                          f"entry {c.get('entry')} SL {c.get('sl')} tgt {c.get('target')} RR {c.get('rr')}", flush=True)
                                except Exception as _e:
                                    print(f"{now_iso()} [sinal cont ERRO] {type(_e).__name__}:{str(_e)[:80]}", flush=True)
                            append(VERD_F, v)
                        tmp = OFFSET_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps({"offset": offset})); os.replace(tmp, OFFSET_F)
            except Exception as e:
                print(f"{now_iso()} [erro] {type(e).__name__}:{str(e)[:80]}", flush=True)
            time.sleep(FLOOR_S)
    finally:
        PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--selftest" in sys.argv: sys.exit(cli_selftest())
    elif "--anchors" in sys.argv: sys.exit(cli_anchors())
    elif "--survey" in sys.argv: cli_survey("--replay" in sys.argv)
    elif "--once" in sys.argv: cli_once()
    elif "--read-smoke" in sys.argv:
        k = 0
        if "--n" in sys.argv:
            try: k = int(sys.argv[sys.argv.index("--n") + 1])
            except Exception: k = 0
        cli_read_smoke(k)
    else: main_loop()
