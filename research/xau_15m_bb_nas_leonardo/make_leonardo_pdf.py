#!/usr/bin/env python3
"""Gera PDF explicativo da estrategia XAU 15M LONG (pre-aprovada) para o Leonardo. Cris 2026-06-27.
Texto detalhado (logica tecnica + o que validamos) + os 36 prints em ordem da pasta Desktop.
Saida: ~/Desktop/Estrategia_XAU_15M_5ATR_Leonardo.pdf. Usa reportlab+PIL. Sem char '!=' especial (fonte)."""
from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle)

PRINTS = Path("/Users/cristrein/Desktop/5ATR + 4H & B v3 ≠BEAR")
OUT = Path("/Users/cristrein/Desktop/Estrategia_XAU_15M_5ATR_Leonardo.pdf")
PAGE = landscape(A4); W,H = PAGE
ML=MR=1.6*cm; MT=1.4*cm; MB=1.2*cm
AVW = W-ML-MR

ss=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=ss["Heading1"],fontSize=20,leading=24,textColor=colors.HexColor("#1a2b4a"),spaceAfter=6)
SUB=ParagraphStyle("SUB",parent=ss["Normal"],fontSize=11,leading=14,textColor=colors.HexColor("#666666"),spaceAfter=2)
H2=ParagraphStyle("H2",parent=ss["Heading2"],fontSize=13.5,leading=17,textColor=colors.HexColor("#0b5d3b"),spaceBefore=10,spaceAfter=4)
BODY=ParagraphStyle("BODY",parent=ss["Normal"],fontSize=10.5,leading=15,spaceAfter=4,alignment=4)
BUL=ParagraphStyle("BUL",parent=BODY,leftIndent=12,bulletIndent=2,spaceAfter=2)
CAP=ParagraphStyle("CAP",parent=ss["Normal"],fontSize=9,leading=11,textColor=colors.HexColor("#555555"),alignment=1,spaceBefore=4)
NOTE=ParagraphStyle("NOTE",parent=BODY,fontSize=9.5,leading=13,textColor=colors.HexColor("#7a3b00"))

S=[]
def P(t,st=BODY): S.append(Paragraph(t,st))
def B(t): S.append(Paragraph("• "+t,BUL))

# ---------- CAPA / TEXTO ----------
P("Estrategia XAU 15M LONG — \"5ATR + Regime\"",H1)
P("Documento explicativo para Leonardo · Ouro (XAU/USD) · grafico de 15 minutos · 27/06/2026 · status: PRE-APROVADA",SUB)
P("Estrategia de COMPRA (long) de ouro no grafico de 15 minutos. Perfil: <b>scalp de alto acerto</b> — "
  "acerta muito, com ganhos controlados e perda maxima pequena. Nao busca tacadas gigantes; busca consistencia. "
  "Todas as regras foram calibradas e auditadas em ~2 anos de dados reais (2024–2026) com verificacao adversarial "
  "(um \"advogado do diabo\" tentando derrubar cada achado antes de aprovar).")

P("1. A ideia central (em uma frase)",H2)
P("Comprar o repique de um fundo que <b>provou forca</b>, apenas quando o mercado maior <b>nao esta caindo nem de lado</b>, "
  "e gerir a saida para deixar o lucro respirar <b>sem abrir mao do alto acerto</b>.")

P("2. Entrada — gatilho \"5ATR confirm\"",H2)
B("O sistema marca um <b>fundo local</b> (uma minima destacada, chamada minima fractal).")
B("Ele <b>nao compra no fundo</b>. Espera o preco subir forte: <b>5×ATR acima desse fundo</b> "
  "(ATR = medida de volatilidade; 5×ATR = um salto relevante).")
B("A compra ocorre no <b>fechamento da vela</b> que confirma esse salto.")
B("Por que assim: exigir o salto <b>filtra fundos que nao seguram</b>. E uma entrada \"atrasada\" de proposito — "
  "troca preco por confirmacao. Validado: entrar antes, sem confirmacao, piora o resultado.")

P("3. Filtros — so entra se TODOS passarem",H2)
B("<b>Forca do impulso (A2):</b> a perna de alta precisa ser eficiente e ampla. Evita repiques fracos.")
B("<b>Anti-range (h1_eff):</b> nao entra com o mercado \"de lado\" (sem direcao). Esse filtro sozinho "
  "<b>cortou o drawdown pela metade</b> — e a peca mais solida da estrategia.")
B("<b>Regime de tendencia (4H e Diario nao-BEAR):</b> so compra quando nem o grafico de 4 horas nem o diario "
  "estao em tendencia de baixa. Sempre a favor do contexto maior.")
B("<b>Uma posicao por vez:</b> nunca sobrepoe operacoes; ao bloquear um trade ruim, libera a vaga para o proximo melhor.")

P("4. Stop (SL) — \"flush\"",H2)
P("O stop fica <b>logo abaixo do fundo da perna</b> (a menor minima ate a entrada, menos um respiro de 0,1×ATR). "
  "E um stop <b>estrutural</b>: se o preco perde o fundo que deu origem ao trade, a tese morreu e saimos.")

P("5. Saida (EXIT) — trailing escalonado \"K2 gb2.0\"",H2)
B("<b>Fase 1 (ate +2R):</b> trailing apertado, colado nos fundinhos. Protege o ganho cedo.")
B("<b>Fase 2 (apos +2R):</b> o trailing <b>afrouxa</b> — passa a acompanhar o topo permitindo devolver ate "
  "<b>2R do pico</b> antes de sair.")
B("Ideia: a maioria e scalp (sai perto de +1R). Quando um trade mostra forca (passa de +2R), o sistema da corda "
  "para ele respirar e correr mais — <b>sem trocar o perfil de alto acerto</b>. (R = multiplo do risco; +2R = ganhou o dobro do que arriscou.)")

P("6. O que VALIDAMOS — e o que descartamos (auditoria adversarial)",H2)
B("<b>FICOU:</b> filtro anti-range (h1_eff) + regime nao-BEAR — melhoram acerto e reduzem risco de forma robusta.")
B("<b>FICOU:</b> SL flush + saida K2 gb2.0 — o ajuste de saida adiciona lucro mantendo acerto e drawdown identicos.")
B("<b>CAIU:</b> inverter para vender em topos (short espelho) — perde dinheiro; o gatilho nao detecta topo.")
B("<b>CAIU:</b> refinar a entrada com \"limite na demanda\" — virou ruido e piorou o drawdown.")
B("<b>CAIU:</b> clonar as saidas gigantes (runners) — comprovadamente <b>nao e reproduzivel por regra</b>: os grandes "
  "movimentos sao lentos (~162 velas) e nenhuma pista na entrada os separa. Por isso o perfil e de <b>acerto alto, nao de tacada grande</b>.")

P("7. Resultados (2 anos · 170 operacoes · calibracao em historico)",H2)
tdata=[["Metrica","Valor"],
       ["Acerto (win rate)","64,1%"],
       ["Resultado total","+70,5 R"],
       ["Perda maxima acumulada (drawdown)","-3,0 R (muito baixa)"],
       ["Sequencia maxima de perdas","3"],
       ["Por ano (2024 / 2025 / 2026)","+17,4 / +44,7 / +8,4 R"]]
t=Table(tdata,colWidths=[10*cm,9*cm])
t.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0b5d3b")),
    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ("FONTSIZE",(0,0),(-1,-1),10.5),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f2f6f3"),colors.white]),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#cccccc")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
]))
S.append(t); S.append(Spacer(1,6))
P("<b>Leitura honesta:</b> estrategia pequena, positiva e de baixissimo risco. E <b>calibracao em dados historicos</b> "
  "(nao e resultado ao vivo). Caveats: alguns stops com gap nao modelados; numeros absolutos um pouco otimistas no "
  "preenchimento; vigiar o desempenho em 2026.",NOTE)

P("8. Como ler os prints (proximas paginas)",H2)
B("Cada imagem e o grafico de 15M com as operacoes desenhadas: caixa de posicao = um trade (entrada, stop embaixo, alvo/saida em cima).")
B("Numero #N = ordem da operacao. <b>Verde = operacao vencedora</b> · <b>Vermelho = operacao perdedora</b>.")
B("As 36 imagens cobrem a sequencia de operacoes em ordem cronologica.")

S.append(PageBreak())

# ---------- PRINTS ----------
files=sorted(PRINTS.glob("*.png"))
N=len(files)
avail_h = H-MT-MB-1.1*cm   # espaco p/ imagem (deixa caption)
for idx,f in enumerate(files,1):
    iw,ih=PILImage.open(f).size; ar=ih/iw
    w=AVW; h=w*ar
    if h>avail_h: h=avail_h; w=h/ar
    S.append(Image(str(f),width=w,height=h))
    S.append(Paragraph(f"Print {idx} de {N} — operacoes plotadas (verde = ganho, vermelho = perda)",CAP))
    if idx<N: S.append(PageBreak())

def footer(canvas,doc):
    canvas.saveState(); canvas.setFont("Helvetica",7.5); canvas.setFillColor(colors.HexColor("#999999"))
    canvas.drawString(ML,0.6*cm,"XAU 15M LONG \"5ATR + Regime\" — pre-aprovada — documento interno")
    canvas.drawRightString(W-MR,0.6*cm,f"pag. {doc.page}")
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=PAGE,leftMargin=ML,rightMargin=MR,topMargin=MT,bottomMargin=MB,
                      title="Estrategia XAU 15M LONG 5ATR+Regime",author="Cris")
doc.build(S,onFirstPage=footer,onLaterPages=footer)
print(f"OK -> {OUT}")
print(f"prints incluidos: {N} | tamanho: {OUT.stat().st_size//1024} KB")
