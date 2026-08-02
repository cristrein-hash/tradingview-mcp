#!/usr/bin/env python3
"""PDF para o Leonardo — v2 (Cris 2026-08-02): PRIMEIRO o que o sistema live leu SOZINHO (funil E1×E2 +
os 8 sinais emitidos com outcomes, DA=CLEAN), DEPOIS os trades ideais do Cris e a análise da semana.
Números verificados: week_eval_20260802_e1xe2_full.py + week_eval_20260802_ideal_trades.py + DA.
Saída: ~/Desktop/Resumo_Semana_XAU_27-31Jul_para_Leonardo.pdf"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT = str(Path.home() / "Desktop" / "Resumo_Semana_XAU_27-31Jul_para_Leonardo.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#0f3460"))
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.8, leading=13.5, spaceAfter=4)
SM = ParagraphStyle("SM", parent=P, fontSize=8.8, textColor=colors.HexColor("#555555"))

CELL = ParagraphStyle("CELL", parent=ss["BodyText"], fontSize=8.2, leading=10.5, spaceAfter=0)
CELLH = ParagraphStyle("CELLH", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")


def tbl(data, widths):
    # células como Paragraph => quebra de linha automática (strings simples sobrepunham texto longo)
    wrapped = []
    for ri, row in enumerate(data):
        wrapped.append([Paragraph(str(c), CELLH if ri == 0 else CELL) for c in row])
    t = Table(wrapped, colWidths=widths)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460"))]))
    return t

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15 * mm, bottomMargin=13 * mm,
                        leftMargin=15 * mm, rightMargin=15 * mm)
E = []
E.append(Paragraph("XAUUSD — Resumo da Semana 27–31 Julho 2026", H1))
E.append(Paragraph("Parte A: o que o sistema leu e sinalizou SOZINHO · Parte B: os trades ideais (benchmark) · "
                   "Parte C: análise da semana — números auditados (Devil's Advocate: CLEAN)", SM))
E.append(Spacer(1, 5))

E.append(Paragraph("PARTE A — O sistema autónomo: o que o live leu sozinho", H2))
E.append(Paragraph(
    "O funil tem duas camadas: o <b>E1 (gerador)</b> deteta situações mecânicas em estrutura real (rejeição de "
    "zona, sweep, quebra, íman HTF) e produz candidatos; o <b>E2 (reader contextual, IA)</b> lê cada candidato "
    "contra o quadro completo (regime, perna, leilão, zonas, macro) e só <b>emite</b> o que converge. "
    "Nada executa sozinho — os sinais emitidos vão ao Telegram para decisão humana.", P))
E.append(Spacer(1, 3))
E.append(Paragraph("A1. O funil da semana em números", H2))
E.append(tbl([
    ["Camada", "Volume", "Detalhe"],
    ["E1 gerou", "250 candidatos únicos", "122 magnet_reject · 63 zone_reject · 63 sweep_reclaim · 152 SHORT / 98 LONG"],
    ["E2 leu", "58 candidatos", "30 SHORT · 28 LONG (os restantes morreram em dedup/anti-spam antes do read)"],
    ["E2 recusou", "40 pelo read + 10 por higiene", "Razões dominantes: 'apanhar faca / contra a perna' (27×) · 'leilão contra/vazio' (12×)"],
    ["E2 EMITIU", "8 sinais (todos SHORT)", "0 longs emitidos — o reader recusou o lado comprador a semana toda"],
], [30 * mm, 44 * mm, 94 * mm]))
E.append(Spacer(1, 4))
E.append(Paragraph("A2. Os 8 sinais emitidos — cada um, com resultado (SL-first, auditado)", H2))
E.append(tbl([
    ["Quando (Lisboa)", "Sinal", "Entry", "SL", "Alvo", "Conv.", "Resultado"],
    ["Seg 27 20:05", "SHORT íman 4H", "4077,88", "4090,99", "4048,33", "42", "WIN +2,2R"],
    ["Seg 27 21:46", "SHORT rejeição zona 4H", "4077,00", "4090,85", "4048,33", "60", "WIN +2,1R"],
    ["Ter 28 00:46", "SHORT rejeição zona 4H", "4071,86", "4081,58", "4048,33", "50", "WIN +2,4R"],
    ["Qua 29 15:46", "SHORT íman 4H", "4001,32", "4028,69", "3919,20", "60", "LOSS −1R (stopado antes do FOMC)"],
    ["Qui 30 04:00", "SHORT rejeição zona 4H", "4063,88", "4091,37", "3981,42", "50", "LOSS −1R"],
    ["Qui 30 05:27", "SHORT rejeição zona 1H", "4053,51", "4072,49", "4010,16", "50", "LOSS −1R"],
    ["Qui 30 10:01", "SHORT rejeição zona 15M", "4061,26", "4072,69", "4036,66", "40", "LOSS −1R"],
    ["Sex 31 12:45", "SHORT pós-notícia 15M", "4052,25", "4058,98", "4036,66", "72", "LOSS −1R"],
], [26 * mm, 40 * mm, 17 * mm, 17 * mm, 17 * mm, 12 * mm, 39 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "<b>Painel autónomo: N=8 · WR 38% (3W/5L) · +1,7R · avgR +0,22R · pior sequência 5 losses.</b> "
    "Leitura honesta: (1) os 3 wins vieram da perna bear de seg-ter — o sistema leu bem o lado certo no início "
    "da semana; (2) os 5 losses concentram-se de 4ª a 6ª, quando o mercado virou range pós-FOMC e os shorts de "
    "continuação deixaram de pagar — o reader manteve o viés vendedor tempo demais; (3) recusar TODOS os longs "
    "protegeu de ~9 facas do motor mecânico de teste (ver Parte C), mas também recusou o único repique vencedor. "
    "Caveats do auditor: amostra pequena (8), fill idealizado (alert-only), e o lucro assenta nos 3 wins de seg-ter.", P))

E.append(Paragraph("PARTE B — Os 6 trades ideais (benchmark do Cris, plotados no chart)", H2))
E.append(Paragraph(
    "Depois do fecho da semana, o Cris plotou no chart os 6 melhores trades possíveis (com hindsight — é o teto, "
    "não o alcançável). Servem para medir quanto do potencial o sistema viu:", P))
E.append(tbl([
    ["Dir", "Entry", "SL", "TP", "RxR", "Quando", "O sistema viu?"],
    ["SHORT", "4106,06", "4118,36", "4028,47", "6,3R", "Seg 01:00", "Não — classe fade-de-topo não existia (→R10)"],
    ["SHORT", "4089,57", "4101,86", "4038,69", "4,1R", "Seg 13:00", "E1 gerou; E2 ainda não estava ligado (go-live 2ª à noite)"],
    ["SHORT", "4088,35", "4104,81", "4018,04", "4,3R", "Seg 09:00", "Idem — timing do go-live"],
    ["SHORT", "4068,68", "4078,69", "4043,75", "2,5R", "Ter 01:00", "SIM — emitido às 00:46 conv 50 (o 3º win da Parte A)"],
    ["LONG", "4011,48", "3994,50", "4110,47", "5,8R", "Ter 15:15", "Não — sem gatilho de compra NO bloco (→R9)"],
    ["LONG", "4067,76", "4057,74", "4107,88", "4,0R", "Qua 19:30", "Não — veto de evento (por design; foi o trade humano +1.600$)"],
], [13 * mm, 17 * mm, 17 * mm, 17 * mm, 12 * mm, 20 * mm, 72 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "Teto teórico +27R. O padrão dos 6: entrada no extremo estrutural (topo de supply / fundo de order block), "
    "stop cirúrgico 10-17 pts atrás da estrutura, alvo na estrutura oposta. O sistema capturou integralmente 1 "
    "dos 6 (a quebra de continuação) — e os dois gaps reais viraram features na mesma semana.", P))

E.append(Paragraph("PARTE C — Análise da semana e o que mudou", H2))
E.append(Paragraph(
    "<b>Mercado:</b> semana de FOMC. Queda 4110→4016 antes do evento; Powell dovish disparou +59 pts até 4116 "
    "<b>totalmente devolvidos em ~40 min</b> (chicote clássico); quinta re-testou o topo 4110-4117 e sexta caiu "
    "a 4021, fechando em 4046 — range macro <b>3995↔4116</b>, regime BEAR. GDP fraco (1,5%) + PCE a arrefecer "
    "(3,3%) + guerra Irão-EUA + petróleo forte.", P))
E.append(Paragraph(
    "<b>Experiência 'Retoma' encerrada:</b> um gatilho mecânico de compra de fundos correu a semana em teste "
    "seco: 1W/9L, −6R, 8 losses seguidos → reprovado e arquivado. A lição que fica: <b>gatilho mecânico sem "
    "leitura de contexto compra facas em bear</b> — enquanto o reader contextual recusava exatamente esses "
    "repiques. É a validação, com dados forward, da arquitetura em duas camadas.", P))
E.append(Paragraph("<b>O que foi construído esta semana (já em produção, tudo alert-only):</b>", P))
E.append(tbl([
    ["Feature", "O que faz", "Prova"],
    ["R8 bos_continuation", "Sinaliza a 2ª quebra estrutural (a confirmação; o 1º CHoCH é muitas vezes manipulação)", "Recall do short perdido de 5ª 01:15 (3R)"],
    ["R9 ob_touch_hold", "Compra/vende NO order block 4H/1D (toque+hold), SL atrás da borda + descritores de qualidade (perna de chegada, nº do toque, absorção)", "Recall do LONG monstro de 3ª (entry 4022, SL 3993)"],
    ["R10 top_fade", "Vende exaustão no topo: raid profundo + ≥2 rejeições + guarda anti-evento", "Recall do topo de 2ª (4097); ZERO no spike FOMC"],
    ["Polaridade bubbles", "Venda absorvida em demanda = compra (context-dependente), corrigida nos 2 caminhos", "Prova viva: long em demanda já não é bloqueado"],
    ["Prioridade OB", "As zonas do reader agora são order blocks reais", "Supply falsa 4061 → OB real 4101-4116"],
], [30 * mm, 84 * mm, 54 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "<b>As 3 lições:</b> (1) Veto de evento nos dois sentidos — nem operar antes do binário, nem tratar o spike "
    "como conclusão. (2) Trailing em momentum de evento — o trade real do FOMC fez +1.600$ (conta em 100.350) "
    "mas valia ~3.000$ com trailing no discurso. (3) Custo da causalidade — o sistema entra na confirmação "
    "(pior preço que o wick ideal); o benchmark serve para medir esse custo, não para o negar.", P))
E.append(Spacer(1, 6))
E.append(Paragraph("Suporte: WEEK_EVAL_20260727_31_REPORT.md · scripts week_eval_20260802_*.py · auditoria "
                   "Devil's Advocate CLEAN (outcomes dos 8 sinais verificados independentemente contra o preço).", SM))
doc.build(E)
print(f"PDF gerado: {OUT}")
