#!/usr/bin/env python3
"""READER DE VELA CONSTANTE (Cris 2026-08-04, opção B literal): o Opus lê CADA vela 5M/15M/1H no fecho e
avalia a fita continuamente. Os reads vão para LOG (candle_reads.jsonl) + chat — NUNCA para Telegram.
Telegram = SÓ sinal CONFIRMADO (gate confirmado + hard-lock CANDLE_TG_AUTHORIZED, default OFF até validar).

Motivo: dia -4R em que o sistema reagia tarde a gatilhos em vez de LER a fita. Agora lê constante.
CONSOME o E2 (render_composite p/ a imagem, CLI Opus, _extract_json) + bar-store — não reconstrói reader.
Física: 1 read de cada vez (o Opus demora 30-300s); se fecharem várias velas durante um read, lê a MAIS
FRESCA de cada TF e regista as saltadas (honesto). py3.9."""
import os, sys, json, time, subprocess, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import e2_quality as E2
import context_liquidity as CL
try:
    from context_confluence import read_confluence_store as _rcs
except Exception:
    _rcs = lambda tf="15": None

LX = ZoneInfo("Europe/Lisbon")
STORE = BASE.parent / "my-strategy/core/bar_store/store"
LOG = BASE / "logs" / "candle_reads.jsonl"
TFS = {"15": "bars_15m.jsonl", "60": "AGG15"}   # 5M REMOVIDO (ordem Cris 04/08: parar leitura 5min — saturava o Opus); 60 = agregado 4×15m
TG_OK = os.environ.get("CANDLE_TG_AUTHORIZED", "") == "1"   # Telegram só confirmado; default OFF
POLL_S = 20

# CONTINUIDADE DE TESE (Cris 2026-08-10): o reader era amnésico (cada vela = subprocess isolado) → declarava
# "espera reclaim>X" e na barra do reclaim re-adiava para outro gatilho (movia a baliza, sempre atrás do
# preço). Fix: persistir o PLANO que o reader declara e RE-ALIMENTÁ-LO no prompt da vela seguinte, para ele
# HONRAR o próprio gatilho (com discrição no gatilho: genuíno=confirma, fakeout=invalida). Estado por TF.
STATE = BASE / ".reader_state"; STATE.mkdir(exist_ok=True)


def _planf(tf):
    return STATE / f"plan_{tf}.json"


def load_plan(tf):
    try:
        return json.loads(_planf(tf).read_text())
    except Exception:
        return None


def save_plan(tf, plan):
    """Persiste o plano só se for acionável (direção + gatilho); senão limpa (sem plano em aberto)."""
    try:
        if isinstance(plan, dict) and plan.get("direction") in ("LONG", "SHORT") and plan.get("trigger"):
            _planf(tf).write_text(json.dumps(plan, ensure_ascii=False))
        else:
            _planf(tf).unlink(missing_ok=True)
    except Exception:
        pass

TAPE_SYS = (
    "És um trader XAUUSD discricionário experiente a LER A FITA no fecho de uma vela. NÃO estás a julgar um "
    "trade proposto — estás a ler o que a vela que ACABOU DE FECHAR, no seu contexto completo, está a dizer. "
    "Recebes a imagem composta (FRAME perna-1H, MAPA DO TRADER, LIQUIDEZ/MANIPULAÇÃO, estrutura MTF, auction, "
    "zonas, macro) e a vela fechada do TF em foco.\n"
    "Lê como um humano lê o gráfico: em que FASE está (exaustão / continuação / reversão-a-formar / range)? "
    "O preço está numa zona CRÍTICA do mapa do trader ou numa supply/demand HTF? Há assinatura de rejeição/"
    "absorção/sweep+reclaim, ou é vela morta? Aplica a regra de liquidez (iniciativa-para-íman = manipulação; "
    "deslocamento-pós-sweep = genuíno; sweep+reclaim sobrepõe o rótulo de perna atrasado).\n"
    "CONTEXTO DE CONTINUAÇÃO (default, NÃO um veto): ouro em tendência de alta = caso-base é comprar recuos que os suportes segurem. MAS és um SINALIZADOR NEUTRO, não um confirmador do viés — a FITA manda, e um sinal CONTRA-tese pode ser o melhor sinal. SHORT É CONFIRMÁVEL, SIMÉTRICO AO LONG (Cris 2026-08-13), quando há REJEIÇÃO IMPRESSA NO ÍMAN: sweep/varrimento de um topo/PDH OU retest de nível-rompido-por-baixo, + fecho no TERÇO INFERIOR da vela + buyers varridos/PRESOS + iniciativa SELL (idealmente CHoCH down). É a MESMA assinatura de teste-e-rejeição-NO-íman que exiges para o long, aplicada ao contrário — a doutrina de continuação NÃO pode vetar um short com essa assinatura impressa. PROIBIDO continua: short ANTECIPADO (sem rejeição impressa) e short de pullback raso sem assinatura. Cuidado com whipsaw em janelas de notícia (ex.: PPI/CPI). USA o bloco TOPOS SEQUENCIAIS (30M/1H) como CONFIRMAÇÃO MACRO EXTRA: lower-highs consecutivos = distribuição/topo (reforça short, enfraquece long); higher-highs = continuação (reforça long, enfraquece short) — nunca gatilho isolado.\n"
    "POLARIDADE — PRIORIDADE DE LEITURA (Cris 2026-08-10): uma SUPPLY rompida COM FORÇA (fecho decisivo "
    "acima, movimento impulsivo) vira DEMANDA OBRIGATÓRIA de ALTA PROBABILIDADE de segurar. LÊ-A EM PRIMEIRO "
    "LUGAR como suporte de continuação — mesmo que o indicador OB já não desenhe a caixa (a polaridade do "
    "nível permanece). Numa perna forte, o pullback deve NO MÁXIMO vir a essa polaridade (ex-topos rompidos) "
    "e segurar; um RECLAIM LEGÍTIMO aí é entrada de continuação de alta prioridade. Vigia essas ex-supplies "
    "com atenção redobrada.\n"
    "FUNDO DE PULLBACK MACRO — PADRÃO APRENDIDO MULTI-TF (análise 4H+1H+30M, 05→13/08; é confirmação EXTRA que "
    "COMPLEMENTA o dossiê E0/market_context, não o substitui). Camadas por TF:\n"
    "  • 4H (ÂNCORA macro): a tendência sobe em ESCADA de HIGHER-LOWS (4223→4313→4316→4356→4382). Os 3 "
    "pullbacks macro foram de ~1.2-1.9% (52-81pt) e a vela-de-fundo 4H foi 3/3: VERDE + fecho no TERÇO SUPERIOR "
    "do range + pavio inferior (absorção na demanda) + a vela 4H SEGUINTE RECLAMA acima. Define a DIREÇÃO e a "
    "zona-alvo do pullback.\n"
    "  • 1H (CONFIRMAÇÃO / timing): a mesma assinatura aparece em ~65% dos fundos 1H (verde/fecho-alto/reclaim). "
    "Usa-a para CRONOMETRAR o fundo DENTRO do pullback 4H — é o TF onde confirmas que a demanda 4H segurou.\n"
    "  • 30M (GATILHO fino): ~60%, mais RUÍDO (muitos pivôs são bounces em down-leg, não o fundo macro). SÓ vale "
    "em CONFLUÊNCIA com 1H+4H; sozinho é falível.\n"
    "  REGRA DE FIABILIDADE (precisão): o fundo de ALTA qualidade mostra a assinatura nos TRÊS TFs (30M E 1H E "
    "4H) AO MESMO TEMPO, todos em HIGHER-LOW. Quantos mais TFs concordam, maior a convicção.\n"
    "  ASSINATURA FORTE de fundo: pavio inferior GRANDE (≥50% do range) + fecho no terço superior (≥66%) + vela "
    "seguinte reclama acima.\n"
    "  FILTRO DE ESTRUTURA (decisivo): a assinatura só é ACUMULAÇÃO-para-COMPRAR se for HIGHER-LOW; num LOWER-LOW "
    "é apenas bounce-em-down-leg (fraco/faca) e exige confirmação extra. Enquanto o 4H mantém higher-lows a "
    "tendência é UP (comprar demandas); um LOWER-LOW no 4H quebra a escada = mudança de tendência.\n"
    "  SIMÉTRICO para topos (short): lower-highs + sweep/rejeição no íman + fecho no terço inferior = distribuição. "
    "Consome os blocos TOPOS/FUNDOS SEQUENCIAIS (30M/1H) já dados no prompt.\n"
    "REGRA DO 1º PULLBACK (Cris 2026-08-05, após short confirmado às 10h que falhou): o ouro NUNCA desce "
    "verdadeiramente na PRIMEIRA correção de uma perna impulsiva forte (perna fresca de vários ATR / dezenas "
    "de pontos). Pullback raso da 1ª correção NÃO é venda — NUNCA confirmes SHORT contra perna impulsiva de "
    "alta na sua 1ª correção (nem LONG no espelho de perna impulsiva de baixa). Short contra perna forte SÓ "
    "após DISTRIBUIÇÃO visível: múltiplos testes do topo, compra a secar toque a toque, sweep+rejeição+CHoCH. "
    "MAS um FAILED-BREAK do topo/PDH (varrimento ACIMA do high + devolução + fecho no terço inferior + buyers "
    "presos), OU o RECUO a um nível já ROMPIDO-por-baixo que rejeita e fecha no low, JÁ SÃO essa "
    "distribuição/exaustão impressa — NÃO os descartes como '1º pullback'; aí o short qualifica.\n"
    "SINAL CONFIRMADO (confirmed_signal=true) SÓ quando: convergência ALTA num sentido + numa zona/nível que "
    "importa + assinatura confirmada (rejeição/absorção/break com fecho, não antecipação) + entry/SL/alvo "
    "deriváveis com R:R>=2. Na dúvida, confirmed_signal=false (é leitura, não sinal). Não inventes números; "
    "usa só o dossiê.\n"
    "CONTINUIDADE DE TESE (Cris 2026-08-10 — REGRA CRÍTICA, o teu erro de hoje): NÃO és amnésico. Se te for "
    "dado um PLANO EM ABERTO (declaraste numa vela anterior 'espera gatilho X para entrar'), tens de o HONRAR. "
    "Se o gatilho do teu plano DISPAROU nesta vela (a condição cumpriu-se COM FECHO — ex.: declaraste 'espera "
    "reclaim>4321' e a vela fechou 4330), decide AGORA: (a) se a impressão é genuína, confirmed_signal=true com "
    "entry/SL/alvo — EXECUTA o plano; (b) se é fakeout ou a estrutura mudou, invalida e diz porquê. O QUE É "
    "PROIBIDO é ver o gatilho cumprido e simplesmente pedir OUTRO gatilho ('agora espera um pullback') — isso é "
    "MOVER A BALIZA e deixa-te sempre atrás do preço. Quando NÃO tens sinal mas vês um setup a formar-se, "
    "declara o PLANO (direction+trigger+invalidation concretos) para o honrares na próxima vela. Devolve SÓ um objeto JSON."
)
TAPE_SCHEMA = (
    "\n\nDevolve SÓ este JSON:\n"
    '{"reasoning":"<lê a vela na fita: fase, localização, assinatura, o que diz>",'
    '"phase":"EXAUSTAO|CONTINUACAO|REVERSAO_A_FORMAR|RANGE","bias":"LONG|SHORT|NONE",'
    '"at_level":"<zona/nível crítico onde está, ou vazio>","convergence":"high|moderate|low|incoherent",'
    '"confirmed_signal":false,"direction":"LONG|SHORT|NONE","entry":<num|null>,"sl":<num|null>,'
    '"target":<num|null>,"rr":<num|null>,"conviction":<INTEIRO 0-100>,"note":"<uma frase para o Cris>",'
    '"plan":{"direction":"LONG|SHORT|NONE","trigger":"<condição concreta do gatilho, ex \'fecho 15M>4321\', ou vazio se sem plano>",'
    '"invalidation":"<condição que mata o plano, ex \'fecho<4310\'>","note":"<o que esperas p/ entrar>"}}'
)


def hm(t): return dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")


def _read_jl(fname, budget=8000):
    try:
        with open(STORE / fname, "rb") as fh:
            fh.seek(0, 2); sz = fh.tell(); fh.seek(max(0, sz - budget))
            rows = [json.loads(l) for l in fh.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        return [b for b in rows if all(k in b for k in ("t", "o", "h", "l", "c"))]
    except Exception:
        return []


def _agg_1h(m15):
    """Agrega 15m em velas 1H (bucket t//3600). Só velas COMPLETAS (4 barras 15m) contam como fechadas."""
    buckets = {}
    for b in m15:
        hb = (b["t"] // 3600) * 3600
        buckets.setdefault(hb, []).append(b)
    out = []
    for hb in sorted(buckets):
        g = sorted(buckets[hb], key=lambda x: x["t"])
        out.append({"t": hb, "o": g[0]["o"], "h": max(x["h"] for x in g), "l": min(x["l"] for x in g),
                    "c": g[-1]["c"], "_n15": len(g)})
    return out


def load_bars(tf, n=40):
    if TFS[tf] == "AGG15":
        return _agg_1h(_read_jl("bars_15m.jsonl", budget=20000))[-n:]
    return _read_jl(TFS[tf])[-n:]


def obs_candidate(tf, bar, dsr):
    """Candidato-observação p/ render_composite dar a imagem completa. Direção = viés da liquidez fresca."""
    liq = None
    try:
        conf = _rcs("15") or {}
        liq = CL.read_liquidity(magnets=(dsr.get("axes") or {}).get("magnets"),
                                mtf=(dsr.get("axes") or {}).get("mtf"),
                                amd=(dsr.get("axes") or {}).get("amd_setup"), window=conf.get("window"))
    except Exception:
        pass
    bias = "SHORT" if (liq and liq.get("direction") == "down") else "LONG" if (liq and liq.get("direction") == "up") else "NONE"
    return {"id": f"tape_{tf}_{bar['t']}", "direction": bias, "rule": "tape_obs", "tf": tf,
            "entry": bar["c"], "sl": None, "target": None, "rr": None,
            "src": f"OBSERVAÇÃO fecho vela {tf} — O{bar['o']} H{bar['h']} L{bar['l']} C{bar['c']}",
            "materiality": {"sl_atr": None, "confluence": None, "confluence_breakdown": {}}}


# --- TOPOS SEQUENCIAIS (feature macro, Cris 2026-08-13): confirmação EXTRA de topo/continuação ---
def _agg15(bars, step):
    """Agrega bars 15M em velas de `step` segundos (30M=1800, 1H=3600). Só h/l precisam para pivôs."""
    g = {}
    for b in bars:
        k = (b["t"] // step) * step
        if k not in g:
            g[k] = {"t": k, "h": b["h"], "l": b["l"]}
        else:
            g[k]["h"] = max(g[k]["h"], b["h"]); g[k]["l"] = min(g[k]["l"], b["l"])
    return [g[k] for k in sorted(g)]


def _pivot_highs(bars, k=2):
    """Pivô de alta = high[i] é o máximo local numa janela de ±k. Puro/testável."""
    out = []
    for i in range(k, len(bars) - k):
        h = bars[i]["h"]
        if all(h >= bars[i + j]["h"] for j in range(-k, k + 1) if j != 0):
            out.append(bars[i])
    return out


def seq_tops_block(bars15, n=4):
    """Bloco de TOPOS SEQUENCIAIS 30M/1H para o prompt. Lower-highs = distribuição/topo (reforça SHORT);
    higher-highs = continuação (reforça LONG). Confirmação EXTRA, nunca gatilho isolado. '' se dados curtos."""
    if not bars15 or len(bars15) < 12:
        return ""
    out = []
    for name, step in (("1H", 3600), ("30M", 1800)):
        tp = _pivot_highs(_agg15(bars15, step), 2)[-n:]
        if len(tp) < 2:
            continue
        hs = [t["h"] for t in tp]
        seq = " → ".join("%.2f" % h for h in hs)
        last = ("LOWER-HIGH (distribuição/topo a formar-se)" if hs[-1] < hs[-2]
                else "HIGHER-HIGH (continuação)" if hs[-1] > hs[-2] else "igual")
        lh = sum(1 for i in range(1, len(hs)) if hs[i] < hs[i - 1])
        hh = sum(1 for i in range(1, len(hs)) if hs[i] > hs[i - 1])
        out.append("  %s: %s | último = %s | %dLH/%dHH" % (name, seq, last, lh, hh))
    if not out:
        return ""
    return ("\n\n# ⛰️ TOPOS SEQUENCIAIS (confirmação macro EXTRA, NÃO gatilho isolado): topos DESCENDENTES "
            "(lower-highs consecutivos) = distribuição / topo a formar-se → REFORÇA short e enfraquece long; "
            "ASCENDENTES (higher-highs) = continuação de alta → reforça long e enfraquece short.\n" + "\n".join(out))


def _pivot_lows(bars, k=2):
    """Pivô de baixa = low[i] é o mínimo local numa janela de ±k. Puro/testável."""
    out = []
    for i in range(k, len(bars) - k):
        lo = bars[i]["l"]
        if all(lo <= bars[i + j]["l"] for j in range(-k, k + 1) if j != 0):
            out.append(bars[i])
    return out


def seq_bottoms_block(bars15, n=4):
    """FUNDOS SEQUENCIAIS 30M/1H (simétrico aos topos). Higher-lows = acumulação/continuação-up (reforça
    LONG); lower-lows = breakdown/tendência-baixa (reforça SHORT). Confirmação EXTRA, nunca gatilho isolado."""
    if not bars15 or len(bars15) < 12:
        return ""
    out = []
    for name, step in (("1H", 3600), ("30M", 1800)):
        bt = _pivot_lows(_agg15(bars15, step), 2)[-n:]
        if len(bt) < 2:
            continue
        ls = [b["l"] for b in bt]
        seq = " → ".join("%.2f" % x for x in ls)
        last = ("HIGHER-LOW (acumulação/continuação-up)" if ls[-1] > ls[-2]
                else "LOWER-LOW (breakdown)" if ls[-1] < ls[-2] else "igual")
        hl = sum(1 for i in range(1, len(ls)) if ls[i] > ls[i - 1])
        ll = sum(1 for i in range(1, len(ls)) if ls[i] < ls[i - 1])
        out.append("  %s: %s | último = %s | %dHL/%dLL" % (name, seq, last, hl, ll))
    if not out:
        return ""
    return ("\n\n# 🏔️ FUNDOS SEQUENCIAIS (confirmação macro EXTRA, NÃO gatilho isolado): fundos ASCENDENTES "
            "(higher-lows consecutivos) = acumulação / continuação-up → REFORÇA long e enfraquece short; "
            "DESCENDENTES (lower-lows) = breakdown / tendência-baixa → reforça short e enfraquece long.\n" + "\n".join(out))


def read_candle(tf, bar, dsr):
    """UM read Opus da fita no fecho da vela. Reutiliza a imagem do E2 + CLI Opus. Retry via _read_once-like."""
    cand = obs_candidate(tf, bar, dsr)
    image = E2.render_composite(dsr, cand)
    # LEITURA CANÓNICA de TODOS os indicadores no fecho (Cris 04/08: "leitura permanente de todos os
    # indicadores a cada vela"): snapshot real do market_read (OB/SMC/SVP/NAS/Bubbles/RSI/Vol) no prompt.
    indic = ""
    try:
        import market_read as MR
        lines = [MR.read_line(t) for t in ("15", "60") if MR.snapshot(t)]
        if lines:
            indic = "\n\n# INDICADORES REAIS NO FECHO (leitura canónica do chart)\n" + "\n".join(f"  {l}" for l in lines)
    except Exception:
        pass
    focus = (f"\n\n# VELA EM FOCO ({tf}M, fecho {hm(bar['t'])} Lisboa): O{bar['o']} H{bar['h']} "
             f"L{bar['l']} C{bar['c']} — lê ESTA vela na fita acima.")
    # CONTINUIDADE: re-alimenta o PLANO EM ABERTO que o reader declarou numa vela anterior (honra o gatilho).
    plan = load_plan(tf); planblock = ""
    if plan and plan.get("direction") in ("LONG", "SHORT"):
        planblock = (f"\n\n# ⚠️ O TEU PLANO EM ABERTO (declarado numa vela ANTERIOR — HONRA-O, não movas a baliza):\n"
                     f"  direção {plan['direction']} · GATILHO: {plan.get('trigger')} · invalidação: {plan.get('invalidation')}\n"
                     f"  o que esperavas: {plan.get('note')}\n"
                     f"  → Se o GATILHO disparou NESTA vela (condição cumprida com fecho): CONFIRMA (se genuíno) ou "
                     f"INVALIDA (se fakeout/estrutura mudou). NÃO peças gatilho novo.")
    # POLARIDADES ATIVAS (manutenção da leitura — ex-supplies furadas = suportes prováveis; lei validada +12pp
    # vs null; sobrevivem à caixa OB sumir via polarity_tracker).
    polblock = ""
    try:
        import polarity_tracker
        pol = polarity_tracker.load_active_supports(bar["c"])
        if pol:
            zs = " · ".join(f"{z['low']:.0f}-{z['high']:.0f}" for z in pol[:5])
            polblock = (f"\n\n# 🔁 POLARIDADES ATIVAS (ex-SUPPLIES furadas COM FORÇA = SUPORTES obrigatórios de "
                        f"alta-prob no pullback — lei de price action, prioridade de leitura): {zs}\n"
                        f"  Se o preço recuar a uma destas e imprimir RECLAIM LEGÍTIMO, é entrada de continuação "
                        f"de ALTA prioridade. Lê-as em 1º lugar como suporte, mesmo sem a caixa OB desenhada.")
    except Exception:
        pass
    topsblock = botsblock = ""
    try:
        b15 = load_bars("15", 80)
        topsblock = seq_tops_block(b15)      # topos sequenciais 30M/1H = confirmação macro extra
        botsblock = seq_bottoms_block(b15)   # fundos sequenciais 30M/1H = confirmação macro extra (simétrico)
    except Exception:
        pass
    prompt = image + indic + focus + planblock + polblock + topsblock + botsblock + TAPE_SCHEMA
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None)
    for attempt in range(2):
        try:
            r = subprocess.run([E2.CLAUDE_EXE, "-p", prompt, "--append-system-prompt", TAPE_SYS,
                                "--output-format", "json", "--model", E2.READ_MODEL],
                               capture_output=True, text=True, timeout=E2.READ_TIMEOUT, env=env)
            out = json.loads(r.stdout or "{}")
            if out.get("is_error"):
                last = {"error": "claude is_error"}; time.sleep(2); continue
            v = E2._extract_json(out.get("result", ""))
            if v and "phase" in v:
                cv = E2.fnum(v.get("conviction"))
                if cv is not None:
                    v["conviction"] = int(round(cv * 100)) if 0 <= cv <= 1 else int(round(cv))
                # CONTINUIDADE: sinal confirmado = plano executado (limpa); senão persiste o plano declarado.
                save_plan(tf, None if v.get("confirmed_signal") else v.get("plan"))
                return v
            last = {"error": "sem tese", "raw": (out.get("result") or "")[:200]}
        except Exception as e:
            last = {"error": f"{type(e).__name__}:{str(e)[:80]}"}
        time.sleep(2)
    return last


def is_confirmed(v):
    """Sinal confirmado = o read declara-o E é operável (direção + entry/sl/alvo + R:R>=2 + convicção alta)."""
    if not isinstance(v, dict) or v.get("error"): return False
    if not v.get("confirmed_signal"): return False
    if v.get("direction") not in ("LONG", "SHORT"): return False
    e, s, t = E2.fnum(v.get("entry")), E2.fnum(v.get("sl")), E2.fnum(v.get("target"))
    rr = E2.fnum(v.get("rr"))
    if None in (e, s, t): return False
    if rr is None:
        risk = abs(e - s); rr = abs(t - e) / risk if risk else 0
    return rr >= 2.0 and (E2.fnum(v.get("conviction")) or 0) >= 60


def log_read(tf, bar, v):
    rec = {"ts": E2.now_iso(), "tf": tf, "bar_t": bar["t"], "bar": bar, "read": v,
           "confirmed": is_confirmed(v)}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def fmt_chat(tf, bar, v):
    if v.get("error"):
        return f"[vela {tf}M {hm(bar['t'])}] read falhou: {v['error']}"
    return (f"[vela {tf}M {hm(bar['t'])} C{bar['c']}] {v.get('phase')} · {v.get('bias')} · "
            f"conv {v.get('convergence')}/{v.get('conviction')} · {v.get('at_level') or 'sem nível'} · "
            f"{str(v.get('note'))[:140]}")


# --- FILTRO ANTI-CHASE do reader-grupo (Cris 2026-08-12) ---
# Buraco: o reader confirmou LONG 4416/4421 NO TOPO do breakout e mandou ao GRUPO; ambos falharam (TP nunca
# tocado, voltaram ao SL). Fix: um LONG a comprar perto do TOPO da janela 15M rolante = chase -> vai só ao
# privado, nao ao grupo. Metrica = posicao do entry no range recente (chase compra ~topo; pullback ~fundo).
# 1a-cut calibrada para apanhar o caso de hoje; a validar em forward (nao e edge provado). Config, nao preco.
CHASE_WIN = 16          # barras 15M (~4h) da janela rolante que TERMINA no sinal
CHASE_POS = 0.80        # entry >= 80% do range da janela = topo = chase


def _range_pos(entry, win):
    """Posicao 0..1 do entry no range [min low, max high] de `win` bars. None se indefinido. Puro/testavel."""
    if entry is None or not win:
        return None
    his = [b["h"] for b in win if b.get("h") is not None]
    los = [b["l"] for b in win if b.get("l") is not None]
    if len(his) < 8 or len(los) < 8:
        return None
    hi, lo = max(his), min(los)
    if hi - lo < 1e-6:
        return None
    return (entry - lo) / (hi - lo)


def is_chase_long(v):
    """LONG a comprar perto do TOPO da janela 15M rolante = chase -> so privado, fora do grupo.
    SHORT e LONG-de-pullback passam ao grupo. Usa bars 15M REAIS do store (nao inventa)."""
    if (v.get("direction") or "") != "LONG":
        return False
    e = E2.fnum(v.get("entry"))
    try:
        bars = load_bars("15", CHASE_WIN + 6)
    except Exception:
        return False
    pos = _range_pos(e, (bars or [])[-CHASE_WIN:])
    return pos is not None and pos >= CHASE_POS


def send_confirmed_tg(tf, bar, v):
    if not TG_OK: return "tg-off"
    txt = (f"🤖 LIVE SYSTEM · READER — SINAL CONFIRMADO\n"
           f"✅ SINAL CONFIRMADO ({tf}M {hm(bar['t'])}) — {v['direction']} XAUUSD\n"
           f"entry {v['entry']} · SL {v['sl']} · alvo {v['target']} (RR {v.get('rr')})\n"
           f"{v.get('phase')} · {v.get('at_level') or ''} · convicção {v.get('conviction')}\n"
           f"{str(v.get('note'))[:180]}\n(advisory — a decisão é tua)")
    try:
        # Reader no GRUPO (Cris 12/08) — MAS com FILTRO ANTI-CHASE: LONG no topo do range 15M -> so privado.
        aud = "group"
        if is_chase_long(v):
            aud = "assistant"
            txt += "\n⚠️ CHASE (topo do range 15M) — enviado só ao teu privado, fora do grupo."
        return f"tg-{aud}" if E2._tg_send(txt, audience=aud) else "tg-fail"
    except Exception:
        return "tg-erro"


def main_loop():
    print(f"📖 candle-reader ARMADO — Opus lê cada vela 5M/15M/1H no fecho → log (Telegram confirmado={'ON' if TG_OK else 'OFF'})", flush=True)
    seen = {tf: None for tf in TFS}
    # ARRANQUE: lê IMEDIATAMENTE o último 15M FECHADO (há sempre um read disponível pós-start; Cris 2026-08-04
    # "não estás lendo constantemente?" — sem isto ficava-se sem read entre o arranque e o próximo fecho).
    try:
        b15 = load_bars("15", 3)
        dsr0 = E2.load_dossier()
        if len(b15) >= 1 and dsr0:                     # store escreve SO fechadas: [-1] = ultima FECHADA
            v0 = read_candle("15", b15[-1], dsr0)
            rec0 = log_read("15", b15[-1], v0)
            print("[arranque] " + fmt_chat("15", b15[-1], v0), flush=True)
            if rec0["confirmed"]:
                print(f"   ✅ CONFIRMADO → {send_confirmed_tg('15', b15[-1], v0)}", flush=True)
    except Exception as e:
        print(f"[arranque] read falhou: {type(e).__name__}", flush=True)
    for tf in TFS:                                    # baseline: novos closes após o arranque
        b = load_bars(tf, 2)
        if b: seen[tf] = b[-1]["t"]                   # [-1] = última fechada (store só escreve fechadas)
    while True:
        try:
            try:
                import polarity_tracker; polarity_tracker.update()   # single-writer: mantém polaridades vivas
            except Exception:
                pass
            dsr = E2.load_dossier()
            if not dsr:
                time.sleep(POLL_S); continue          # dossiê ausente (E0 down): não crashar render
            todo = []
            for tf in TFS:
                bars = load_bars(tf, 3)
                if not bars: continue
                closed = bars[-1]                      # [-1] = última FECHADA (store nunca escreve em-formação)
                if tf == "60" and closed.get("_n15") != 4:      # 1H: só hora COMPLETA
                    closed = bars[-2] if len(bars) >= 2 and bars[-2].get("_n15") == 4 else None
                if not closed: continue
                if seen[tf] is None: seen[tf] = closed["t"]; continue
                if closed["t"] > seen[tf]:
                    todo.append((tf, closed))
            if todo:
                prio = {"60": 0, "15": 1}              # 60>15: sem 5M (ordem Cris)
                todo.sort(key=lambda x: (prio[x[0]], -x[1]["t"]))
                tf, bar = todo[0]
                skipped = [(t, b["t"]) for t, b in todo[1:]]
                v = read_candle(tf, bar, dsr)
                rec = log_read(tf, bar, v)
                print(fmt_chat(tf, bar, v), flush=True)
                seen[tf] = bar["t"]                    # marca SÓ o TF lido, com o t lido (nunca re-load)
                if skipped:
                    print(f"   (pendentes p/ próximo ciclo: {[(t, hm(ts)) for t, ts in skipped]})", flush=True)
                if rec["confirmed"]:
                    ch = send_confirmed_tg(tf, bar, v)
                    print(f"   ✅ CONFIRMADO → {ch}: {v.get('direction')} {v.get('entry')}/{v.get('sl')}/{v.get('target')}", flush=True)
        except Exception as e:
            print(f"candle-reader erro: {type(e).__name__}:{str(e)[:80]}", flush=True)
        time.sleep(POLL_S)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        # is_confirmed
        ok1 = is_confirmed({"confirmed_signal": True, "direction": "SHORT", "entry": 4100, "sl": 4110,
                            "target": 4070, "rr": 3, "conviction": 70})
        ok2 = not is_confirmed({"confirmed_signal": True, "direction": "SHORT", "entry": 4100, "sl": 4110,
                                "target": 4095, "rr": 0.5, "conviction": 70})   # RR baixo
        ok3 = not is_confirmed({"confirmed_signal": False, "direction": "SHORT", "entry": 4100, "sl": 4110,
                                "target": 4070, "conviction": 90})               # não confirmado
        ok4 = not is_confirmed({"confirmed_signal": True, "direction": "NONE"})  # sem direção
        ok5 = not is_confirmed({"error": "x"})
        rr_auto = is_confirmed({"confirmed_signal": True, "direction": "LONG", "entry": 4000, "sl": 3990,
                                "target": 4030, "conviction": 65})               # rr calc = 3
        for lab, ok in (("confirmado válido", ok1), ("RR baixo rejeitado", ok2), ("não-confirmado rejeitado", ok3),
                        ("sem direção rejeitado", ok4), ("erro rejeitado", ok5), ("rr auto-calc", rr_auto)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5, rr_auto])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    if "--once" in sys.argv:
        tf = sys.argv[sys.argv.index("--once") + 1] if len(sys.argv) > sys.argv.index("--once") + 1 else "15"
        dsr = E2.load_dossier() or {}
        bars = load_bars(tf, 3)
        bar = bars[-1]
        print(f"read único vela {tf}M {hm(bar['t'])}...", flush=True)
        v = read_candle(tf, bar, dsr)
        print(json.dumps(v, ensure_ascii=False, indent=1))
        print("\nchat:", fmt_chat(tf, bar, v), "\nconfirmado:", is_confirmed(v))
        sys.exit(0)
    main_loop()
