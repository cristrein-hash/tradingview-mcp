#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
import textwrap
import fcntl
import time
from datetime import datetime

CHART_LOCK_PATH = "/tmp/tradingview_chart.lock"
CHART_LOCK_TIMEOUT_S = 90


def acquire_chart_lock(timeout_s=CHART_LOCK_TIMEOUT_S):
    """Acquire exclusive flock on TradingView chart resource.
    Returns (fd, wait_seconds). Raises TimeoutError if timeout exceeded.
    Serializes chart_set_symbol/timeframe across concurrent claude headless runs."""
    fd = open(CHART_LOCK_PATH, "w")
    deadline = time.monotonic() + timeout_s
    start = time.monotonic()
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, round(time.monotonic() - start, 2)
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fd.close()
                raise TimeoutError(f"chart lock timeout after {timeout_s}s")
            time.sleep(0.5)


def release_chart_lock(fd):
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()
    except Exception:
        pass

BASE_DIR = Path.home() / "tradingview-mcp"
CLAUDE_CLI = str(Path.home() / ".local" / "bin" / "claude")  # path absoluto: LaunchAgent não herda PATH do shell
STRATEGY_DIR = BASE_DIR / "my-strategy"
RULES = STRATEGY_DIR / "strategy_rules.json"
OP_PROMPT = STRATEGY_DIR / "operational_prompt.md"
QUASE_VALIDO_DOC = STRATEGY_DIR / "research/experimental/intraday_quase_valido_experimental.md"
DYNAMIC_BB_DOC = STRATEGY_DIR / "research/experimental/parked/dynamic_intraday_bb_zones_D6.md"  # PARKED 2026-05-19 (Fase 0.4 sub-A)
CANDIDATO_FORTE_DOC = STRATEGY_DIR / "research/experimental/setup_candidato_forte_policy.md"
PROMOTION_POLICY_DOC = STRATEGY_DIR / "research/experimental/setup_promotion_policy_experimental.md"
MODULE_AWARE_RULES_DOC = STRATEGY_DIR / "research/experimental/module_aware_global_rules_v3.md"
XAUUSD_4H_SWING_DOC = STRATEGY_DIR / "research/experimental/xauusd_4h_long_rejection_swing.md"  # DEACTIVATED — kept for history
XAUUSD_4H_BREAKOUT_REGIME_DOC = STRATEGY_DIR / "research/experimental/xauusd_4h_long_breakout_continuation_regime_filtered.md"  # ACTIVE (substitui 4H_LONG_REJECTION_SWING)
XAUUSD_1H_DECISIVE_DOC = STRATEGY_DIR / "research/experimental/xauusd_1h_long_decisive_body60_htf.md"  # DEACTIVATED 2026-06-01 — visual auction-theory review (kept for history)
XAGUSD_1H_DECISIVE_DXY_DOC = STRATEGY_DIR / "research/experimental/xagusd_1h_long_decisive_dxy_structural.md"  # ACTIVE — SETUP_CANDIDATO_FORTE intraday + DXY structural
XAUUSD_1H_EXECUTION_DOC = STRATEGY_DIR / "research/experimental/xauusd_1h_long_rejection_execution.md"  # DEACTIVATED — kept for history
XAUUSD_INTRADAY_BB_DOC = STRATEGY_DIR / "research/experimental/xauusd_intraday_bb_confluence_execution.md"
US500_4H_PULLBACK_DOC = STRATEGY_DIR / "research/experimental/us500_4h_long_pullback_rejection.md"  # DEACTIVATED — kept for history
US500_4H_FAILED_BREAKDOWN_DOC = STRATEGY_DIR / "research/experimental/us500_4h_long_failed_breakdown_regime.md"  # ACTIVE (novo SETUP_VALIDO)
US500_1H_BREAKOUT_REGIME_DOC = STRATEGY_DIR / "research/experimental/us500_1h_long_breakout_regime_filtered.md"  # ACTIVE (SETUP_CANDIDATO_FORTE)
US500_INTRADAY_PULLBACK_DOC = STRATEGY_DIR / "research/experimental/us500_intraday_long_pullback_execution.md"  # DEACTIVATED — kept for history
ETHUSD_4H_BREAKOUT_DOC = STRATEGY_DIR / "research/experimental/ethusd_4h_long_breakout_continuation.md"  # DEPRECATED — kept for history
ETHUSD_30M_MOMENTUM_DOC = STRATEGY_DIR / "research/experimental/ethusd_30m_confirmed_momentum_execution.md"  # DEACTIVATED — kept for history
ETHUSD_4H_BREAKOUT_REGIME_DOC = STRATEGY_DIR / "research/experimental/ethusd_4h_long_breakout_regime_filtered.md"  # ACTIVE (substitui ETHUSD_4H_LONG_BREAKOUT_CONTINUATION)
ETHUSD_1H_PULLBACK_REGIME_DOC = STRATEGY_DIR / "research/experimental/ethusd_1h_long_pullback_ema50_regime.md"  # ACTIVE (novo módulo intraday)
EURUSD_4H_COMBO_DXY_DOC = STRATEGY_DIR / "research/experimental/eurusd_4h_long_breakout_combo_strict_dxy.md"  # ACTIVE — SETUP_VALIDO (substitui EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION)
EURUSD_1H_DECISIVE_DOC = STRATEGY_DIR / "research/experimental/eurusd_1h_long_decisive_htf1d_dxy.md"  # ACTIVE — SETUP_CANDIDATO_FORTE intraday
EURUSD_30M_BREAKOUT_DOC = STRATEGY_DIR / "research/experimental/eurusd_30m_long_quality_breakout_continuation.md"  # DEACTIVATED — kept for history
LOG_DIR = BASE_DIR / "alert-bridge" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === Guard B (Fase 0.3 — 2026-05-19) ===
# Short-circuit pra alert_types deprecated pós-migração 2026-05-17 (drawings → indicators).
# Evita spawn caro de claude headless + crashes latentes em build_prompt (ex: NameError
# em f-string com {SYMBOL}_{DIR} literal — fixado 2026-05-19).
# MIRROR: lista replicada em tv_webhook_receiver.py (Guard A). Manter sincronizadas.
DEPRECATED_ALERT_TYPES = frozenset({
    "monitor_zone",
    "monitor_dynamic_bb_zone",
    "monitor_trendline_lta",
    "monitor_trendline_ltb",
    "monitor_invalidation",
    "monitor_dynamic_line",
    "monitor_breakout",
    "setup_watch_recheck",
    "manual_d6b_create_alert",
    "manual_d6b_create_price_alert",
})

DEFAULT_ALERT = {
    "symbol": "PEPPERSTONE:XAUUSD",
    "timeframe": "1H",
    "alert_type": "test_connectivity",
    "event": "manual_recheck_test",
    "message": "Teste manual de reavaliação com Claude Code headless",
    "price": 4675.71
}


def is_test_alert(alert: dict) -> bool:
    alert_type = str(alert.get("alert_type", "")).lower()
    event = str(alert.get("event", "")).lower()
    message = str(alert.get("message", "")).lower()

    if alert_type == "test_connectivity":
        return True
    if event.startswith("test") or "test" in event:
        return True
    if "teste" in message or "test" in message:
        return True
    if "cloudflare_tunnel_test" in event:
        return True

    return False


def build_test_response(alert: dict) -> str:
    symbol = alert.get("symbol", "desconhecido")
    timeframe = alert.get("timeframe", "desconhecido")
    event = alert.get("event", "test_connectivity")

    return textwrap.dedent(f"""
    TESTE RECEBIDO
    Canal: TradingView → webhook → Claude → Telegram funcionando.
    Ativo: {symbol}
    Timeframe: {timeframe}
    Evento: {event}
    Análise operacional: não executada, pois este alerta é apenas teste/conectividade.
    Ação tomada: nenhuma.
    Próxima ação: usar alert_type operacional para reavaliações reais.
    """).strip()


def is_deprecated_alert(alert: dict) -> bool:
    """Detecta alert_type da era drawings (pré-migração 2026-05-17)."""
    at = str(alert.get("alert_type", "")).strip()
    return at in DEPRECATED_ALERT_TYPES


def build_deprecated_short_circuit_response(alert: dict) -> str:
    """Resposta inerte pra deprecated. Texto não casa critérios de should_send_*_to_telegram."""
    at = alert.get("alert_type", "")
    sym = alert.get("symbol", "")
    return textwrap.dedent(f"""
    DEPRECATED_SHORT_CIRCUIT
    alert_type: {at}
    symbol: {sym}
    Motivo: alert_type da era drawings (pré-migração 2026-05-17). Não há análise operacional.
    Ação tomada: nenhuma. Sinal já contabilizado pelo Guard A no receiver.
    Ação esperada: remover origem (alerta TV ainda configurado ou script legado).
    """).strip()


# ============================================================================
# ZONE_TOUCH_SMC_INTERIM_PRESERVED — Fase 0.4 sub-B (2026-05-19)
# ----------------------------------------------------------------------------
# Texto original do módulo ATIVO INTERIM ZONE_TOUCH_SMC_CONVERGENT_LONG_INTERIM
# (criado 2026-05-15, desativado 2026-05-19). Preservado fora da f-string do
# prompt operacional para reaproveitamento futuro pelo Caminho C (zone-touch
# baseado em indicators, não drawings). NÃO é executado nem lido pelo Claude.
# ----------------------------------------------------------------------------
#
# Módulo ATIVO INTERIM — ZONE_TOUCH_SMC_CONVERGENT_LONG_INTERIM (criado 2026-05-15):
# - Razão de existir: auditoria 2026-05-15 revelou ZERO SETUP_VALIDO emitidos
#   historicamente. Causa: alertas TV são zone-touch (50/50), módulos formais
#   exigem trigger mecânico (breakout/failed_breakdown/pullback). Interseção
#   vazia. Este módulo cria CAMINHO B (zone-touch convergente) pra SETUP_VALIDO.
# - Sample: n=0 backtest formal. Marcado INTERIM com revalidação.
# - Direção: APENAS LONG nesta versão. SHORT requer adaptar Order Block bearish
#   e ainda não foi testado.
# - Aplicável quando alert_type in {monitor_dynamic_bb_zone, monitor_zone,
#   monitor_trendline_lta, monitor_dynamic_line, setup_watch_recheck} E
#   direção identificada = LONG E preço dentro/na borda da zona.
#
# Trigger (todos obrigatórios):
#   T1. alert_type compatível (lista acima).
#   T2. Direção LONG identificada com clareza.
#   T3. Preço dentro ou na borda imediata da zona.
#
# Filtros obrigatórios (TODOS):
#   F1. HTF bias alinhado: HTF 1D bullish E HTF 12H bullish (ambos: close > EMA50).
#   F2. R:R estimado >= 2:1 com stop estrutural definido (não apenas ATR).
#   F3. Hard blocks globais PASS (R:R, MCP, entry late, falling knife, etc.).
#   F4. Entry NÃO atrasado: entry_late_distance_r < 0.5.
#   F5. Zona AUTO_CLAUDE_ ou AUTO_CLAUDE_DYNAMIC_ válida no chart.
#
# Confluências fortes (mínimo 4 obrigatório — promoção a SETUP_VALIDO):
#   C1. RSI extremo (sobrevenda <=30) OU recém saindo de sobrevenda com reação.
#   C2. Divergência regular bullish (RSI vs preço).
#   C3. CHoCH ou BOS bullish estrutural confirmado.
#   C4. Sweep + reentry da liquidez (preço varreu low recente e recuperou).
#   C5. Sinal NAS100 LONG ou NAS BOTTOM dentro/borda da zona.
#   C6. Rejection close (candle com pavio inferior >=50% e close bullish).
#   C7. Cluster Market Order Bubbles (NÃO obrigatório em TF 1H+ por regra de 2026-05-15).
#   C8. Zona nested em HTF (BB 1H dentro de P3 4H, etc.).
#   C9. V3d Order Block Leonardo (XAU/EUR 4H apenas, quando ativo).
#
# Stop técnico: abaixo da invalidação estrutural da zona (último fundo válido).
# Target mínimo: 2R. Default R:R alvo 2.5R.
#
# Classificação:
#   - 4+ confluências fortes + filtros F1-F5 PASS  -> SETUP_VALIDO (Direção: LONG)
#   - 3 confluências + filtros PASS                -> SETUP_CANDIDATO_FORTE
#   - <3 confluências                              -> SETUP_EM_OBSERVACAO
#   - HTF não alinhado OU R:R<2                    -> SETUP_EM_OBSERVACAO ou NO_TRADE
#
# Output esperado quando promove a SETUP_VALIDO:
#   Strategy Module: ZONE_TOUCH_SMC_CONVERGENT_LONG_INTERIM
#   Module backtest n: 0 (INTERIM)
#   Classificação: SETUP_VALIDO
#   Direção: LONG
#   Promotion trigger: DENSE_STRUCTURAL_CONFLUENCE
#   Module checklist notes: listar as 4+ confluências em ordem
#
# CRITÉRIO INTERIM (revalidação):
#   - n >= 30 trades shadow live com este módulo aplicado
#   - PF >= 1.4 e win >= 45%
#   - no_top5 >= 0 (robustez sem fat-tail)
#   Se atingir critérios: módulo é promovido a estável (sem flag INTERIM).
#   Se NÃO atingir em n=30: reverter módulo (volta a régua clássica).
#
# Risco de oversup: este módulo é abrangente. Em casos limítrofes (3-4 confluências
# e contexto não ideal), preferir SETUP_CANDIDATO_FORTE em vez de SETUP_VALIDO.
# ============================================================================


def build_prompt(alert: dict) -> str:
    alert_type = alert.get("alert_type", "setup_recheck")
    # === External Market Factors block (Fase 1 Passive Logging — 2026-05-12) ===
    ext = alert.get("external_factors") or {}
    ext_bias = ext.get("external_bias", "unknown")
    ext_risk = ext.get("external_risk_level", "unknown")
    ext_tv = ext.get("external_trade_validation", "neutral")
    ext_conf = ext.get("external_confidence", 0)
    ext_reasons = ext.get("external_main_reasons", []) or []
    ext_supportive = ext.get("external_supportive_factors", []) or []
    ext_risks = ext.get("external_risk_factors", []) or []
    ext_blocking = ext.get("external_blocking_factors", []) or []
    ext_decision = ext.get("external_decision_note", "")
    ext_ok = ext.get("external_fetch_ok", False)
    ext_stale = ext.get("external_stale", True)
    ext_age = ext.get("external_age_minutes", None)
    ext_err = ext.get("external_fetch_error", "")
    ext_ts = ext.get("external_timestamp_utc", "")
    ext_freshness_label = "FRESH" if (ext_ok and not ext_stale) else ("STALE" if ext_ok else "FETCH_FAILED")

    macro_context_block = textwrap.dedent(f"""
    External Market Factors (iMac analyst — Fase 1 Passive Logging):
    - Bias: {ext_bias}
    - Risk level: {ext_risk}
    - Trade validation: {ext_tv}
    - Confidence: {ext_conf}
    - Main reasons: {ext_reasons}
    - Supportive factors: {ext_supportive}
    - Risk factors: {ext_risks}
    - Blocking factors: {ext_blocking}
    - Decision note: {ext_decision}
    - Timestamp UTC: {ext_ts}
    - Age (minutes): {ext_age}
    - Freshness: {ext_freshness_label}
    - Fetch ok: {ext_ok}
    - Stale: {ext_stale}
    - Fetch error: {ext_err}

    INSTRUÇÃO CRÍTICA — FASE 1 PASSIVE LOGGING (NÃO ALTERE CLASSIFICAÇÃO):
    Esta camada externa é INFORMATIVA APENAS nesta fase. Você DEVE:
    1. Registrar TODOS os campos acima dentro do seu output em um bloco intitulado:
       "Macro context (Fase 1 passive logging):"
       Espelhe os campos exatamente como recebidos.
    2. NÃO usar Trade validation (confirm/neutral/caution/block) para alterar a classificação técnica.
    3. NÃO downgrade nem upgrade da Classificação por causa de macro nesta fase.
    4. NÃO alterar Promotion status por causa de macro.
    5. NÃO mencionar macro como motivo de bloqueio ou aprovação operacional.
    6. Se Fetch failed ou Stale, registrar isso no bloco mas continuar análise técnica normalmente.
    7. Continue classificando puramente pela régua técnica + módulos experimentais existentes.

    Razão da Fase 1: estamos validando a qualidade do filtro externo antes de deixá-lo afetar decisões. Após 50+ eventos teremos dados para correlacionar contexto macro com outcome real em D2R e decidir se o filtro tem valor preditivo.
    """).strip()

    return textwrap.dedent(f"""
    Você está rodando em modo automático de reavaliação após alerta do TradingView.

    Leia obrigatoriamente estes arquivos antes da análise:
    {OP_PROMPT}
    {RULES}
    {CANDIDATO_FORTE_DOC}
    {PROMOTION_POLICY_DOC}
    {MODULE_AWARE_RULES_DOC}
    {XAUUSD_4H_BREAKOUT_REGIME_DOC}
    {XAUUSD_1H_DECISIVE_DOC}
    {XAGUSD_1H_DECISIVE_DXY_DOC}
    {XAUUSD_INTRADAY_BB_DOC}
    {US500_4H_FAILED_BREAKDOWN_DOC}
    {US500_1H_BREAKOUT_REGIME_DOC}
    {ETHUSD_4H_BREAKOUT_REGIME_DOC}
    {ETHUSD_1H_PULLBACK_REGIME_DOC}
    {EURUSD_4H_COMBO_DXY_DOC}
    {EURUSD_1H_DECISIVE_DOC}

    Alerta recebido:
    ```json
    {json.dumps(alert, ensure_ascii=False, indent=2)}
    ```

    Tipo do alerta:
    {alert_type}

    {macro_context_block}

    Regras críticas:
    - Alertas são gatilhos de reavaliação, não sinais de entrada.
    - A classificação final depende do gráfico atual, não do momento em que o alerta foi criado.
    - Não execute ordens.
    - Não edite Pine Script.
    - Não altere strategy_rules.json.
    - Não promova INTRADAY_QUASE_VALIDO, QUASE_VALIDO ou SETUP_CANDIDATO_FORTE a SETUP_VALIDO.
    - QUASE_VALIDO / INTRADAY_QUASE_VALIDO ficam obsoletos como linguagem operacional nova.
    - Use SETUP_CANDIDATO_FORTE quando houver oportunidade assimétrica forte para revisão humana.
    - SETUP_CANDIDATO_FORTE é revisão humana; não é entrada automática e não autoriza trade.

    REGRAS OPERACIONAIS V4 (D2R Phase 1 — 2026-05-13, baseadas em 95 trades reais):

    1. **BUBBLE CLUSTER GATE (restrito por TF — atualizado 2026-05-15):**
       - TF 15M / 30M: SEM cluster bubbles → no MÁXIMO SETUP_EM_OBSERVACAO.
         Razão: LTF mais propenso a noise; cluster é confluência crítica em baixa
         resolução temporal.
       - TF 1H / 4H / 12H / 1D: cluster bubbles é OPCIONAL. NÃO bloqueia promoção
         a SETUP_CANDIDATO_FORTE quando ausente. Outras confluências estruturais
         (CHoCH/BOS, RSI extremo, divergência, sweep, NAS, rejeição, zona nested
         HTF) substituem o sinal de cluster.
         Razão: auditoria 2026-05-15 (n=557 records operacionais) mostrou cluster
         present em 0/13 records TF 4H. Gate impedia CANDIDATO_FORTE em 4H —
         justamente o TF de melhor win rate documentado (D2R Phase 1: TF 4H = 71%
         win, avg +1.63R). Phase 1 (n=2 no grupo controle sem cluster) é base
         estatística frágil; relaxamento por TF mantém proteção em LTF onde
         noise domina e libera HTF onde estrutura dispensa cluster.
       - Em TF 1H / 4H / 12H / 1D: AINDA assim, se cluster bubble estiver PRESENT,
         tratar como confluência extra forte (peso na decisão).

    2. **SHORT side — política por ativo (PR 4, D2R n=220 atualizado 2026-05-14):**
       ATIVOS COM SHORT OPERACIONAL (podem virar CANDIDATO_FORTE se critérios OK):
       - **ETHUSD SHORT**: OPERACIONAL (n=10, 60% win, +11.33R) — edge-surpresa confirmado em PR 4.
       - **XAGUSD SHORT**: OPERACIONAL (n=8, 50% win, +4.16R).
       - **EURUSD SHORT**: OPERACIONAL (n=3, 67% win, +3.37R) — sample pequeno mas positivo.
       - **BTCUSD SHORT**: aceito com rigor padrão (sample baixo para decisão).

       ATIVOS COM SHORT EM SHADOW DEFENSIVO (máx SETUP_EM_OBSERVACAO, NUNCA CANDIDATO_FORTE):
       - **XPTUSD SHORT**: PR 4 relaxou de BLOCKED para máx OBSERVACAO (n=25, 40% win, +8.24R — inversão vs PR1 mas ainda preliminar).
       - **US500 SHORT**: DEGRADADO (n=3, 0% win, -3R). Máximo SETUP_EM_OBSERVACAO.
       - **XAUUSD SHORT**: marginal (n=23, 39% win). Máximo SETUP_EM_OBSERVACAO até nova análise.
       - **USOUSD SHORT**: BLOQUEADO operacionalmente (n=6, 17% win, -2.58R). Pode classificar OBSERVACAO ou NO_TRADE.

       Em todos os casos: bear divergence obrigatória + CHoCH/BOS fechado + cluster bubbles para CANDIDATO_FORTE.

    3. **LONG side — política por ativo (PR 4, D2R n=220):**
       ATIVOS COM LONG OPERACIONAL (podem virar CANDIDATO_FORTE se critérios OK):
       - **US500 LONG**: 💎 jewel (n=7, 100% win, +14.54R) — configuração mais forte do sistema.
       - **XPTUSD LONG**: OPERACIONAL (n=6, 83% win, +16.39R) — PR 4 desbloqueou, sample dobrou desde PR1.
       - **EURUSD LONG**: OPERACIONAL (n=3, 100% win, +5.96R).
       - **USOUSD LONG**: OPERACIONAL (n=5, 80% win, +6.81R) — confirmado em PR 1.
       - **ETHUSD LONG**: OPERACIONAL (n=21, 57% win, +18.28R) — sólido.
       - **XAUUSD LONG**: OPERACIONAL (n=13, 46% win, +7.03R) — sólido com rigor padrão.
       - **BTCUSD LONG**: aceito com rigor padrão.

       Nenhum LONG bloqueado por ativo no PR 4.

    4. **Priorização TF 4H + TF 15M LONG (atualizado 2026-05-15 — D2R Phase 2 n=208):**
       - TF 4H continua STAR: +1.08R, 59% win, PF 3.98 (n=22). Peso MAIOR na classificação.
       - TF 15M LONG: prioridade IGUAL a TF 4H quando direção LONG + ativo whitelist.
         Evidência D2R Phase 2: TF 15M LONG entrega +1.50R, 72% win, PF 6.38 (n=18) —
         equivalente a TF 4H LONG (+1.43R, 75% win, PF 9.61 em n=12).
         NÃO aplicar rigor extra em 15M LONG. Critérios standard suficientes para
         promoção a CANDIDATO_FORTE. Ativos com edge LONG confirmado: US500
         (TF 15M: +1.14R / 73% win em n=11), XPTUSD (+0.87R / 42% / n=19), ETHUSD,
         XAUUSD (LONG operacional em todos TFs).
       - TF 15M SHORT: rigor padrão (sem tratamento especial nem promoção facilitada).
         Evidência: TF 15M SHORT entrega +0.40R, 38% win (n=26) — mediano, sem edge claro.
       - TF 30M: rigor extra mantido para promoção a CANDIDATO_FORTE — precisam
         confluência adicional além do mínimo (3 fortes).

    5. **Calibração CANDIDATO_FORTE vs OBSERVACAO V2 (atualizado 2026-05-15 — D2R Phase 2 n=208):**

       Phase 1 (n=50) sugeriu inversão (CF +0.12 vs OBS +0.85, Δ -0.73). Phase 2
       com 4× mais dados mostra equivalência geral (CF +0.54 vs OBS +0.59, Δ -0.05).
       A inversão real é LOCAL, não universal.

       Onde CF SUPERA OBS claramente (regra antiga deixava dinheiro na mesa):
         - TF 15M: CF +1.19R vs OBS +0.72R (Δ +0.47)
         - TF 4H:  CF +2.06R vs OBS +0.93R (Δ +1.14)
         - ETHUSD: CF +1.49R vs OBS +0.56R (Δ +0.93)
         - XPTUSD: CF +0.87R vs OBS -0.10R (Δ +0.97)

       Onde a INVERSÃO real existe (preferir OBSERVACAO):
         - TF 60 (1H) + direção SHORT: CF +0.09R / 25% win vs OBS +0.68R / 56% win (Δ -0.59)
         - XAUUSD com sinais marginais (apenas 1 confluência além do trigger,
           típico CHoCH solo): CF +0.24R vs OBS +0.61R (Δ -0.37 no geral XAU)

       Observação importante (D2R retroativo n=208):
         - 24 records OBSERVACAO (16% do total OBS) entregaram +2.85R / 100% win
           retroativamente — setups rebaixados a OBS por excesso de cautela.
         - Esses são os "jewels perdidos" que esta calibração V2 visa recuperar.

       DIRETRIZ V2 (substitui "em dúvida prefira OBSERVACAO"):
         DEFAULT: quando critérios de CANDIDATO_FORTE passam, PROMOVER. Não rebaixar
                  por excesso de cautela.

         EXCEÇÕES — preferir OBSERVACAO mesmo com critérios borderline OK:
           (a) TF 60 (1H) + direção SHORT — independente do ativo
           (b) XAUUSD SHORT com apenas 1 confluência forte além do trigger
               (típico: CHoCH único sem RSI extremo/sweep/NAS confluência adicional)

         Em todos os outros contextos (TF 15M, 30M, 4H; ETHUSD, XPTUSD, EURUSD,
         BTCUSD, US500, USOUSD; LONG ou SHORT exceto exceção a): promover a
         CANDIDATO_FORTE quando critérios passam.

       Coerente com regras V4 anteriores: bubble gate LTF (15M/30M) mantido,
       hard blocks ativos, R:R>=2:1, stop estrutural — todos esses continuam
       sendo pré-requisitos OBJETIVOS antes desta calibração subjetiva.

    ═══════════════════════════════════════════════════════════════════════════
    REGRAS INTERIM — sample insuficiente (auditoria 2026-05-15)
    ═══════════════════════════════════════════════════════════════════════════
    Sample gate institucional (memória feedback_sample_gate_for_rules):
      n<30      → hipótese; NÃO muda comportamento sem flag interim
      n=30-49   → muda como INTERIM com prazo de revalidação
      n=50-99   → muda como preliminar, monitorar reversão
      n≥100     → regra estável
      Sub-cohort: requer 2× o n do tier (ex: TF×ativo×direção requer n≥60 direcional)

    As 3 regras abaixo foram editadas hoje com sample frágil. Comportamento
    está ativo, MAS são hipóteses operacionais. Quando atingir threshold de
    revalidação, decidir manter/reverter com base em outcome live.

    INTERIM #1 — Bubble gate relaxado em TF 1H+ (eb1df5b, 2026-05-15)
      Sample atual: n=13 records TF 4H (presence rate 0/13 = 0%)
      Revalidar quando: n≥50 records TF 4H operacionais OU 90 dias forward
      Reverter se: CF promovidos em TF 1H+ sem cluster tiverem PF<1.2 em n≥20

    INTERIM #2 — TF 15M LONG liberado de "rigor extra" (c274247, 2026-05-15)
      Sample atual: TF 15M LONG D2R n=18 (avg +1.50R, win 72%, PF 6.38)
      Revalidar quando: n≥50 D2R outcomes TF 15M LONG
      Reverter se: win cair para <50% OU PF<1.4 em n≥30

    INTERIM #3 — CF vs OBS V2 carve-outs TF 1H SHORT + XAU SHORT marginal
                 (2fab450, 2026-05-15)
      Sample atual: TF 60 SHORT total n=36 (20 CF + 16 OBS); XAU SHORT 1H n=21
      Revalidar quando: n≥60 TF 60 SHORT OU n≥30 XAU SHORT 1H novos pós-V2
      Reverter se: regra Phase 1 ("em dúvida OBS") provar superior em re-audit

    Outras mudanças hoje com sample OK (não-interim):
      - Hard blocks refactor (7b41064): refactor estrutural, não muda regra estatística
      - Entry late narração escalonada (4bf7cf3): threshold mantido, só verbosity
      - OBS silenced Telegram (c7ccff6): routing change, n=107 OBSERVACAO ≥30

    Disciplina: NÃO criar novas regras frágeis sobre estas até revalidar.
    ═══════════════════════════════════════════════════════════════════════════

    - Pode criar alertas de monitoramento se permitido pelas regras existentes.
    - Pode desenhar marcações próprias AUTO_CLAUDE_ se permitido pelas regras.
    - Seja curto e operacional, pois a resposta será enviada ao Telegram.

    Regra experimental principal:
    Avalie se o alerta se enquadra como SETUP_CANDIDATO_FORTE conforme setup_candidato_forte_policy.md.

    Use SETUP_CANDIDATO_FORTE quando houver oportunidade assimétrica forte para revisão humana, com:
    - zona ou linha operacional relevante AUTO_CLAUDE_;
    - preço tocando, entrando, reagindo ou muito próximo da zona/linha;
    - direção operacional clara;
    - stop técnico claro;
    - R:R estimado >= 2:1;
    - sem janela macro vermelha imediata;
    - pelo menos 3 confluências fortes.

    Confluências fortes incluem:
    - RSI extremo ou recém saindo de extremo;
    - divergência Regular Bull/Bear;
    - CHoCH/BOS;
    - sweep/reentry;
    - sinal NAS100 LONG/SHORT dentro ou na borda da zona;
    - rejeição clara;
    - cluster Market Order Bubbles;
    - zona nested em HTF;
    - linha dinâmica de invalidação/reentry/breakout;
    - contexto HTF favorecendo direção;
    - price action esticado chegando em supply/demand.

    Não use mais QUASE_VALIDO / INTRADAY_QUASE_VALIDO em novas respostas operacionais.
    Se a oportunidade for forte, use SETUP_CANDIDATO_FORTE.
    Se não for forte, use SETUP_EM_OBSERVACAO ou NO_TRADE.

    Se for SETUP_CANDIDATO_FORTE:
    - deixe claro que NÃO é entrada automática;
    - inclua R:R estimado;
    - inclua stop técnico;
    - inclua gatilho faltante;
    - inclua “REVISÃO HUMANA”.
    
    Política experimental de promoção:
    Avalie também se o SETUP_CANDIDATO_FORTE possui gatilho objetivo suficiente para promoção.

    Use Promotion trigger:
    - NONE
    - REJECTION_CLOSE
    - SWEEP_REENTRY
    - CHOCH_BOS
    - BREAKOUT_RETEST
    - DENSE_STRUCTURAL_CONFLUENCE

    Use Promotion status:
    - NOT_PROMOTED
    - KEEP_AS_CANDIDATO_FORTE
    - PROMOTE_TO_SETUP_VALIDO
    - DOWNGRADE_TO_OBSERVACAO
    - NO_TRADE

    Importante:
    - DENSE_STRUCTURAL_CONFLUENCE sozinho não promove para SETUP_VALIDO.
    - Para PROMOTE_TO_SETUP_VALIDO, precisa haver gatilho objetivo: rejection close, sweep/reentry, CHoCH/BOS ou breakout retest.
    - Nunca promova se R:R < 2:1, stop não estiver claro, leitura MCP falhar ou houver macro red window.
    - Esta política é experimental e deve ser medida em D2R.
    - Não diga que "a regra do alerta proíbe promover" SETUP_CANDIDATO_FORTE para SETUP_VALIDO.
    - A formulação correta é: "os critérios de promoção ainda não foram preenchidos" ou "promoção não confirmada".
    - Se mantiver como SETUP_CANDIDATO_FORTE, explique quais critérios faltaram: confirmação, CHoCH/BOS, R:R, stop, RSI, bubbles, NAS100, rejeição fechada ou follow-through.


    Política ativa — MODULE_AWARE_GLOBAL_RULES_V3 (shadow mode REMOVIDO em 2026-05-12):
    - Apenas 7 classificações canônicas existem agora:
      SETUP_VALIDO, SETUP_VALIDO_INTRADAY, SETUP_CANDIDATO_FORTE, SETUP_EM_OBSERVACAO,
      NO_TRADE, SETUP_PERDIDO_NAO_PERSEGUIR, SETUP_ATRASADO_AGUARDAR_RETESTE.
    - NÃO usar: SETUP_VALIDO_SHADOW, SETUP_VALIDO_INTRADAY_SHADOW, SETUP_OPERACIONAL_MANUAL,
      SETUP_FORTE, SETUP_EXCELENTE, INTRADAY_*, SETUP_CANDIDATO_FORTE_INTRADAY.
    - Distinção intraday/swing é via campo `Execution TF`, não via nome da classificação,
      exceto SETUP_VALIDO_INTRADAY que é mantido como classificação distinta.

    ═══════════════════════════════════════════════════════════════════════════
    CLASSIFICAÇÃO V4 SHADOW (2026-05-14 — paralelo a V3, NÃO substitui)
    ═══════════════════════════════════════════════════════════════════════════
    Em PARALELO à classificação V3 (obrigatória, mantém Telegram routing), emita
    também uma classificação V4 SHADOW. V4 reflete o discriminador real de edge
    identificado em D2R (n=220): entry_model + R:R + gatilho fechado.

    V4 tem 4 categorias APENAS:
      1. NO_TRADE_V4              — Hard block, late, invalidated, MCP fail
      2. SETUP_INFO_ONLY          — Estrutura interessante mas sem gatilho operacional
                                    (line_break/trendline/breakout SEM R:R≥2 OU SEM confirmação fechada)
      3. SETUP_ZONE_WATCH         — Zona ativa testada, SEM candle fechado de confirmação
                                    (= zone_touch puro, mesmo com confluências múltiplas)
      4. SETUP_CONFIRMED_ENTRY    — Candle de gatilho FECHOU + R:R≥2:1 + sem blockers ativos
                                    (= reentry/breakout_retest/confirmation_close/line_break com
                                    tradeable=True por critério estrito)

    REGRA DE MAPEAMENTO V4 (curto-circuitada, parar no primeiro match):
      1. hard_blocks failed → NO_TRADE_V4
      2. entry_model ∈ {{confirmation_close, breakout_retest, line_break}}:
         a. + R:R ≥ 2:1 + stop estrutural + sem blockers ativos → SETUP_CONFIRMED_ENTRY
         b. caso contrário                                       → SETUP_INFO_ONLY
      3. entry_model = reentry:
         a. + R:R ≥ 2:1 + stop estrutural + V3 = CANDIDATO_FORTE  → SETUP_CONFIRMED_ENTRY
         b. caso contrário                                        → SETUP_ZONE_WATCH
      4. entry_model = zone_touch → SETUP_ZONE_WATCH (NUNCA promover por confluência)
      5. alert_type com line/trendline/breakout/invalidation sem gatilho → SETUP_INFO_ONLY
      6. default → SETUP_ZONE_WATCH

    FUNDAMENTAÇÃO ESTATÍSTICA (D2R n=220 limpa, sem USDJPY):
      - SETUP_CONFIRMED_ENTRY: 69% win, avg +1.97R (n=26) — high-probability
      - SETUP_ZONE_WATCH:      50% win, avg +0.57R (n=98) — espere gatilho
      - SETUP_INFO_ONLY:       46% win, avg +0.71R (n=13) — marginal
      - Hipótese central: confluências múltiplas em zona costumam aparecer DEPOIS
        do move (fade tardio). Candle fechado de confirmação marca o INÍCIO do move.

    REGRA DE SHADOW MODE:
      - V4 é LOGGADO mas NÃO altera Telegram routing nem decisões operacionais.
      - Telegram continua usando V3 (Classificação:).
      - Validação contra outcomes D2R reais em 1 semana antes de migrar.
      - Emita SEMPRE as DUAS classificações no output.

    OUTPUT OBRIGATÓRIO no fim da resposta — UMA linha cada:
      Classificação: <uma das 7 strings V3 — ver vocabulário estrito abaixo>
      Classificação V4: <NO_TRADE_V4 | SETUP_INFO_ONLY | SETUP_ZONE_WATCH | SETUP_CONFIRMED_ENTRY>
    ═══════════════════════════════════════════════════════════════════════════

    ═══════════════════════════════════════════════════════════════════════════
    V3D SHADOW — Leonardo OB estrutural (atualizado 2026-05-15 — XAUUSD, EURUSD em TF=240/4H)
    ═══════════════════════════════════════════════════════════════════════════
    APLICAR para alertas em XAUUSD ou EURUSD com timeframe=240 (4H).
    Para outros ativos ou TFs, emitir todos os campos V3d como N/A.

    Evidência empírica (backtest 7.4 anos, audit SMC6 2026-05-15):
    - XAUUSD 4H: V3d n=37, +9.28R, win 43%, PF 1.49 — COMPLEMENTAR ao mech
      (Pearson -0.05, só 2 overlap em 7.4y, +14% R combinado, Sharpe igual).
    - EURUSD 4H: V3d n=45, +25.75R, win 53%, PF 2.65, Sharpe 2.26 — FORTE.
      Combinado com mech: +172% R, Sharpe +1.10, MaxDD MELHORA. V3d cobre 2021
      e 2022 (anos onde mech praticamente não disparou). Overlap 8.5%.
    Ativos onde V3d NÃO se aplica (auditados, perdedores em backtest):
    - BTCUSD 4H: DEACTIVATED 2026-05-21 no cleanup (fora do foco XAU-only)
    - ETHUSD 4H: V3d -13.69R, Sharpe -2.41 (falha em bear cripto)
    - XAGUSD 4H: V3d -3.67R, Sharpe -0.44 (estrutura SMC ruidosa)
    - XPTUSD/US500 4H: marginais e dependentes de 1 ano outlier

    Avaliar V3d Leonardo Order Block:
    1. Identificar último BOS_BULL ou CHOCH_BULL nos últimos 30 candles 4H:
       - BOS_BULL: candle com close > pivot_high(5,5) anterior
       - CHOCH_BULL: idem após sequência bearish
    2. Se evento encontrado, identificar Order Block Leonardo:
       - Último candle BEARISH (close < open) ANTES da pernada de impulso
       - Range do OB: [low, high] desse candle
    3. Identificar último fundo válido (LVB):
       - Low mínimo entre o evento e seu pivot low anterior
    4. Verificar se preço atual está em zona OB:
       - low_atual <= ob_top
    5. Calcular potencial trade:
       - Entry = ob_top
       - Stop = LVB (sem buffer)
       - Target = entry + 5R
       - R_pts = entry - stop

    REGRA DE SHADOW:
      - V3d é APENAS LOGADO. NÃO altera classificação V3, V4 ou Telegram.
      - Validação forward: D2R comparará outcomes V3d com mecânico.
      - Critério promoção a operacional: 30+ trades V3d shadow com PF≥1.4 e
        no_top5≥0.

    OUTPUT V3D OBRIGATÓRIO — adicionar 7 linhas:
      V3d shadow asset: <XAUUSD | EURUSD | N/A>
      V3d shadow event present: <true | false | N/A>
      V3d shadow event type: <BOS_BULL | CHOCH_BULL | NONE | N/A>
      V3d shadow OB zone: <"low-top" | N/A>
      V3d shadow LVB stop: <preço | N/A>
      V3d shadow in zone now: <true | false | N/A>
      V3d shadow R potential pts: <número | N/A>
    ═══════════════════════════════════════════════════════════════════════════

    ═══════════════════════════════════════════════════════════════════════════
    MTF SHADOW — HTF BOS/CHOCH gate (Hybrid Grade A/B, audit MTF1 2026-05-15)
    ═══════════════════════════════════════════════════════════════════════════
    APLICAR APENAS para alertas em XAUUSD 4H, EURUSD 4H ou EURUSD 1H que
    disparam módulo mecânico (SETUP_VALIDO ou SETUP_CANDIDATO_FORTE).

    NÃO APLICAR (emitir N/A) para:
    - XAUUSD 1H: filtro testado, HURTS edge (-3.46 Sharpe vs misaligned)
    - XAGUSD 1H: filtro testado, HURTS edge (-0.34 Sharpe vs misaligned)
    - ETHUSD 1H PULLBACK: lookback BOS recente não aplicável a pullback
    - US500 4H FAILED_BREAKDOWN: trigger contra-tendência, SMALL_N inconclusivo
    - ETH 4H BREAKOUT v1.2: marginal (+0.46 Sharpe), não vale overhead
    - US500 1H BREAKOUT: marginal (+0.28 Sharpe), não vale overhead
    - Qualquer outro asset/TF: emitir todos os campos MTF como N/A.

    Evidência empírica (backtest 7.4 anos, audit MTF1 em módulos reais):
    - XAUUSD 4H BREAKOUT_CONTINUATION: aligned PF 3.37 (Sharpe +2.40) vs
      misaligned PF 1.45 (Sharpe +1.83) — Δ Sharpe +0.57. n=234.
    - EURUSD 4H BREAKOUT_COMBO_STRICT_DXY: aligned PF 5.04 (Sharpe +1.77) vs
      misaligned PF 1.54 (Sharpe +0.93) — Δ Sharpe +0.84. n=47.
    - EURUSD 1H DECISIVE_HTF1D_DXY: aligned PF 3.86 (Sharpe +1.59) vs
      misaligned PF 1.22 (Sharpe +0.57) — Δ Sharpe +1.02. n=73.

    Mapeamento HTF:
    - XAUUSD 4H trigger → HTF = 1D
    - EURUSD 4H trigger → HTF = 1D
    - EURUSD 1H trigger → HTF = 4H

    Verificação MTF (BOS/CHOCH HTF nos últimos 6 candles HTF):
    1. Identificar HTF aplicável (ver tabela acima)
    2. Puxar OHLCV HTF (~50 candles) via MCP — chart_set_symbol + chart_set_timeframe + data_get_ohlcv
    3. Aplicar mesma lógica BOS/CHOCH do V3d:
       - BOS_BULL: close > pivot_high(5,5) anterior + trend já era 1
       - CHOCH_BULL: close > pivot_high(5,5) anterior + trend anterior era -1
    4. Verificar: algum evento BOS_BULL/CHOCH_BULL ocorreu nos ÚLTIMOS 6 CANDLES HTF
       antes do timestamp atual?
    5. Restaurar chart_set_symbol e chart_set_timeframe ao original do alerta

    REGRA DE SHADOW (atual — não altera classificação ainda):
      - MTF é APENAS LOGADO. NÃO altera classificação V3 nem V4 nem Telegram.
      - Acumulação live → após n≥30 trades com MTF preenchido em módulo X,
        validar prospectivamente se mtf_aligned=true tem PF/Sharpe superior.
      - Critério promoção a Hybrid (futuro):
          SETUP_VALIDO  ← módulo + mtf_aligned=true (Grade A, position cheio)
          SETUP_CANDIDATO_FORTE ← módulo + mtf_aligned=false (Grade B, reduzido)

    OUTPUT MTF OBRIGATÓRIO — adicionar 3 linhas:
      MTF shadow applicable: <true | false>
      MTF shadow HTF used: <1D | 4H | N/A>
      MTF shadow aligned: <true | false | N/A>
    ═══════════════════════════════════════════════════════════════════════════

    REGRA PREVALECENTE — VOCABULÁRIO ESTRITO V3 (esta seção prevalece sobre qualquer outra):
    - Use APENAS estas 7 strings exatas como valor de "Classificação:":
        1. SETUP_VALIDO
        2. SETUP_VALIDO_INTRADAY
        3. SETUP_CANDIDATO_FORTE
        4. SETUP_EM_OBSERVACAO
        5. NO_TRADE
        6. SETUP_PERDIDO_NAO_PERSEGUIR
        7. SETUP_ATRASADO_AGUARDAR_RETESTE
    - NÃO emita as seguintes strings em "Classificação:" (são DEPRECADAS):
        ❌ SETUP_CANDIDATO_FORTE_INTRADAY    → use SETUP_CANDIDATO_FORTE com Execution TF: 15/30/60
        ❌ INTRADAY_EM_OBSERVACAO            → use SETUP_EM_OBSERVACAO com Execution TF: 15/30/60
        ❌ SETUP_EM_OBSERVACAO_INTRADAY      → use SETUP_EM_OBSERVACAO com Execution TF: 15/30/60
        ❌ INTRADAY_SETUP_VALIDO             → use SETUP_VALIDO_INTRADAY
        ❌ INTRADAY_SETUP_FORTE              → use SETUP_VALIDO_INTRADAY (Priority A)
        ❌ INTRADAY_SETUP_EXCELENTE          → use SETUP_VALIDO_INTRADAY (Priority A)
        ❌ INTRADAY_NO_TRADE                 → use NO_TRADE com Execution TF: 15/30/60
        ❌ SETUP_FORTE / SETUP_EXCELENTE     → use SETUP_VALIDO (Priority A)
        ❌ SETUP_VALIDO_SHADOW / *_SHADOW    → use SETUP_VALIDO ou SETUP_VALIDO_INTRADAY
        ❌ SETUP_OPERACIONAL_MANUAL          → use SETUP_VALIDO ou SETUP_VALIDO_INTRADAY
    - NUNCA acrescente sufixo _INTRADAY a nenhuma classificação além de SETUP_VALIDO_INTRADAY.
    - NUNCA use o prefixo INTRADAY_ em nenhuma classificação.
    - Se você se pegar prestes a escrever uma string deprecada, PARE e use a string V3 + Execution TF.
    - O campo Execution TF carrega a informação de timeframe; a classificação carrega apenas a tier.

    PRE-VALIDADO MECANICAMENTE (Caminho A — Pines mecânicos, 2026-05-19):
    Quando alert.alert_type começa com "module_trigger_", o setup JÁ PASSOU todos os
    triggers + filtros mecânicos do módulo no candle FECHADO (validação Pine in-chart,
    backtest 7 anos). NÃO re-detectar módulo, NÃO re-validar triggers do payload.
    Confiar no payload Pine e focar APENAS em:

      1. Hard blocks APLICÁVEIS aos pines mecânicos (subset reduzido — Pine
         já garante o resto):
           - MCP_UNRELIABLE (infra: leitura MCP do TradingView falhou)
           - ENTRY_LATE_CHASING (entry_late_distance_r >= 0.5)
           - SETUP_LOST_NO_CHASE (preço passou demais; |entry_late_distance_r| alto)
           - RR_BELOW_2 (apenas se Claude recalcular stop por estrutura e R:R cair < 2)
         Se algum APLICÁVEL FAIL → NO_TRADE com motivo.

         NÃO aplicar aos pines mecânicos (Pine garante por design, ou subjetivo
         conflitante com a tese mecânica do módulo):
           - DIRECTION_UNDEFINED (Pine envia direction explícito no payload)
           - NO_OBJECTIVE_TRIGGER (Pine É o trigger objetivo — close > swing_high,
             body%, ADX, EMA50, etc. dependendo do módulo)
           - ONLY_NOISE_NO_STRUCTURE (Pine usa estrutura: swing high/low + ATR +
             body% + ADX + EMA — não é noise por design)
           - FALLING_KNIFE (CONFLITA com módulos BREAKOUT_CONTINUATION /
             FAILED_BREAKDOWN / pullback regime — Pine compra em movimento forte
             por design, essa É a tese da estratégia testada 7 anos)

      2. Contexto de entry: preço atual ainda perto de alert.entry_price?
         entry_late_distance_r = (price_atual - alert.entry_price) / alert.r_points
         (LONG: positivo significa atrasado; SHORT: negativo significa atrasado).
         Se |entry_late_distance_r| >= 0.5 → SETUP_ATRASADO_AGUARDAR_RETESTE.

      3. Reaproveitar do payload SEM recalcular nem questionar:
         alert.entry_price, alert.stop_price, alert.target_price_4r, alert.r_points,
         alert.priority, alert.strategy_module, alert.module_backtest_n, alert.direction.

      4. External factors permanecem informativos (Fase 1 passive) — NÃO afetam decisão.

      5. Classificação default por alert_type (se hard blocks PASS e entry NÃO atrasado):

         SETUP_VALIDO direto (4H, regra estável, backtest sólido):
           - module_trigger_xauusd_4h_breakout_continuation       (n=234, PF 1.64)
           - module_trigger_ethusd_4h_breakout_regime             (regime-filtered)
           - module_trigger_eurusd_4h_breakout_combo_strict_dxy   (combo DXY strict)
           - module_trigger_us500_4h_failed_breakdown             (failed breakdown)

         SETUP_CANDIDATO_FORTE (1H INTERIM, aguarda n>=30 forward):
           - module_trigger_eurusd_1h_decisive_htf1d_dxy          (n=73,  PF 1.46)
           - module_trigger_xagusd_1h_decisive_dxy_structural     (n=69,  PF 1.79)
           - module_trigger_us500_1h_breakout_regime              (n=222, PF 1.22)
           - module_trigger_ethusd_1h_pullback_ema50              (n=96)
         (XAUUSD_1H_LONG_DECISIVE_BODY60_HTF removido 2026-06-01 — visual auction-theory review rejected; sem substituto LONG 1H ativo para XAUUSD)

      6. ECOAR no stdout campos obrigatórios (extract_field do receiver lê de lá):
         Strategy Module: <copiar de alert.strategy_module>
         Module backtest n: <copiar de alert.module_backtest_n>
         Direção: <copiar de alert.direction>
         Entry: <copiar de alert.entry_price>
         Stop: <copiar de alert.stop_price>
         Target: <copiar de alert.target_price_4r>
         R points: <copiar de alert.r_points>
         Priority: <copiar de alert.priority>
         Trigger: <copiar de alert.trigger_method>
         Promotion trigger: MECHANICAL_PINE_VALIDATED
         Operational signal: YES_MANUAL_REVIEW
         D2R required: true
         Entry late distance R: <valor calculado>

    Hierarquia de avaliação CURTO-CIRCUITADA (parar no primeiro FAIL):
      0. PRE-VALIDADO MECANICAMENTE: se alert.alert_type começa com "module_trigger_"
         → seguir bloco acima. Pular itens 1-5 desta hierarquia (módulo já validado
         mecanicamente pelo Pine; só checar hard blocks + entry timing).
      1. hard_blocks: se FAIL → NO_TRADE. Preencher Hard block triggered. STOP.
      2. module_detection: se nenhum módulo formal aplica → régua clássica, máximo SETUP_CANDIDATO_FORTE.
         Se múltiplos aplicam → resolver via precedência (SWING>INTRADAY; direções conflitantes=NO_TRADE; A>B>C; maior module_backtest_n; menor TF).
      3. module_checklist: se FAIL → SETUP_CANDIDATO_FORTE máximo. Preencher Module checklist failed on.
      4. promotion_trigger: se NONE → SETUP_CANDIDATO_FORTE máximo.
      5. entry_quality: se R:R/stop falham → NO_TRADE ou SETUP_EM_OBSERVACAO. Se entry late → SETUP_ATRASADO_AGUARDAR_RETESTE.
         Se tudo passa → promover a SETUP_VALIDO (swing) ou SETUP_VALIDO_INTRADAY (intraday).

    Hard blocks globais (atualizado 2026-05-15 — enum fixo, dormentes removidos):

      ATIVOS (disparam quando aplicável):
        - MCP_UNRELIABLE                — leitura MCP falhou/inconsistente
        - DIRECTION_UNDEFINED           — direção indefinida ou incompatível com módulo
        - RR_BELOW_2                    — R:R < 2:1
        - ENTRY_LATE_CHASING            — entry_late_distance_r >= 0.5
        - SETUP_LOST_NO_CHASE           — setup perdido / preço já passou
        - FALLING_KNIFE                 — falling knife ou melt-up chase evidente
        - NO_OBJECTIVE_TRIGGER          — ausência de gatilho objetivo
        - ONLY_NOISE_NO_STRUCTURE       — setup baseado APENAS em RSI/NAS/Bubble/dry zone
                                          touch sem ESTRUTURA DE PREÇO
                                          (ver accepted_price_structures em strategy_rules.json)

      DORMENTE (NÃO disparar até further notice):
        - MACRO_RED_WINDOW              — DORMENTE 2026-05-15. External Factors writer iMac
                                          está degenerado (calendar_active=False em 100% de
                                          87 healthy records). Sem fonte confiável → não
                                          usar como hard block. Reativar após patch iMac
                                          (real yield escalonado + writer 9 fatores).

      OPERATIONAL GATES (NÃO são hard blocks globais, são downgrade caps por ativo/TF):
        - BUBBLE_CLUSTER_GATE_LTF       — TF 15M/30M sem cluster → max OBSERVACAO
                                          (TF 1H+ liberado em 2026-05-15)
        - ASSET_DIRECTION_BLOCKED       — ex: XPT SHORT bloqueado, USOUSD SHORT bloqueado.
                                          Use formato ASSET_DIRECTION_BLOCKED:{{SYMBOL}}_{{DIR}}.
                                          Esses CAPS na classificação (max OBSERVACAO),
                                          NÃO bloqueiam fluxo. Reportar em Module checklist
                                          notes, não em Hard block triggered.

      REMOVIDOS (nunca disparam empiricamente — Claude já filtra implicitamente):
        - STOP_UNDEFINED                — Claude sempre define stop em texto livre
        - SYMBOL_TF_WRONG               — receiver tem watchlist gate + módulos validam TF

    RSI dependente de módulo (NÃO universal):
    - RSI extremo, NAS TOP/BOTTOM e Market Order Bubbles NÃO são obrigatórios universais.
    - Para módulos validados, pergunte: "O RSI/NAS/Bubbles confirma este tipo específico de setup?"
    - Se hard blocks passarem e checklist obrigatório do módulo passar, SETUP_VALIDO/SETUP_VALIDO_INTRADAY
      pode ser emitido mesmo sem RSI extremo, se o módulo não exigir RSI extremo.
    - Nunca relaxar: R:R, entrada atrasada, MCP confiável, setup perdido, chasing,
      gatilho objetivo, estrutura de preço.

    Operacional V3:
    - Todo SETUP_VALIDO / SETUP_VALIDO_INTRADAY / SETUP_CANDIDATO_FORTE deve ter:
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
    - Demais classificações: Operational signal: NO; D2R required: false.
    - Execução é sempre manual. Sistema NUNCA executa ordens automaticamente.

    Não diga que "a regra do alerta proíbe promover". Diga: "critérios de promoção ainda não preenchidos".


    Campos estruturados obrigatórios em TODA resposta operacional (em linhas próprias):
      Strategy Module: <nome ou NONE>
      Module backtest n: <inteiro ou null>
      Global hard blocks: PASS | FAIL — motivo curto
      Module checklist: PASS | FAIL — motivo curto
      Module checklist notes: <texto livre detalhando itens parciais>
      Module score: A/B/C ou 0
      Operational signal: YES_MANUAL_REVIEW | NO
      D2R required: true | false
      Hard block triggered: <ENUM FIXO — ver tabela abaixo>
      NO_TRADE reason: <ENUM FIXO — preenchido APENAS quando Classificação=NO_TRADE; senão NONE>
      Module checklist failed on: NONE | <item>
      Promotion trigger: NONE | REJECTION_CLOSE | MOMENTUM_CONTINUATION | BREAKOUT_RETEST | SWEEP_REENTRY | CHOCH_BOS | RETEST_HOLD | NAS_SIGNAL_AT_ZONE | DENSE_STRUCTURAL_CONFLUENCE
      Promotion status: NOT_PROMOTED | KEEP_AS_CANDIDATO_FORTE | PROMOTE_TO_SETUP_VALIDO | PROMOTE_TO_SETUP_VALIDO_INTRADAY | DOWNGRADE_TO_OBSERVACAO | NO_TRADE
      Priority: A | B | C
      Trigger: <descrição do gatilho técnico>
      Execution TF: 15 | 30 | 60 | 240 | 720 | D
      Entrada ideal: <preço>
      Preço atual: <preço>
      Entrada atrasada: <ver regra de narração abaixo>
      Entry late distance R: <número decimal SEMPRE — nunca null/none>

    REGRA DE NARRAÇÃO "Entrada atrasada" (atualizado 2026-05-15):
      O campo "Entry late distance R" deve SEMPRE conter um número decimal
      (incluindo 0.0). Nunca usar "null" ou "none" — calcule mesmo que aproximado.

      O campo "Entrada atrasada" usa narração escalonada conforme valor:
        - elr < 0.25:        "Entrada atrasada: NÃO"
                             (uma linha, sem justificativa adicional)
        - 0.25 <= elr < 0.5: "Entrada atrasada: NÃO (borderline, distance R=X.XX)"
                             (alerta que está próximo do limite)
        - elr >= 0.5:        "Entrada atrasada: SIM (distance R=X.XX)"
                             (e marcar hard_block_triggered: ENTRY_LATE_CHASING
                             OU classification: SETUP_ATRASADO_AGUARDAR_RETESTE
                             dependendo do contexto)

      Motivação: auditoria 2026-05-15 mostrou que 89% dos records narravam
      "Entrada atrasada" mesmo quando claramente OK (elr<0.2). Overhead de
      prompt sem ganho. Narração escalonada economiza prompt budget mantendo
      o filtro (threshold 0.5 não muda — regra calibrada D2R n=208).

    ENUM FIXO PARA "Hard block triggered" (e "NO_TRADE reason" quando aplicável):
    Use EXATAMENTE um dos valores abaixo (case-sensitive). Múltiplos podem ser
    combinados com " + " (ex: "RR_BELOW_2 + ENTRY_LATE_CHASING"). NUNCA inventar
    nomes novos — se o caso não bate, use OTHER + comentário em Module checklist notes.

      Hard blocks globais ativos:
        NONE                        — passou todos os hard blocks
        MCP_UNRELIABLE
        DIRECTION_UNDEFINED
        RR_BELOW_2
        ENTRY_LATE_CHASING
        SETUP_LOST_NO_CHASE
        FALLING_KNIFE
        NO_OBJECTIVE_TRIGGER
        ONLY_NOISE_NO_STRUCTURE

      Operational gates (NÃO são hard blocks — usar somente quando essa for
      A ÚNICA razão do downgrade; senão deixar NONE e mencionar em Module
      checklist notes):
        BUBBLE_CLUSTER_GATE_LTF       — apenas em TF 15M/30M
        ASSET_DIRECTION_BLOCKED:{{SYMBOL}}_{{LONG|SHORT}}

      Reserva:
        OTHER                         — só se NENHUM dos acima bate; detalhar em notes

    EXEMPLOS válidos:
      Hard block triggered: NONE
      Hard block triggered: RR_BELOW_2
      Hard block triggered: ENTRY_LATE_CHASING + NO_OBJECTIVE_TRIGGER
      Hard block triggered: ASSET_DIRECTION_BLOCKED:XPTUSD_SHORT
      NO_TRADE reason: RR_BELOW_2 + FALLING_KNIFE

    PASS/FAIL ESTRITAMENTE BINÁRIO:
    - Global hard blocks e Module checklist são PASS ou FAIL. NUNCA "PASS parcial".
    - Para detalhar itens parciais, use Module checklist notes (texto livre).
    - Não coloque estes campos apenas em texto narrativo; escreva cada um em linha própria.


    Módulo DEACTIVATED — ZONE_TOUCH_SMC_CONVERGENT_LONG_INTERIM (criado 2026-05-15, desativado 2026-05-19):
    - Dependia de alert_types da era drawings (monitor_dynamic_bb_zone, monitor_zone,
      monitor_trendline_lta, monitor_dynamic_line, setup_watch_recheck), todos
      curto-circuitados pelo Guard A/B (Fase 0.3, commit 5555e8f).
    - Sample live: 0 trades — input nunca chegou ao prompt pós-migração 2026-05-17.
    - NÃO emitir SETUP_VALIDO sob este nome.
    - Estrutura original preservada em comentário Python fora desta f-string
      (procurar ZONE_TOUCH_SMC_INTERIM_PRESERVED no claude_recheck.py) para
      reaproveitamento futuro (Caminho C com input indicators, não drawings).

    ═══════════════════════════════════════════════════════════════════════════

    Módulo ATIVO — XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED (substitui o antigo 4H_LONG_REJECTION_SWING em 2026-05-12):
    - Backtest 234 trades / 7.4 anos: total net +64.57R @ 0.05R spread, avg +0.276R, PF 1.64, max losing streak 16.
    - Avalie explicitamente se o alerta pertence a este módulo antes de outros XAUUSD swing.
    - Só pode ser considerado quando TODOS os critérios abaixo são verdadeiros:
      Trigger (todos obrigatórios):
        T1. Ativo = PEPPERSTONE:XAUUSD;
        T2. Timeframe = 4H (ou 240);
        T3. Direção = LONG;
        T4. close > swing_high(10) (rompimento da máxima dos últimos 10 candles 4H);
        T5. close > open;
        T6. body_pct >= 0.5 (corpo do candle >= 50% do range total);
        T7. RSI(14) > RSI-based MA.
      Filtros de regime (TODOS obrigatórios — gate de entrada):
        F1. ADX(14) >= 20;
        F2. Close > EMA(200);
        F3. EMA(50) > EMA(200);
        F4. EMA(50) com slope positivo nos últimos 5 bars;
        F5. ATR(14) > ATR_MA(20) (volatilidade expandindo).
      Hard blocks globais não podem falhar (R:R >= 2:1, stop claro, sem chasing, MCP confiável, sem macro red imediato).
    - Stop técnico: low do candle de sinal − 0.5 × ATR(14). Rejeitar se |entry - stop| > 5 × ATR.
    - Target: 4R fixo. BE após +1R. Sem trailing default. Max hold 24 candles 4H.
    - Não classifique este módulo para SHORT (XAUUSD SHORT não tem edge sistemático).
    - Não classifique em 1H/30M/15M.
    - Se todos os critérios passam:
      Strategy Module: XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED
      Module backtest n: 234
      Classificação: SETUP_VALIDO
      Direção: LONG
      Execution TF: 240
      Trigger: MOMENTUM_CONTINUATION
      Promotion status: PROMOTE_TO_SETUP_VALIDO
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
      Priority: A (todos os 5 filtros passam confortavelmente: ADX > 25, ATR > 1.2×MA, etc.) ou B (passam marginalmente).
    - Se 1+ filtro falha mas trigger passa: classificar SETUP_CANDIDATO_FORTE e indicar em Module checklist notes qual filtro falhou.
    - Se trigger falha: NÃO usar este módulo.

    Módulo DEPRECADO — XAUUSD_4H_LONG_REJECTION_SWING:
    - DEACTIVATED em 2026-05-12.
    - Backtest profundo (n=1070, 7.4y) mostrou Total R -59.3R, PF 0.88, avg -0.055R.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO sob este nome.
    - Se o alerta originalmente foi marcado com este módulo, reclassificar como SETUP_CANDIDATO_FORTE (régua clássica) ou avaliar XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED se os critérios dele se aplicam.


    Módulo DESATIVADO — XAUUSD_1H_LONG_DECISIVE_BODY60_HTF:
    - DEACTIVATED em 2026-06-01 após visual auction-theory review (n=25 sample em PEPPERSTONE:XAUUSD 1H, 2024-01 → 2026-05).
    - Backtest mecânico era positivo (n=127, PF 1.57, win 44.9%, avg +0.213R, no_top5 +14.75R, no_top10 +2.50R), mas revisão visual mostrou entradas tardias e em contexto já esticado — muito mecanizado, parecido com XAUUSD_4H_BREAKOUT_CONTINUATION mas pior alinhamento auction-theory.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO_INTRADAY nem SETUP_CANDIDATO_FORTE sob este nome.
    - Se o alerta originalmente foi marcado com este módulo: reclassificar para SETUP_EM_OBSERVACAO/NO_TRADE. Sem substituto LONG 1H ativo para XAUUSD.
    - Pine #05 mantida em arquivo (não usar para novos alertas). Audit CSV e Pine preservados em my-strategy/.
    - Substituiu (e foi substituído por nenhum) o módulo legacy XAUUSD_1H_LONG_REJECTION_EXECUTION (também DEACTIVATED em 2026-05-12).

    Módulo ATIVO — XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL (INTRADAY — default SETUP_CANDIDATO_FORTE):
    - Avalie se o alerta pertence a este módulo: PEPPERSTONE:XAGUSD + TF 1H + LONG decisive breakout + DXY estrutural bearish.
    - Backtest n=69 trades / 2.36y (2024-01 → 2026-05). PF 1.79, win 44.9%, avg +0.234R, max losing streak 4, no_top5 +1.37R. 3 de 3 anos positivos.
    - **Default classification é SETUP_CANDIDATO_FORTE** — NÃO promover automaticamente a SETUP_VALIDO_INTRADAY até validação ao vivo (30+ trades reais, avg_r > +0.15, PF > 1.40, no_top5 ainda positivo).
    - Só pode ser classificado SETUP_CANDIDATO_FORTE quando TODOS os filtros abaixo passarem em candle 1H FECHADO:
      Trigger (5 obrigatórios):
        1. close > swing_high(10);
        2. close > open (candle bullish);
        3. body_pct >= 0.6;
        4. range >= 1.2 × ATR(14);
        5. RSI(14) > RSI-based MA.
      Filtros técnicos de regime (3 obrigatórios):
        6. close > EMA(200) no 1H;
        7. EMA(50) > EMA(200) no 1H;
        8. ATR(14) > ATR_MA(20).
      Filtros HTF (2 obrigatórios):
        9. HTF 1D close > HTF 1D EMA(50);
        10. HTF 4H close > HTF 4H EMA(50).
      Filtro MACRO DXY ESTRUTURAL (1 obrigatório — pull via MCP):
        11. TVC:DXY close < EMA200(DXY) no 4H — USD weakness ESTRUTURAL (não tático).
    - **IMPORTANTE — diferença vs EURUSD:** Para XAG usamos **DXY < EMA200 (estrutural)**, NÃO EMA50 (tático). Audit comprovou que XAG responde a USD weakness de longo prazo.
    - Procedimento MCP para pull DXY estrutural:
      1. Lembrar estado: símbolo atual = PEPPERSTONE:XAGUSD, TF = 60.
      2. chart_set_symbol("TVC:DXY").
      3. chart_set_timeframe("240").
      4. data_get_ohlcv(count=250) — 250 candles 4H de DXY (preciso de pelo menos 200 para EMA200 estável).
      5. Calcular EMA200 dos últimos 200 closes (alpha = 2/201).
      6. Comparar close atual de DXY com EMA200 calculada.
      7. chart_set_symbol("PEPPERSTONE:XAGUSD") — restaurar.
      8. chart_set_timeframe("60") — restaurar.
      9. Reportar no output: "Macro context (DXY): DXY < EMA200 (X.XXX < Y.YYY) ✅" ou downgrade.
    - Política de fallback DXY:
      Caso A — DXY < EMA200 + todos filtros passam → SETUP_CANDIDATO_FORTE (default).
      Caso B — DXY >= EMA200 (não bearish estrutural) → downgrade SETUP_EM_OBSERVACAO; campo "Module checklist failed on: macro_filter_dxy_not_structural_bear".
      Caso C — MCP falhou ao consultar DXY → downgrade SETUP_EM_OBSERVACAO; campo "Module checklist failed on: macro_filter_unverifiable".
    - Stop / gestão padrão:
      Stop = low − 0.5 × ATR(14). Rejeitar se R > 5 × ATR(14).
      Target = 3R fixo. BE após +1R. Trailing desabilitado. Max hold = 20 candles 1H.
    - Output template (Caso A):
      Strategy Module: XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL
      Module backtest n: 69
      Macro context (DXY): DXY < EMA200 (X.XX < Y.YY) ✅
      Trigger: breakout swhi10 + body >= 0.6 + range >= 1.2×ATR + RSI > MA
      Execution TF: 60
      Promotion status: KEEP_AS_CANDIDATO_FORTE
      D2R required: true
      Classificação: SETUP_CANDIDATO_FORTE
      Direção: LONG
    - Frequência baixa (~0.55 trade/sem, ~2.4/mês). Pode haver semanas/meses sem sinal.
    - SHORT em XAGUSD não tem edge confirmado — NÃO classificar SHORT por este módulo.
    - Não existe módulo SWING 4H aprovado para XAG — apenas este intraday 1H.
    - **NÃO confundir o filtro DXY estrutural (EMA200) deste módulo com o filtro DXY tático (EMA50) dos módulos EURUSD.**

    Módulo DESATIVADO — XAUUSD_1H_LONG_REJECTION_EXECUTION:
    - DEACTIVATED em 2026-05-12 após audit profundo.
    - Backtest n=1338, PF 1.04, avg +0.017R, win 17.4%, no_top5 -5.38R — edge fat-tail dependente, inexistente.
    - Forward-test live havia rodado n=21 (insuficiente para validar antes do audit).
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO_INTRADAY nem SETUP_CANDIDATO_FORTE sob este nome.
    - Se o alerta originalmente foi marcado com este módulo: reclassificar para SETUP_EM_OBSERVACAO/NO_TRADE. (Sucessor XAUUSD_1H_LONG_DECISIVE_BODY60_HTF também foi DEACTIVATED em 2026-06-01 por visual review; sem substituto LONG 1H ativo para XAUUSD.)


    Módulo experimental separado — XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
    (RESEARCH / NOT_DEPLOYED — sem pipeline de outcomes ativo desde 2026-04-30):
    - **Status atual:** RESEARCH, NOT_DEPLOYED (catalog 2026-06-01). Forward-test parado em 2026-04-30
      com 0 outcomes mensurados em 31 observações. **Não há pipeline de coleta de outcomes ativo hoje.**
    - **Limite máximo de classificação** enquanto não houver outcomes ativos:
      `INTRADAY_EM_OBSERVACAO` ou `INTRADAY_QUASE_VALIDO 🟡 — REVISÃO HUMANA`.
      **NÃO emitir** `SETUP_VALIDO_INTRADAY` nem `SETUP_CANDIDATO_FORTE_INTRADAY` sob este módulo,
      independentemente da qualidade visual da confluência. Reativação exige decisão de produto sobre
      pipeline de outcomes (entry/stop/target/exit/R-realizado).
    - **Não emitir entrada automática.** Toda mensagem deve carregar a marca explícita
      "NÃO É ENTRADA AUTOMÁTICA — REVISÃO HUMANA".
    - Avalie explicitamente se o alerta pertence ao módulo XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION.
    - Este módulo é separado dos módulos XAUUSD_4H_LONG_REJECTION_SWING (REJECTED legacy) e
      XAUUSD_1H_LONG_REJECTION_EXECUTION (DEACTIVATED legacy).
    - Tese auction-style mantida (BigBeluga zones + multi-TF):
      4H = contexto maior / zonas estruturais (premium/discount HTF);
      1H = zona principal de decisão (BigBeluga supply/demand);
      30M = setup / reação / qualidade de rejeição ou reclaim;
      15M = gatilho de execução / refinamento / invalidação curta.
    - Direções permitidas (apenas para classificação observacional): LONG e SHORT.
    - Gatilhos auction-aware reconhecidos como referência de qualidade (não promovem nada hoje):
      REJECTION_CLOSE; SWEEP_REENTRY; CHOCH_BOS; BREAKOUT_RETEST; RETEST_HOLD; NAS_SIGNAL_AT_ZONE.
    - Dense confluence sozinha NUNCA é setup válido — esta era a regra anterior e segue valendo.
    - Se o preço já se afastou demais da entrada ideal, marque "Entrada atrasada: SIM" e não persiga; aguarde retest.
    - Se este módulo for relevante, use:
      Strategy Module: XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
      Intraday Context: 4H / 1H
      Setup TF: 30M
      Execution TF: 15M
      Classificação: INTRADAY_EM_OBSERVACAO  ou  INTRADAY_QUASE_VALIDO 🟡 — REVISÃO HUMANA
      Priority: A/B/C  (sinalização de qualidade da confluência, NÃO autoriza entrada)
    - Deixe claro na saída: "módulo em pesquisa; sem outcomes ativos; reativação depende de pipeline D2R aprovado".


    Módulo ATIVO — US500_4H_LONG_FAILED_BREAKDOWN_REGIME (substitui US500_4H_LONG_PULLBACK_REJECTION em 2026-05-12):
    - Backtest: 45 trades / 4.4 anos, total net +15.26R @ 0.05R spread, avg +0.339R, PF 1.83, win 37.8%, max losing streak 5.
    - Único módulo US500 com edge confirmado em backtest profundo. TODOS os anos completos positivos (2022 bear +2.70R / 2023 +6.64R / 2024 +7.15R / 2025 +4.13R).
    - Sem top 5: +3.01R (ROBUSTO — não fat-tail).
    - Default classification: SETUP_VALIDO ✅.

    Critérios obrigatórios:
      Trigger (todos):
        T1. Ativo = PEPPERSTONE:US500;
        T2. Timeframe = 4H (ou 240);
        T3. Direção = LONG;
        T4. low < swing_low(20) (varreu mínima dos últimos 20 candles 4H);
        T5. close > swing_low(20) (RECLAIM — fechou de volta acima da mínima varrida);
        T6. close > open (candle bullish);
        T7. body_pct >= 0.5 (recuperação decisiva).
      Filtros de regime (todos obrigatórios):
        F1. Close > EMA(200) no 4H;
        F2. EMA(50) > EMA(200) no 4H;
        F3. ATR(14) > ATR_MA(20) (volatilidade expandindo).
      Hard blocks globais não podem falhar.
    - Stop: low do candle de sinal − 0.5 × ATR(14). Rejeitar se |entry-stop| > 5 × ATR.
    - Target: 2.5R fixo (CONSERVATIVE para US500). BE após +1R. Sem trailing. Max hold 24 candles 4H.
    - NÃO classificar para SHORT. NÃO classificar em outros TFs (1H/30M/15M).
    - Se todos critérios passam:
      Strategy Module: US500_4H_LONG_FAILED_BREAKDOWN_REGIME
      Module backtest n: 45
      Classificação: SETUP_VALIDO  ← default
      Direção: LONG
      Execution TF: 240
      Promotion trigger: SWEEP_REENTRY
      Promotion status: PROMOTE_TO_SETUP_VALIDO
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
      Priority: A (ATR > 1.3×MA + body > 0.7) ou B (default).

    Módulo ATIVO — US500_1H_LONG_BREAKOUT_REGIME_FILTERED (substitui US500_INTRADAY_LONG_PULLBACK_EXECUTION em 2026-05-12):
    - Backtest: 222 trades / 2.3 anos, total net +18.93R @ 0.05R spread, avg +0.085R, PF 1.22, win 40.5%, max losing streak 11.
    - Edge marginal mas POSITIVO. 2024 +22.72R / 2025 -12.32R / 2026 +8.52R (parcial).
    - Default classification: SETUP_CANDIDATO_FORTE (NÃO promove a SETUP_VALIDO_INTRADAY automaticamente).
    - Critérios técnicos obrigatórios:
      Trigger (todos):
        T1. Ativo = PEPPERSTONE:US500;
        T2. Timeframe = 1H (ou 60);
        T3. Direção = LONG;
        T4. close > swing_high(10);
        T5. close > open;
        T6. body_pct >= 0.5;
        T7. RSI(14) > RSI-based MA.
      Filtros regime técnicos:
        F1. Close > EMA(200) no 1H;
        F2. EMA(50) > EMA(200) no 1H;
        F3. EMA(50) slope > 0;
        F4. ATR(14) > ATR_MA(20);
        F5. ADX(14) >= 20.
      ★ Filtros HTF obrigatórios (v1.1):
        H1. HTF 1D close > HTF 1D EMA(50) — diário em bull regime;
        H2. HTF 4H close > HTF 4H EMA(50) — 4H em bull regime.
      Hard blocks globais não podem falhar.
    - Stop: low − 0.5 × ATR. Rejeitar se R > 5 × ATR.
    - Target: 4R fixo. BE +1R. Sem trailing. Max hold 20 candles 1H.
    - NÃO classificar para SHORT. NÃO classificar em outros TFs.
    - Se todos critérios passam:
      Strategy Module: US500_1H_LONG_BREAKOUT_REGIME_FILTERED
      Module backtest n: 222
      Classificação: SETUP_CANDIDATO_FORTE  ← default (NÃO emitir SETUP_VALIDO_INTRADAY)
      Direção: LONG
      Execution TF: 60
      Promotion trigger: MOMENTUM_CONTINUATION
      Promotion status: KEEP_AS_CANDIDATO_FORTE
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
      Priority: A (todos confortáveis + RSI > 60 + ADX > 25) | B (default).

    Módulo DEPRECADO — US500_4H_LONG_PULLBACK_REJECTION:
    - DEACTIVATED em 2026-05-12.
    - Backtest profundo (n=412, 4.4y) mostrou Total Net R -67.65R, PF 0.68, win 12.9%. TODOS os anos negativos.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO sob este nome.
    - Se o alerta originalmente foi marcado com este módulo, reclassificar para US500_4H_LONG_FAILED_BREAKDOWN_REGIME se critérios deste aplicam, ou SETUP_EM_OBSERVACAO/NO_TRADE.

    Módulo DESATIVADO — US500_INTRADAY_LONG_PULLBACK_EXECUTION:
    - DEACTIVATED em 2026-05-12.
    - Backtest profundo (n=943, 1.3y) mostrou Total Net R -105.20R, PF 0.78. Pior módulo do sistema.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO_INTRADAY nem SETUP_CANDIDATO_FORTE sob este nome.
    - Para intraday LONG US500, usar US500_1H_LONG_BREAKOUT_REGIME_FILTERED.
    - SHORT em US500 não tem edge — NÃO automatizar SHORT em nenhum módulo US500.


    Módulo ATIVO — ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED v1.2 (com filtro MACRO ETHBTC, promovido a SETUP_VALIDO em 2026-05-12):
    - Backtest v1.2: 72 trades / 5.4 anos, total net +38.42R @ 0.05R spread, avg +0.534R, PF 2.13, win 36.1%, max losing streak 9.
    - Sem top 5: +13.67R (ROBUSTO). Sem top 10: -6.02R (dramaticamente melhor que v1.0/v1.1).
    - Default classification: SETUP_VALIDO (promovido por atender TODOS os critérios mínimos).
    - Avalie explicitamente se o alerta pertence a este módulo antes de outros ETH swing.

    CRITÉRIOS TÉCNICOS (todos obrigatórios — avaliados no gráfico ETHUSD 4H):
      Trigger:
        T1. Ativo = PEPPERSTONE:ETHUSD;
        T2. Timeframe = 4H (ou 240);
        T3. Direção = LONG;
        T4. close > swing_high(10);
        T5. close > open;
        T6. body_pct >= 0.6 (v1.1: corpo >= 60% do range);
        T7. RSI(14) > RSI-based MA.
      Filtros de regime técnicos:
        F1. ADX(14) >= 25;
        F2. Close > EMA(200);
        F3. EMA(50) > EMA(200);
        F4. EMA(50) slope (5 bars) > 0;
        F5. ATR(14) > ATR_MA(20).
      Hard blocks globais não podem falhar.

    ★ FILTRO MACRO OBRIGATÓRIO v1.2 — ETHBTC > EMA50:
    Antes de classificar SETUP_VALIDO, você DEVE consultar BINANCE:ETHBTC via MCP e verificar se ETH está outperformando BTC.
    Procedimento exato (sequência obrigatória):
      1. Salvar mentalmente: símbolo atual deve voltar a ser PEPPERSTONE:ETHUSD e timeframe 240 ao final.
      2. Chamar chart_set_symbol("BINANCE:ETHBTC")
      3. Chamar chart_set_timeframe("240")
      4. Chamar data_get_ohlcv(count=100) — pegar 100 candles 4H do ETHBTC
      5. Calcular EMA50 manualmente dos 50 últimos closes (alpha = 2/51, ou usando média exponencial de 50 períodos)
      6. Comparar: close_atual_ETHBTC > EMA50_calculada ?
      7. Chamar chart_set_symbol("PEPPERSTONE:ETHUSD") para restaurar
      8. Chamar chart_set_timeframe("240")
      9. Reportar resultado no output (macro_context)

    Política de fallback (CRÍTICA):
    - Se qualquer passo do procedimento ETHBTC falhar (MCP unreliable, symbol not found, OHLCV vazio):
        → macro_context: UNKNOWN
        → Classificação: SETUP_CANDIDATO_FORTE (downgrade conservador, NUNCA SETUP_VALIDO)
        → Module checklist failed on: macro_filter_unverifiable
    - Se ETHBTC close <= EMA50:
        → macro_context: ETHBTC <= EMA50 (X.XXXXX <= Y.YYYYY)
        → Classificação: SETUP_CANDIDATO_FORTE (downgrade por macro)
        → Module checklist failed on: macro_filter_ethbtc_below_ema50
    - Se ETHBTC close > EMA50:
        → macro_context: ETHBTC > EMA50 (X.XXXXX > Y.YYYYY) ✅
        → Classificação: SETUP_VALIDO (promovido — todos os critérios técnicos + macro passaram)

    Stop técnico: low do candle de sinal − 0.5 × ATR(14). Rejeitar se |entry-stop| > 5 × ATR.
    Target: 5R fixo. BE após +1R. Sem trailing. Max hold 30 candles 4H.
    Não classifique este módulo para SHORT (ETH SHORT sem edge).
    Não classifique em 1H/30M/15M (use o módulo específico do TF).

    Output esperado quando todos critérios técnicos + macro passam:
      Strategy Module: ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED
      Module version: v1.2
      Module backtest n: 72
      Macro context: ETHBTC > EMA50 (X.XXXXX > Y.YYYYY) ✅
      Classificação: SETUP_VALIDO  ← v1.2 promovido
      Direção: LONG
      Execution TF: 240
      Promotion trigger: MOMENTUM_CONTINUATION
      Promotion status: PROMOTE_TO_SETUP_VALIDO
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
      Priority: A (todos filtros passam confortavelmente + ADX > 30 + RSI > 60) | B (default).

    Output esperado quando trigger/regime técnicos passam mas macro NÃO (caso B ou C):
      Strategy Module: ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED
      Module version: v1.2
      Macro context: ETHBTC <= EMA50 (...) ⚠️  ou  UNKNOWN (MCP failed)
      Classificação: SETUP_CANDIDATO_FORTE  ← downgrade
      Promotion status: KEEP_AS_CANDIDATO_FORTE
      Module checklist failed on: macro_filter_ethbtc_below_ema50  ou  macro_filter_unverifiable

    Output esperado quando trigger/regime técnicos falham: SETUP_EM_OBSERVACAO ou NO_TRADE conforme o que falha (NÃO USAR este módulo).

    Módulo ATIVO — ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME (novo intraday em 2026-05-12):
    - Backtest: 96 trades / 1.4 anos, total net +23.19R @ 0.05R spread, avg +0.242R, PF 1.68, max losing streak 9, win rate 33.3%.
    - QUALIDADE SUPERIOR aos outros candidatos ETH intraday: sem top 5 ainda +8.44R (positivo).
    - Mas sample 1.4y só: começa como SETUP_CANDIDATO_FORTE. Promover a SETUP_VALIDO_INTRADAY APENAS após 30+ trades ao vivo com avg_r > +0.15R, PF > 1.40, sem dependência de top 5.
    - Tipo: PULLBACK to EMA50 (não breakout). Espera correção e entra no retest da EMA50 em regime trending.
    - Critérios obrigatórios:
      Trigger (todos):
        T1. Ativo = PEPPERSTONE:ETHUSD;
        T2. Timeframe = 1H (ou 60);
        T3. Direção = LONG;
        T4. low <= EMA(50) (pullback tocou/atravessou EMA50);
        T5. close > EMA(50) (fechamento recuperou para cima da EMA50);
        T6. close > open (candle bullish);
        T7. body_pct >= 0.4 (corpo >= 40% do range);
        T8. RSI(14) > RSI-based MA.
      Filtros de regime (TODOS obrigatórios):
        F1. Close > EMA(200) no 1H;
        F2. EMA(50) > EMA(200) no 1H;
        F3. HTF 1D close > HTF 1D EMA(50) — gate HTF crítico.
      Hard blocks globais não podem falhar.
    - Stop: low do candle de sinal − 0.5 × ATR(14). Rejeitar se R > 5 × ATR.
    - Target: 3R fixo. BE após +1R. Sem trailing. Max hold 20 candles 1H.
    - Não classifique este módulo para SHORT.
    - Não classifique em 4H/30M/15M ou outros TFs.
    - Se todos os critérios passam:
      Strategy Module: ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME
      Module backtest n: 96
      Classificação: SETUP_CANDIDATO_FORTE  ← default; NÃO emitir SETUP_VALIDO_INTRADAY automaticamente até validação ao vivo
      Direção: LONG
      Execution TF: 60
      Promotion trigger: RETEST_HOLD
      Promotion status: KEEP_AS_CANDIDATO_FORTE
      Operational signal: YES_MANUAL_REVIEW
      D2R required: true
      Priority: A (pullback limpo + RSI > 55 + HTF strongly bullish) | B (default).

    Módulo DEPRECADO — ETHUSD_4H_LONG_BREAKOUT_CONTINUATION:
    - DEPRECATED em 2026-05-12.
    - Backtest profundo (n=613, 5.4y) mostrou Total Net R -35.68R, PF 0.89, avg -0.058R.
    - Filtro "RSI >= 52" não exclui losses (comprovado).
    - Filtro runner 8R Priority A piora resultado (comprovado).
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO sob este nome.
    - Se o alerta originalmente foi marcado com este módulo, reclassificar para ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED se os critérios dele se aplicam, ou para SETUP_CANDIDATO_FORTE/SETUP_EM_OBSERVACAO conforme o caso.

    Módulo DESATIVADO — ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION:
    - DEACTIVATED em 2026-05-12.
    - Backtest profundo (n=2061 combined, 1.4y) mostrou Total Net R -265.20R combinado, PF 0.72.
    - LONG: -170R / PF 0.67. SHORT: -95R / PF 0.78. AMBAS DIREÇÕES SEM EDGE.
    - Filtro "1+ confirmação adicional (NAS/bubble/divergência/RSI reclaim/retest hold/CHoCH-BOS)" é IRRELEVANTE — resultado idêntico com ou sem.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO_INTRADAY nem SETUP_CANDIDATO_FORTE_INTRADAY sob este nome.
    - SHORT em ETHUSD não tem edge sistemático em nenhum TF testado — NÃO automatizar SHORT em ETH em nenhum módulo.
    - Se o alerta originalmente foi para este módulo: reclassificar para ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME se direção LONG e critérios 1H aplicam, ou para SETUP_EM_OBSERVACAO/NO_TRADE caso contrário.


    Módulo ATIVO — EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY (SWING — default SETUP_VALIDO):
    - Avalie se o alerta pertence a este módulo: PEPPERSTONE:EURUSD + TF 4H + LONG breakout.
    - Backtest n=47 trades / 7.4y (2019-01 → 2026-05). PF 2.03, win 42.6%, avg +0.284R, max losing streak 4. Sem top 5 ainda positivo (+1.10R). 6 de 8 anos positivos.
    - Só pode ser classificado SETUP_VALIDO quando TODOS os filtros abaixo passarem em candle 4H FECHADO:
      Trigger (5 obrigatórios):
        1. close > swing_high(10) — rompimento da máxima dos últimos 10 candles 4H;
        2. close > open (candle bullish);
        3. body_pct >= 0.6 (corpo >= 60% do range, decisivo);
        4. range >= 1.2 × ATR(14) (barra de alta amplitude);
        5. RSI(14) > RSI-based MA (momentum alinhado).
      Filtros técnicos de regime (4 obrigatórios):
        6. close > EMA(200) no 4H;
        7. EMA(50) > EMA(200) no 4H (golden cross);
        8. ATR(14) > ATR_MA(20) (volatilidade expandindo);
        9. ADX(14) >= 25 (força direcional confirmada).
      Filtros HTF (2 obrigatórios):
        10. HTF 1D close > HTF 1D EMA(50);
        11. HTF 12H close > HTF 12H EMA(50).
      Filtro MACRO DXY (1 obrigatório — pull via MCP):
        12. TVC:DXY close < EMA50(DXY) no 4H (DXY em bearish regime).
    - Procedimento MCP para pull DXY (executar antes de classificar):
      1. Lembrar estado: símbolo atual = PEPPERSTONE:EURUSD, TF = 240.
      2. chart_set_symbol("TVC:DXY").
      3. chart_set_timeframe("240").
      4. data_get_ohlcv(count=100) — 100 candles 4H de DXY.
      5. Calcular EMA50 dos últimos 50 closes (alpha = 2/51).
      6. Comparar close atual de DXY com EMA50 calculada.
      7. chart_set_symbol("PEPPERSTONE:EURUSD") — restaurar.
      8. chart_set_timeframe("240") — restaurar.
      9. Reportar no output: "Macro context (DXY): DXY < EMA50 (X.XXX < Y.YYY) ✅" ou downgrade conforme casos B/C.
    - Política de fallback DXY:
      Caso A — DXY close < EMA50 + todos filtros passam → Classificação: SETUP_VALIDO.
      Caso B — DXY close >= EMA50 (não bearish) → downgrade para SETUP_CANDIDATO_FORTE; campo "Module checklist failed on: macro_filter_dxy_not_bearish".
      Caso C — MCP falhou em ler TVC:DXY (símbolo não acessível, OHLCV vazio) → downgrade para SETUP_CANDIDATO_FORTE; campo "Module checklist failed on: macro_filter_unverifiable".
    - Stop / gestão padrão:
      Stop = low_signal_bar − 0.5 × ATR(14). Rejeitar se R > 5 × ATR(14).
      Target = 2.5R fixo. BE após +1R. Trailing desabilitado. Max hold = 24 candles 4H (4 dias).
    - Output template (Caso A):
      Strategy Module: EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY
      Module backtest n: 47
      Macro context (DXY): DXY < EMA50 (X.XXX < Y.YYY) ✅
      Trigger: breakout swhi10 + body >= 0.6 + range >= 1.2 ATR + RSI > MA
      Execution TF: 240
      Promotion status: PROMOTE_TO_SETUP_VALIDO
      D2R required: true
      Classificação: SETUP_VALIDO
      Direção: LONG
    - Frequência muito baixa (~0.59 trade/mês). Pode ter meses sem sinal — não forçar.
    - NÃO emitir SETUP_VALIDO sem confirmação DXY bearish via MCP.
    - SHORT em EURUSD não tem edge confirmado — NÃO classificar SHORT por este módulo.

    Módulo ATIVO — EURUSD_1H_LONG_DECISIVE_HTF1D_DXY (INTRADAY — default SETUP_CANDIDATO_FORTE):
    - Avalie se o alerta pertence a este módulo: PEPPERSTONE:EURUSD + TF 1H + LONG decisive breakout.
    - Backtest n=73 trades / 2.4y (2024-01 → 2026-05). PF 1.46, win 42.5%, avg +0.174R, max losing streak 8. Todos os 3 anos parciais positivos.
    - **Default classification é SETUP_CANDIDATO_FORTE** — NÃO promover automaticamente a SETUP_VALIDO_INTRADAY até validação ao vivo (30+ trades reais, avg_r > +0.15, PF > 1.40).
    - Só pode ser classificado SETUP_CANDIDATO_FORTE quando TODOS os filtros abaixo passarem em candle 1H FECHADO:
      Trigger (5 obrigatórios — DECISIVE breakout):
        1. close > swing_high(10) — rompimento da máxima dos últimos 10 candles 1H;
        2. close > open (candle bullish);
        3. body_pct >= 0.7 (DECISIVO, não pavio);
        4. range >= 1.5 × ATR(14) (barra de alta amplitude);
        5. RSI(14) > RSI-based MA (momentum alinhado).
      Filtros técnicos de regime (3 obrigatórios):
        6. close > EMA(200) no 1H;
        7. EMA(50) > EMA(200) no 1H;
        8. ATR(14) > ATR_MA(20) (volatilidade expandindo).
      Filtro HTF (1 obrigatório):
        9. HTF 1D close > HTF 1D EMA(50).
      Filtro MACRO DXY (1 obrigatório — pull via MCP, mesmo procedimento do módulo 4H):
        10. TVC:DXY close < EMA50(DXY) no 4H.
    - Procedimento MCP DXY: idêntico ao módulo EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY acima.
    - Política de fallback DXY:
      Caso A — DXY confirmado bearish + todos filtros passam → SETUP_CANDIDATO_FORTE (default).
      Caso B — DXY não bearish OU MCP falhou → SETUP_EM_OBSERVACAO (downgrade adicional). Campo "Module checklist failed on: macro_filter_dxy_not_bearish" ou "macro_filter_unverifiable".
    - Stop / gestão padrão:
      Stop = low − 0.5 × ATR(14). Target = 3R fixo. BE após +1R. Trailing desabilitado. Max hold = 20 candles 1H.
    - Output template (Caso A):
      Strategy Module: EURUSD_1H_LONG_DECISIVE_HTF1D_DXY
      Module backtest n: 73
      Macro context (DXY): DXY < EMA50 (X.XX < Y.YY) ✅
      Trigger: breakout swhi10 + body >= 0.7 + range >= 1.5×ATR + RSI > MA
      Execution TF: 60
      Promotion status: KEEP_AS_CANDIDATO_FORTE
      D2R required: true
      Classificação: SETUP_CANDIDATO_FORTE
      Direção: LONG
    - Frequência intraday baixa (~0.66 trade/sem). Filtros restritivos por design (qualidade > frequência).
    - SHORT em EURUSD não tem edge — NÃO classificar SHORT.

    Módulo DESATIVADO — EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION:
    - DEACTIVATED em 2026-05-12 após audit V2.
    - Baseline backtest perdia -104R em walk-forward profundo. Sem edge sistemático em 30M EURUSD.
    - NÃO usar como Strategy Module. NÃO emitir SETUP_VALIDO_INTRADAY nem SETUP_CANDIDATO_FORTE sob este nome.
    - Substituído operacionalmente por EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY (swing) e EURUSD_1H_LONG_DECISIVE_HTF1D_DXY (intraday).
    - Se o alerta originalmente foi marcado com este módulo: reclassificar para um dos 2 novos módulos ativos se os critérios aplicam, ou para SETUP_EM_OBSERVACAO/NO_TRADE caso contrário.

    Tarefa:
    1. Use o TradingView MCP para fazer health check.
    2. Se necessário, mude para o ativo e timeframe do alerta.
    3. Reavalie o gráfico conforme strategy_rules.json.
    4. Responda no formato abaixo.

    Formato obrigatório:

    ALERTA REAVALIADO
    Ativo:
    Timeframe:
    Alert type:
    Health:
    Strategy Module:
    Intraday Context:
    Setup TF:
    Execution TF:
    Priority:
    Classificação:
    Direção:
    Resumo:
    Confluências:
    Bloqueio principal:
    R:R estimado:
    Stop técnico:
    Entrada ideal:
    Preço atual:
    Entrada atrasada:
    Gatilho faltante:
    Candidato forte:
    Motivo candidato forte:
    Promotion trigger:
    Promotion status:
    Ação tomada:
    Próxima ação:
    """).strip()


def main():
    if len(sys.argv) > 1:
        try:
            alert = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            raise SystemExit(f"Erro: argumento não é JSON válido: {e}")
    else:
        alert = DEFAULT_ALERT

    started = datetime.now().isoformat()
    log_file = LOG_DIR / "claude_recheck_last.json"

    if is_test_alert(alert):
        output = build_test_response(alert)
        data = {
            "started_at": started,
            "ok": True,
            "mode": "test_alert_short_circuit",
            "stdout": output,
            "stderr": "",
            "alert": alert
        }
        log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(output)
        return

    if is_deprecated_alert(alert):
        output = build_deprecated_short_circuit_response(alert)
        data = {
            "started_at": started,
            "ok": True,
            "mode": "deprecated_alert_short_circuit",
            "alert_type": alert.get("alert_type", ""),
            "stdout": output,
            "stderr": "",
            "alert": alert,
        }
        log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(output)
        return

    prompt = build_prompt(alert)

    cmd = [
        CLAUDE_CLI,
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]

    chart_lock_fd = None
    chart_lock_wait_s = None
    chart_lock_error = None
    try:
        chart_lock_fd, chart_lock_wait_s = acquire_chart_lock()
    except TimeoutError as e:
        chart_lock_error = str(e)

    try:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                text=True,
                capture_output=True,
                timeout=360
            )
        except subprocess.TimeoutExpired:
            output = "ERRO: Claude Code headless excedeu timeout de 360s."
            data = {
                "started_at": started,
                "ok": False,
                "error": "timeout",
                "output": output,
                "alert": alert,
                "chart_lock_wait_s": chart_lock_wait_s,
                "chart_lock_error": chart_lock_error,
            }
            log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            print(output)
            sys.exit(1)
    finally:
        release_chart_lock(chart_lock_fd)

    output = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    data = {
        "started_at": started,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": output,
        "stderr": stderr,
        "alert": alert,
        "chart_lock_wait_s": chart_lock_wait_s,
        "chart_lock_error": chart_lock_error,
    }
    log_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    if result.returncode != 0:
        print("ERRO: Claude Code retornou falha.")
        if stderr:
            print(stderr)
        if output:
            print(output)
        sys.exit(result.returncode)

    print(output)


if __name__ == "__main__":
    main()
