# -*- coding: utf-8 -*-
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether)
OUT = os.path.expanduser("~/Desktop/Trailing_Stops_Ouro_XAU_para_Cris_e_Leonardo.pdf")
GOLD=colors.HexColor("#B8860B");GOLD_LT=colors.HexColor("#F5ECD5");INK=colors.HexColor("#1a1a1a");GREY=colors.HexColor("#555555");RED=colors.HexColor("#cc0000");BOXBG=colors.HexColor("#F7F4EC");LINE=colors.HexColor("#D8CBA6")
def PS(**k):
    n=k.pop('n'); return ParagraphStyle(n, **k)
S={"title":PS(n="t",fontName="Helvetica-Bold",fontSize=25,textColor=INK,leading=29,spaceAfter=6),
"subtitle":PS(n="s",fontName="Helvetica",fontSize=12.5,textColor=GREY,leading=16,spaceAfter=2),
"h1":PS(n="h1",fontName="Helvetica-Bold",fontSize=16,textColor=GOLD,leading=20,spaceBefore=14,spaceAfter=7),
"h2":PS(n="h2",fontName="Helvetica-Bold",fontSize=12.5,textColor=INK,leading=16,spaceBefore=9,spaceAfter=3),
"body":PS(n="b",fontName="Helvetica",fontSize=10.5,textColor=INK,leading=15.5,spaceAfter=6,alignment=TA_JUSTIFY),
"small":PS(n="sm",fontName="Helvetica",fontSize=9,textColor=GREY,leading=12.5,spaceAfter=4),
"bullet":PS(n="bu",fontName="Helvetica",fontSize=10.5,textColor=INK,leading=15,spaceAfter=3,leftIndent=12),
"mk":PS(n="mk",fontName="Helvetica-Bold",fontSize=9,textColor=INK,leading=12),
"mv":PS(n="mv",fontName="Helvetica",fontSize=9,textColor=INK,leading=12)}
st=[]
def hr(sa=6): st.append(HRFlowable(width="100%",thickness=0.8,color=LINE,spaceBefore=2,spaceAfter=sa))
def p(t,s="body"): st.append(Paragraph(t,S[s]))
def bl(items):
    for it in items: st.append(Paragraph("&#8226;&nbsp;&nbsp;"+it,S["bullet"]))
    st.append(Spacer(1,4))
def mbox(title,rows,acc=GOLD):
    data=[[Paragraph("<b>"+title+"</b>",PS(n="mt",fontName='Helvetica-Bold',fontSize=10,textColor=colors.white,leading=13)),""]]
    for k,v in rows: data.append([Paragraph(k,S["mk"]),Paragraph(v,S["mv"])])
    t=Table(data,colWidths=[34*mm,126*mm])
    t.setStyle(TableStyle([("SPAN",(0,0),(1,0)),("BACKGROUND",(0,0),(-1,0),acc),("BACKGROUND",(0,1),(-1,-1),BOXBG),("GRID",(0,1),(-1,-1),0.4,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7)]))
    return t
def call(title,text,bg=GOLD_LT,bar=GOLD):
    inner=[[Paragraph("<b>"+title+"</b>",PS(n="ct",fontName='Helvetica-Bold',fontSize=10,textColor=INK,leading=13,spaceAfter=3))],[Paragraph(text,PS(n="cb",fontName='Helvetica',fontSize=9.8,textColor=INK,leading=14,alignment=TA_JUSTIFY))]]
    t=Table(inner,colWidths=[160*mm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("LINEBEFORE",(0,0),(0,-1),3,bar),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8)]))
    return t
def foot(c,doc):
    c.saveState();c.setStrokeColor(LINE);c.setLineWidth(0.5);c.line(20*mm,14*mm,190*mm,14*mm);c.setFont("Helvetica",8);c.setFillColor(GREY)
    c.drawString(20*mm,9*mm,"Trailing Stops no Ouro (XAU) - documento interno (Cristiano & Leonardo)");c.drawRightString(190*mm,9*mm,"pag. %d"%doc.page);c.restoreState()
st.append(Spacer(1,34));st.append(HRFlowable(width="38%",thickness=3,color=GOLD,spaceAfter=13,hAlign="LEFT"))
p("Trailing Stops no Ouro<br/>&#8212; logica e metodos ideais","title");st.append(Spacer(1,5))
p("Guia pratico para o Cris e o Leonardo &#183; inclui o V_stair e as saidas que o nosso projeto testou no XAU","subtitle")
st.append(Spacer(1,16));hr(8)
p("Um trailing stop e um stop que <b>anda com o preco a nosso favor</b> &#8212; sobe (num long) a medida que o trade lucra, para <b>bloquear ganho</b> sem cortar a jornada cedo demais. A pergunta certa nunca e &laquo;qual e o melhor trailing&raquo;, e <b>&laquo;qual serve este trade, neste contexto&raquo;</b>. Este documento da os metodos, a logica de cada um, e &#8212; o mais valioso &#8212; <b>o que o ouro realmente nos ensinou</b> quando os testamos a serio.","body")
p("Aviso honesto que atravessa tudo: <b>trailing nao e gratis.</b> Troca taxa de acerto e expectativa por captura de cauda. As vezes compensa; muitas vezes um <b>alvo fixo</b> bate o trailing. Provamos com dados &#8212; seccao 3.","small")
st.append(PageBreak())
p("1 &#183; A logica: quando um trailing ajuda e quando magoa","h1");hr()
p("Um trailing resolve um problema real &#8212; <b>&laquo;apanhei a direcao certa, como e que nao devolvo o lucro?&raquo;</b> &#8212; mas cria outro: <b>o ruido.</b> O ouro respira; um stop colado demais e varrido por um recuo normal (um <i>shakeout</i>) e tira-te do trade antes do movimento a favor. Todo o desenho de um trailing e a gestao desta tensao.","body")
p("As tres leis que decidem tudo","h2")
bl(["<b>Convexidade vs. ruido.</b> Trailing brilha em movimento <b>convexo</b> &#8212; perna longa e limpa numa tendencia forte (ex.: ouro 2025). Magoa em <b>lateral/mean-revert</b> &#8212; ai e morto por shakeouts e o alvo fixo rende mais.",
"<b>Ativa so depois de +1R.</b> Primeiro <b>tira o risco</b> (stop a breakeven a +1R), so <b>depois</b> arrasta. Nunca arrastes um stop ainda no vermelho.",
"<b>Sempre no fecho (close), nunca no wick.</b> Avaliar ao <b>fecho da vela</b> ignora as caudas de liquidez que existem so para varrer stops."])
st.append(call("A pergunta que resolve 90% da decisao","&laquo;Este trade tem <b>combustivel para uma perna longa</b> (tendencia forte, catalisador, iman distante a favor)? Ou e de <b>alcance limitado</b> (range, alvo estrutural proximo, sem tendencia)?&raquo; Se e perna longa &#8594; deixa respirar (trailing largo / V_stair). Se e alcance limitado &#8594; <b>alvo fixo</b> (2R&#8211;3R) quase sempre ganha. O erro classico e trailing apertado num mercado sem tendencia = morrer aos shakeouts."))
st.append(PageBreak())
p("2 &#183; Os metodos (logica + quando usar)","h1");hr()
p("Todos assumem: <b>stop inicial estrutural</b> (abaixo da zona/swing &#8722;0,1&#215;ATR), <b>ativacao apos +1R</b>, avaliacao <b>ao fecho</b>.","body")
st.append(KeepTogether([Paragraph("&#9733; V_stair &#8212; a escada de ratchet (o favorito para uso manual)",S["h2"]),Paragraph("<b>A ideia:</b> a medida que o lucro <b>sobe degraus de R</b>, o stop <b>salta para um patamar de lucro trancado</b>. Deixa o runner correr, mas cada degrau fica <b>garantido</b> &#8212; nunca devolves abaixo dele. Meio-termo perfeito entre &laquo;alvo fixo&raquo; (bloqueia cedo) e &laquo;let-run&raquo; (arrisca devolver tudo).",S["body"])]))
st.append(mbox("V_stair &#183; a tabela real do nosso codigo",[("Atinge +2R","&#8594; trava em <b>0R (breakeven)</b> &#8212; risco eliminado"),("Atinge +5R","&#8594; trava em <b>+1R</b>"),("Atinge +8R","&#8594; trava em <b>+3R</b>"),("Atinge +12R","&#8594; trava em <b>+6R</b>"),("Atinge +16R","&#8594; trava em <b>+10R</b>"),("Logica","escada: sobe o piso de lucro em saltos discretos, nunca desce")]))
st.append(Spacer(1,3))
p("<b>Porque e bom para uso manual:</b> simples de seguir no grafico, nao te tira aos shakeouts pequenos (degraus largos), transforma um runner numa serie de lucros garantidos. <b>Brilha em:</b> trades com espaco (rompimentos, tendencia, iman HTF distante). <b>Ajuste:</b> os degraus [2,5,8,12,16] sao generosos &#8212; para trades curtos encolhe a escada (BE a +1,5R, +1R a +3R).","small")
st.append(Spacer(1,8))
st.append(mbox("Breakeven pos +1R (o minimo obrigatorio)",[("Logica","a +1R, sobe o stop para a entrada &#8212; trade <b>sem risco</b>"),("Quando","SEMPRE. E o primeiro degrau do V_stair."),("Cuidado","BE exato as vezes e varrido por 1 tick; usa entrada &#8722;0,1&#215;ATR")]))
st.append(Spacer(1,7))
st.append(mbox("Trail por estrutura &#8212; swing-low (mais 'price-action')",[("Logica","arrasta o stop para <b>debaixo de cada novo swing-low confirmado</b> (&#8722;buffer ATR)"),("Quando","tendencias com pernas limpas / higher-lows visiveis; o teu estilo de zonas"),("Cuidado","em choppy os swing-lows ficam colados = shakeout")]))
st.append(Spacer(1,7))
st.append(mbox("Chandelier ATR (topo &#8722; k&#215;ATR)",[("Logica","stop = maximo do trade &#8722; <b>k&#215;ATR</b> (k&#8776;3); segue o topo a distancia de volatilidade"),("Quando","runners em tendencia forte; adapta-se a volatilidade"),("Cuidado","muito sensivel a k. No teste, so k=5 'funcionava' &#8212; era miragem de 2025 (seccao 3)")]))
st.append(Spacer(1,7))
st.append(mbox("Regime / trend-exit (segurar enquanto a tendencia dura)",[("Logica","NAO e stop de preco &#8212; <b>sai quando o regime vira</b> (alta&#8594;nao-alta no diario)"),("Quando","reversoes que cavalgam uma tendencia inteira (o exit aprovado da nossa L2)"),("Cuidado","segura meses, aceita DD grande; so para quem aguenta exposicao")]))
st.append(Spacer(1,7))
st.append(mbox("R-ladder / ATR-trail (sistematicos)",[("R-ladder","trava 1R atras do pico-R confirmado, em degraus inteiros &#8212; primo mecanico do V_stair"),("ATR-trail","stop = fecho &#8722; k&#215;ATR; segue o preco, nao o topo. Mais 'solto'."),("Quando","regra 100% mecanica sem julgar estrutura")]))
st.append(PageBreak())
p("3 &#183; O que o ouro nos ensinou (a evidencia honesta)","h1");hr()
p("Testamos <b>todos</b> estes metodos a serio na estrategia de continuacao 4H (L1), com validacao estatistica. O resultado surpreende &#8212; e e a licao mais importante.","body")
st.append(call("A conclusao que muda a intuicao","Na continuacao 4H do ouro, <b>NENHUM trailing bateu o alvo fixo de +3R de forma robusta.</b> O melhor candidato (Chandelier k=5) parecia espetacular (+123R vs +45R) MAS: (1) so funcionava com k=5,0 exato &#8212; k=4,5 e k=5,5 falhavam (sorte de parametro, nao edge); (2) <b>88&#8211;92% do ganho vinha SO de 2025</b> &#8212; o ano da parabola (2600&#8594;4700); (3) 2 trades = 55% do total; (4) fora de 2025 o trailing <b>perdia</b> para o +3R. Traducao: &laquo;continuation corre limpo &#8594; trailing cavalga&raquo; e verdade <b>so em ano de tendencia forte</b> &#8212; condicional ao regime, nao edge de saida duravel.",bg=colors.HexColor("#FBF3E6"),bar=RED))
st.append(Spacer(1,8))
p("A saida ideal depende da NATUREZA da estrategia","h2")
st.append(mbox("O que ganhou em cada motor nosso (validado)",[("Continuacao 4H (L1)","<b>alvo fixo +3R.</b> Trailing = beta de 2025. Sem runners multi-R cavalgaveis fora de tendencia forte."),("Reversao/zona 4H (L2)","<b>trend-exit / regime-flip.</b> Segura enquanto a tendencia dura &#8212; capta convexidade (+105R vs +36R). Aceita DD maior."),("Runner de fundo 15M (swept)","<b>let-run com trail de swing-low</b> apos +1R (cap ~20R). Desenhada para cavalgar a perna de recuperacao."),("Capitulacao 15M (Cp)","<b>alvo fixo 3R.</b> Caminho pos-fundo 'choppy' &#8212; o MFE de 6R existe mas nao e capturavel sem ser varrido.")]))
st.append(Spacer(1,6))
p("O padrao: estrategias de <b>alcance-limitado / caminho ruidoso</b> (continuacao, capitulacao) preferem <b>alvo fixo</b>; as de <b>cavalgar tendencia</b> (reversao-de-regime, runner) preferem <b>deixar correr com trailing estrutural</b>. E a seccao 1: convexidade vs. ruido.","body")
st.append(PageBreak())
p("4 &#183; Guia de decisao pratico (para usar ao vivo)","h1");hr()
p("Tres perguntas antes de gerir a saida &#8212; a resposta escolhe o metodo:","body")
st.append(mbox("Arvore de decisao",[("1. Combustivel para perna longa?","tendencia forte / catalisador / iman HTF distante a favor &#8594; SIM = trailing; NAO = alvo fixo"),("2. Caminho limpo ou ruidoso?","higher-lows claros = trail de swing; choppy/range = alvo fixo (evita shakeouts)"),("3. Conta/psicologia aguenta exposicao?","sim = V_stair largo ou regime-exit; nao = alvo fixo 2-3R ou V_stair apertado")]))
st.append(Spacer(1,8))
p("As receitas por cenario","h2")
bl(["<b>Scalp / continuacao com alvo estrutural claro</b> &#8594; <b>alvo fixo 2R&#8211;3R.</b> O que ganha no ouro fora de tendencia-forte. Simples e robusto.",
"<b>Dia de tendencia forte / rompimento com espaco</b> &#8594; <b>V_stair</b> ou <b>trail de swing-low</b>. Aqui e onde o trailing paga.",
"<b>Reversao numa zona HTF (4H/1D) que pode virar a tendencia</b> &#8594; <b>trend/regime-exit</b>.",
"<b>Mercado lateral / pre-evento (ex.: pre-FOMC) / ADX morto</b> &#8594; <b>alvo fixo</b> apertado. NUNCA trailing apertado &#8212; fabrica de shakeouts.",
"<b>Sempre</b> &#8594; <b>breakeven apos +1R</b>. Primeiro tira o risco; so depois cavalga."])
st.append(call("O erro n.1 a evitar (que os dados provam)","<b>Assumir que trailing e sempre melhor.</b> Nao e. No ouro, um trailing apertado destroi a taxa de acerto e a sequencia de perdas &#8212; e fora de um ano de parabola, rende <b>menos</b> que um alvo fixo. Usa trailing so com convexidade real; caso contrario, o alvo fixo e o teu amigo. E testa sempre na tua serie antes de acreditar num &laquo;edge&raquo; de saida &#8212; o Chandelier k=5 parecia genial e era miragem.",bg=GOLD_LT))
st.append(Spacer(1,8))
p("Resumo de uma linha","h2")
p("<b>Tira o risco a +1R; alvo fixo 2-3R por defeito; V_stair ou trail de swing so em perna longa e caminho limpo; regime-exit para cavalgar tendencias; nunca trailing apertado num mercado sem combustivel.</b>","body")
SimpleDocTemplate(OUT,pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=20*mm,title="Trailing Stops no Ouro (XAU)",author="Cristiano & Leonardo").build(st,onFirstPage=foot,onLaterPages=foot)
print("PDF:",OUT,"-",os.path.getsize(OUT),"bytes")
