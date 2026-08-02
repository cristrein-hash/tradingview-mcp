#!/usr/bin/env python3
"""PDF para o Leonardo — resumo da análise dos trades sinalizados na semana 27-31/07/2026.
Números da avaliação verificada (scripts week_eval_20260802_* + DA CLEAN-WITH-CAVEATS).
Saída: ~/Desktop/Resumo_Semana_XAU_27-31Jul_para_Leonardo.pdf"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)

OUT = str(Path.home() / "Desktop" / "Resumo_Semana_XAU_27-31Jul_para_Leonardo.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#0f3460"))
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.8, leading=13.5, spaceAfter=4)
SM = ParagraphStyle("SM", parent=P, fontSize=8.8, textColor=colors.HexColor("#555555"))

def tbl(data, widths, header=True):
    t = Table(data, colWidths=widths)
    style = [("FONTSIZE", (0, 0), (-1, -1), 8.6), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=16 * mm, bottomMargin=14 * mm,
                        leftMargin=16 * mm, rightMargin=16 * mm)
E = []
E.append(Paragraph("XAUUSD — Resumo da Semana 27–31 Julho 2026", H1))
E.append(Paragraph("Sinais do sistema, trades ideais e o que mudou · preparado por Cris + Claude (avaliação verificada de 02/08)", SM))
E.append(Spacer(1, 6))

E.append(Paragraph("1. O contexto da semana", H2))
E.append(Paragraph(
    "Semana de FOMC. O ouro caiu de ~4110 para ~4016 antes do evento (segunda→terça), coilou, e na quarta o "
    "Powell dovish disparou um spike de +59 pts até 4116 que foi <b>totalmente devolvido em ~40 minutos</b> "
    "(o clássico chicote de evento). Quinta voltou ao topo 4110-4117 (a nossa venda excelente) e sexta caiu "
    "até 4021, fechando a semana em <b>4046</b> — praticamente onde estava antes do FOMC. Estrutura: "
    "<b>range macro 3995↔4116</b>, regime BEAR nos detetores. GDP fraco (1,5% vs 2,1%) + Core PCE a arrefecer "
    "(3,3%) + guerra Irão-EUA + petróleo forte = cabo-de-guerra entre dólar e refúgio.", P))

E.append(Paragraph("2. Os 6 trades ideais da semana (benchmark do Cris, plotados no chart)", H2))
E.append(tbl([
    ["Dir", "Entry", "SL", "TP", "R (pts)", "RxR", "Quando"],
    ["SHORT", "4106,06", "4118,36", "4028,47", "12,3", "6,3R", "Seg 01:00 (topo pós-fim-de-semana)"],
    ["SHORT", "4089,57", "4101,86", "4038,69", "12,3", "4,1R", "Seg 13:00 (retest da supply)"],
    ["SHORT", "4088,35", "4104,81", "4018,04", "16,5", "4,3R", "Seg 09:00 (retest, alvo fundo)"],
    ["SHORT", "4068,68", "4078,69", "4043,75", "10,0", "2,5R", "Ter 01:00 (quebra de continuação)"],
    ["LONG", "4011,48", "3994,50", "4110,47", "17,0", "5,8R", "Ter 15:15 (compra NO order block 4H)"],
    ["LONG", "4067,76", "4057,74", "4107,88", "10,0", "4,0R", "Qua 19:30 (momentum do Powell)"],
], [14 * mm, 18 * mm, 18 * mm, 18 * mm, 15 * mm, 13 * mm, 68 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "<b>Teto teórico: +27R (WR 100% por construção — é hindsight, ninguém apanha os 6).</b> O padrão comum: "
    "entrada no extremo estrutural (topo de supply / fundo de order block), stop cirúrgico de 10-17 pts atrás "
    "da estrutura, alvo na estrutura oposta. Quatro classes de trade: fade de supply, quebra de continuação, "
    "acumulação no OB, momentum de evento.", P))

E.append(Paragraph("3. O que o sistema sinalizou (e porquê falhou o resto)", H2))
E.append(tbl([
    ["Trade ideal", "O que o sistema fez", "Causa"],
    ["SHORT 4068 (2,5R)", "✅ SINALIZADO — E2 surfou conv 50 às 00:46", "A classe de continuação que o sistema domina"],
    ["SHORT 4089 + 4088 (8,4R)", "Gerados no E1 (14 e 16 candidatos), sem leitura", "E2 só ligou ao Telegram 2ª à noite (go-live a meio da perna)"],
    ["SHORT 4106 (6,3R)", "Recusado (frame ainda bull no topo)", "Classe fade-de-topo não existia → construída (R10)"],
    ["LONG 4011 (5,8R)", "Zero candidatos no toque do bloco", "Lacuna real de geração → construída (R9)"],
    ["LONG 4067 FOMC (4,0R)", "Recusado por veto de evento", "Fora de scope por design — trade humano (foi o real de +1.600$)"],
], [38 * mm, 68 * mm, 62 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "Do teto de +27R o sistema surfou +2,5R — mas a decomposição importa: metade do miss foi timing de "
    "go-live (resolvido sozinho) e evento (por design, humano). Os dois gaps <i>reais</i> viraram features "
    "novas na mesma semana.", P))

E.append(Paragraph("4. A experiência 'Retoma v1' — encerrada com veredito", H2))
E.append(Paragraph(
    "A Retoma era um gatilho <b>mecânico</b> de compra em fundo fresco durante bear (comprava o 1º reclaim "
    "do fundo). Correu a semana em dry como experiência de contraste contra o reader contextual. "
    "<b>Painel final: N=10 resolvidos · 1W/9L (WR 10%) · −6,0R · pior sequência 8 losses seguidos → "
    "reprovada formalmente</b> (a baliza pré-registada era ≤5). No mesmo período, o reader E2 recusou todos "
    "os longs que leu nessa zona (e também o único vencedor — custo de +3R do conservadorismo) e surfou 8 "
    "shorts, o lado que pagou. <b>Lição central: gatilho mecânico sem leitura de contexto compra facas em "
    "bear; a leitura de convergência (regime + fluxo + estrutura) é o que separa o trade da esperança.</b> "
    "A ideia boa que a Retoma continha (comprar no bloco) foi herdada pela feature R9, na versão estrutural correta.", P))

E.append(Paragraph("5. O que mudou no sistema (construído esta semana, já em produção)", H2))
E.append(tbl([
    ["Feature", "O que faz", "Prova"],
    ["R8 bos_continuation", "Sinaliza a 2ª quebra estrutural (a confirmação; o 1º CHoCH é muitas vezes manipulação)", "Recall do short perdido de 5ª feira 01:15 (3R)"],
    ["R9 ob_touch_hold", "Compra/vende NO order block 4H/1D (toque+hold), SL atrás da borda do bloco", "Recall do LONG monstro de 3ª (entry 4022, SL 3993)"],
    ["R10 top_fade", "Vende exaustão no topo: raid profundo + ≥2 rejeições + guarda anti-evento", "Recall do topo de 2ª (4097); ZERO no spike FOMC"],
    ["Polaridade bubbles", "Venda absorvida em demanda = compra (context-dependente) — corrigida nos 2 caminhos", "Prova viva: long em demanda já não é bloqueado"],
    ["Prioridade OB", "As zonas do reader agora são order blocks reais, não ranges de outros indicadores", "Supply 4061 (falsa) → 4101-4116 (OB real)"],
], [30 * mm, 82 * mm, 56 * mm]))
E.append(Spacer(1, 3))
E.append(Paragraph(
    "Tudo <b>alert-only</b>: os gatilhos geram candidatos, o reader contextual (IA) julga cada um contra o "
    "quadro completo (regime, perna, leilão, zonas, macro), e nada executa sozinho — a decisão final é sempre humana.", P))

E.append(Paragraph("6. As 3 lições da semana", H2))
E.append(Paragraph(
    "<b>1. Veto de evento nos dois sentidos.</b> Nem operar 3h antes de um evento binário, nem tratar o spike "
    "como conclusão — o FOMC devolveu +59 pts em 40 min. O que salvou foi o processo (o reader não validou "
    "nenhum long na euforia).<br/>"
    "<b>2. Trailing em momentum de evento.</b> O trade real do FOMC fez +1.600$ (conta positivada em 100.350) "
    "mas teria sido ~3.000$ com trailing durante o discurso do Powell — gestão de saída é o próximo músculo.<br/>"
    "<b>3. Causal vs ideal.</b> O sistema entra no fecho da confirmação (pior preço que o wick ideal) — é o "
    "custo de não adivinhar. O benchmark dos trades ideais serve para medir esse custo, não para o negar.", P))

E.append(Spacer(1, 8))
E.append(Paragraph("Documentos de suporte: WEEK_EVAL_20260727_31_REPORT.md (relatório completo com auditoria "
                   "Devil's Advocate) · scripts reprodutíveis week_eval_20260802_*.py no repo.", SM))
doc.build(E)
print(f"PDF gerado: {OUT}")
