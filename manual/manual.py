"""Gera dist/Manual do Escriba.pdf. Precisa do reportlab (pip install reportlab)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

AQUI = Path(__file__).parent
SAIDA = AQUI.parent / "dist" / "Manual do Escriba.pdf"
VERSAO = "Outubro de 2026"

FONTES = Path("C:/Windows/Fonts")
for nome, arquivo in (("Texto", "segoeui.ttf"), ("Texto-Negrito", "segoeuib.ttf"),
                      ("Texto-Italico", "segoeuii.ttf"), ("Codigo", "consola.ttf")):
    pdfmetrics.registerFont(TTFont(nome, FONTES / arquivo))
pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-Negrito", italic="Texto-Italico",
                              boldItalic="Texto-Negrito")

VERDE = colors.HexColor("#2C5234")
REALCE = colors.HexColor("#4A7C59")
CINZA = colors.HexColor("#5B6470")
FUNDO_TABELA = colors.HexColor("#E6EEE8")
FUNDO_NOTA = colors.HexColor("#EEF5F0")
FUNDO_ATENCAO = colors.HexColor("#FFF4D6")
LINHA = colors.HexColor("#C9D4CC")

corpo = ParagraphStyle("corpo", fontName="Texto", fontSize=10, leading=14, spaceAfter=6)
ESTILOS = {
    "corpo": corpo,
    "h1": ParagraphStyle("h1", parent=corpo, fontName="Texto-Negrito", fontSize=18, leading=23,
                         textColor=VERDE, spaceBefore=4, spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=corpo, fontName="Texto-Negrito", fontSize=12.5, leading=17,
                         textColor=REALCE, spaceBefore=10, spaceAfter=5),
    "item": ParagraphStyle("item", parent=corpo, leftIndent=16, bulletIndent=2, spaceAfter=4),
    "passo": ParagraphStyle("passo", parent=corpo, leftIndent=22, bulletIndent=2, spaceAfter=5),
    "celula": ParagraphStyle("celula", parent=corpo, fontSize=9.5, leading=13, spaceAfter=0),
    "cabecalho": ParagraphStyle("cabecalho", parent=corpo, fontName="Texto-Negrito", fontSize=9.5,
                                leading=13, spaceAfter=0, textColor=VERDE),
    "legenda": ParagraphStyle("legenda", parent=corpo, fontName="Texto-Italico", fontSize=9,
                              textColor=CINZA, alignment=TA_CENTER, spaceAfter=10),
    "capa-titulo": ParagraphStyle("capa-titulo", fontName="Texto-Negrito", fontSize=40, leading=46,
                                  textColor=VERDE),
    "capa-sub": ParagraphStyle("capa-sub", fontName="Texto", fontSize=17, leading=23,
                               textColor=REALCE, spaceBefore=10),
    "capa-texto": ParagraphStyle("capa-texto", fontName="Texto", fontSize=11.5, leading=17,
                                 textColor=CINZA, spaceBefore=22),
    "sumario": ParagraphStyle("sumario", fontName="Texto", fontSize=11, leading=20),
}

LARGURA = A4[0] - 4.4 * cm
historia = []


def p(texto, estilo="corpo"):
    historia.append(Paragraph(texto, ESTILOS[estilo]))


def h1(texto):
    historia.append(PageBreak())
    p(texto, "h1")


def h2(texto):
    p(texto, "h2")


def itens(*linhas):
    for linha in linhas:
        historia.append(Paragraph(linha, ESTILOS["item"], bulletText="•"))


def passos(*linhas):
    for numero, linha in enumerate(linhas, 1):
        historia.append(Paragraph(linha, ESTILOS["passo"], bulletText=f"{numero}."))


def caixa(titulo, texto, fundo=FUNDO_NOTA):
    conteudo = Paragraph(f"<b>{titulo}</b> {texto}", ESTILOS["celula"])
    tabela = Table([[conteudo]], colWidths=[LARGURA])
    tabela.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fundo),
                                ("BOX", (0, 0), (-1, -1), 0.5, LINHA),
                                ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    historia.extend([Spacer(1, 3), tabela, Spacer(1, 9)])


def atencao(texto):
    caixa("Atenção.", texto, FUNDO_ATENCAO)


def tabela(cabecalho, linhas, larguras):
    dados = [[Paragraph(c, ESTILOS["cabecalho"]) for c in cabecalho]]
    dados += [[Paragraph(c, ESTILOS["celula"]) for c in linha] for linha in linhas]
    t = Table(dados, colWidths=[LARGURA * w for w in larguras], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), FUNDO_TABELA),
                           ("GRID", (0, 0), (-1, -1), 0.5, LINHA),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    historia.extend([Spacer(1, 2), t, Spacer(1, 10)])


def figura(arquivo, largura_cm, legenda):
    imagem = Image(str(AQUI / arquivo))
    proporcao = imagem.imageHeight / imagem.imageWidth
    imagem.drawWidth, imagem.drawHeight = largura_cm * cm, largura_cm * cm * proporcao
    historia.append(KeepTogether([imagem, Spacer(1, 4), Paragraph(legenda, ESTILOS["legenda"])]))


def c(texto):
    """Trecho em fonte de código: o que se digita ou o que aparece na tela."""
    return f'<font name="Codigo" size="9.5">{texto}</font>'


PASTA = c("C:\\Escriba")
PASTA_RESERVA = c("%LOCALAPPDATA%\\Programs\\Escriba")
PASTA_CONFIG = c("%APPDATA%\\Escriba")


class Manual(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h1":
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))


def rodape(tela, doc):
    tela.saveState()
    tela.setFont("Texto", 8.5)
    tela.setFillColor(CINZA)
    tela.drawString(2.2 * cm, 1.3 * cm, "Escriba · Manual de instruções")
    tela.drawRightString(A4[0] - 2.2 * cm, 1.3 * cm, str(doc.page))
    tela.setStrokeColor(LINHA)
    tela.line(2.2 * cm, 1.7 * cm, A4[0] - 2.2 * cm, 1.7 * cm)
    tela.restoreState()


def capa(tela, doc):
    tela.saveState()
    tela.setFillColor(VERDE)
    tela.rect(0, A4[1] - 3.2 * cm, A4[0], 3.2 * cm, stroke=0, fill=1)
    tela.setFillColor(REALCE)
    tela.rect(0, A4[1] - 3.5 * cm, A4[0], 0.3 * cm, stroke=0, fill=1)
    tela.restoreState()


# ---------------------------------------------------------------- capa e sumário
historia.append(Spacer(1, 4.6 * cm))
logo = Image(str(AQUI.parent / "logo" / "escriba.png"), 2.6 * cm, 2.6 * cm)
logo.hAlign = "LEFT"
historia.extend([logo, Spacer(1, 0.5 * cm)])
p("Escriba", "capa-titulo")
p("Manual de instruções", "capa-sub")
p("O aplicativo ouve o preletor pelo microfone, reconhece o livro, o capítulo e o versículo "
  "citados e deixa a passagem pronta no Holyrics, sem ninguém precisar digitar. Também volta "
  "sozinho ao texto principal do sermão e guarda a transcrição do que foi dito.", "capa-texto")
p(f"Versão do manual: {VERSAO}", "capa-texto")
historia.append(NextPageTemplate("normal"))
historia.append(PageBreak())
p("Sumário", "h2")
sumario = TableOfContents()
sumario.levelStyles = [ESTILOS["sumario"]]
historia.append(sumario)

# ---------------------------------------------------------------- 1
h1("1. O que é e como funciona")
p("O Escriba roda em um computador com Windows que recebe o áudio do preletor. Ele "
  "transforma a fala em texto no próprio computador, sem internet, e procura nesse texto "
  "referências bíblicas como “João três dezesseis” ou “Primeira aos Coríntios, capítulo treze”.")
p("Quando encontra uma referência, ele a envia pela rede local para o Holyrics, que pode estar "
  "em outro computador (por exemplo, um Mac). O Holyrics então seleciona aquele versículo na "
  "janela da Bíblia. Dependendo do modo escolhido, o versículo fica apenas selecionado, "
  "esperando o operador projetar, ou já vai para a tela.")
tabela(["Etapa", "Onde acontece", "O que acontece"], [
    ["1. Ouvir", "PC com Windows", "O áudio do microfone escolhido é captado sem parar."],
    ["2. Reconhecer", "PC com Windows", "O motor de fala transforma o áudio em texto, em tempo real."],
    ["3. Detectar", "PC com Windows", "O aplicativo procura livro, capítulo e versículo no texto e "
                                       "confere se a passagem existe na Bíblia."],
    ["4. Enviar", "Rede local", "A referência vai para o API Server do Holyrics."],
    ["5. Mostrar", "Computador do Holyrics", "O versículo é selecionado na janela da Bíblia ou projetado."],
], [0.18, 0.26, 0.56])
caixa("Em resumo:", "você configura uma vez. Depois, basta abrir o aplicativo antes do culto; ele "
      "volta com as mesmas opções e já começa a ouvir.")

h2("O que você precisa")
itens("Um computador com <b>Windows 10 (versão 1803 ou mais nova) ou 11, de 64 bits</b>, com cerca de 350 MB livres em disco "
      "e 350 MB de memória livre.",
      "Uma <b>entrada de áudio</b> nesse computador com a voz do preletor: um microfone, ou de "
      "preferência uma saída da mesa de som ligada a uma interface de áudio.",
      "O <b>Holyrics na versão 2.21 ou mais nova</b>, no mesmo computador ou em outro (Windows ou Mac).",
      "Os dois computadores na <b>mesma rede local</b> (cabo ou Wi-Fi).")
caixa("Dica.", "Quanto mais limpo o áudio, melhor o reconhecimento. Um sinal direto da mesa de som, "
      "só com a voz do preletor, funciona muito melhor do que um microfone captando o ambiente.")

# ---------------------------------------------------------------- 2
h1("2. Instalação no computador com Windows")
passos(f"Copie o arquivo {c('Instalar Escriba.exe')} para o computador (por pendrive, rede ou nuvem).",
       "Dê dois cliques no arquivo.",
       "Se aparecer a tela azul “O Windows protegeu o computador”, clique em <b>Mais informações</b> "
       "e depois em <b>Executar assim mesmo</b>. Isso acontece porque o instalador não tem "
       "assinatura digital paga; não indica problema no arquivo.",
       "Na pergunta “Instalar o Escriba neste computador?”, clique em <b>Sim</b>.",
       "Uma janela preta aparece com a mensagem “Instalando o Escriba”. Aguarde; costuma "
       "levar menos de um minuto.",
       "Ao terminar, o Escriba abre sozinho e surge o aviso de instalação concluída. "
       "Clique em <b>OK</b>.")
h2("O que o instalador faz")
itens(f"Copia o programa para a pasta {PASTA}. Se o Windows não permitir criar essa "
      f"pasta, usa {PASTA_RESERVA}.",
      "Cria o atalho <b>Escriba</b> na área de trabalho e no menu Iniciar.",
      "Registra o programa na lista de aplicativos instalados do Windows.")
p("Não é preciso instalar mais nada: o reconhecimento de fala e os modelos de português já vêm "
  "dentro do instalador.")
h2("Atualizar")
p("Para instalar uma versão nova, basta rodar o instalador novo. Ele fecha o aplicativo, "
  "substitui os arquivos e mantém as suas configurações.")
h2("Se o computador tinha o Bible Crawler")
p("Bible Crawler era o nome deste aplicativo até outubro de 2026. O instalador do Escriba "
  "remove a instalação antiga e aproveita a configuração dela (microfone, IP e token); não é "
  "preciso desinstalar nem configurar de novo. Se o Bible Crawler abria junto com o Windows, o "
  "Escriba passa a abrir também.")
h2("Desinstalar")
p("Abra <b>Configurações &gt; Aplicativos &gt; Aplicativos instalados</b>, procure "
  "<b>Escriba</b> e escolha <b>Desinstalar</b>. A pasta do programa e os atalhos são "
  f"removidos. As configurações ficam guardadas em {PASTA_CONFIG}; apague essa pasta "
  "à mão se quiser começar do zero.")

# ---------------------------------------------------------------- 3
h1("3. Preparar o Holyrics")
p("O Escriba conversa com o Holyrics por um recurso chamado <b>API Server</b>, que precisa "
  "ser ligado uma única vez. Faça os passos abaixo no computador onde o Holyrics está instalado.")
h2("Conferir a versão")
p("O Holyrics precisa estar na versão <b>2.21 ou mais nova</b>. A versão aparece na tela “Sobre” "
  "do programa. Se for mais antiga, atualize antes de continuar; por segurança, faça um backup "
  "pelo próprio Holyrics antes de atualizar.")
h2("Ligar o API Server e criar o token")
passos("No Holyrics, abra o menu <b>Arquivo &gt; Configurações &gt; API Server</b>.",
       "Ative o servidor para a rede local. A porta padrão é <b>8091</b>; mantenha esse número, "
       "a não ser que outro programa já use essa porta.",
       "Clique em <b>gerenciar permissões</b> e crie um token. O token é uma senha: uma sequência "
       "de letras e números que você escolhe ou que o Holyrics gera.",
       f"Nas permissões desse token, para a rede local, marque as ações {c('SelectVerse')} "
       f"(selecionar versículo) e {c('ShowVerse')} (projetar versículo).",
       "Confirme e anote o token. Você vai digitá-lo no Escriba.")
caixa("Observação.", "Os nomes exatos dos botões podem mudar um pouco de uma versão do Holyrics "
      "para outra. O caminho é sempre o das configurações do API Server.")
h2("Descobrir o endereço IP do computador do Holyrics")
itens("<b>No Mac:</b> abra <b>Ajustes do Sistema &gt; Rede</b>, clique na conexão ativa (Wi-Fi ou "
      "Ethernet) e veja o campo <b>Endereço IP</b>. Ele tem um formato como 192.168.0.50.",
      f"<b>No Windows:</b> abra o Prompt de Comando, digite {c('ipconfig')} e procure a linha "
      "<b>Endereço IPv4</b>.",
      "<b>Holyrics e Escriba no mesmo computador:</b> use o IP 127.0.0.1.")
atencao("O roteador pode trocar o IP do computador de tempos em tempos, e o Escriba para de "
        "alcançar o Holyrics quando isso acontece. Para evitar, reserve um IP fixo para o "
        "computador do Holyrics nas configurações do roteador (reserva de DHCP).")
h2("Liberar o firewall")
p("Na primeira vez em que o API Server é ligado, o sistema pode perguntar se o Holyrics pode "
  "receber conexões da rede. Responda <b>Permitir</b>. No Mac, essa opção fica em <b>Ajustes do "
  "Sistema &gt; Rede &gt; Firewall</b>; no Windows, em <b>Segurança do Windows &gt; Firewall</b>.")

# ---------------------------------------------------------------- 4
h1("4. A janela do Escriba")
figura("janela.png", 7.6, "A janela principal, com dados de exemplo.")
tabela(["Campo", "Para que serve"], [
    ["Motor de fala", "O programa que transforma a voz em texto. Deixe em <b>sherpa-onnx</b>, que é o "
                      "mais preciso. O capítulo 9 explica os outros."],
    ["Microfone", "A entrada de áudio que será ouvida. A primeira opção da lista (“Mapeador de som”) "
                  "é o microfone padrão do Windows. Com o motor Windows, este campo fica bloqueado."],
    ["O que deixar pronto no Holyrics", "O modo de trabalho: até onde o aplicativo vai sozinho. Veja o capítulo 5."],
    ["Pedir confirmação antes de enviar", "Quando marcado, cada referência detectada aparece em um aviso e só "
                                           "é enviada se alguém confirmar. Veja o capítulo 5."],
    ["Tempo máximo entre o livro e o capítulo", "Quantos segundos podem passar entre o preletor dizer o livro e "
                                                 "dizer o número. O mesmo limite vale entre o capítulo e o versículo. "
                                                 "O padrão é 3 segundos."],
    ["Texto principal do sermão", "A passagem à qual o preletor volta várias vezes. Depois de outra "
                                  "citação, o aplicativo retorna a ela sozinho, passado o tempo "
                                  "indicado em <b>Voltar a ele</b>. Veja o capítulo 6."],
    ["Salvar a transcrição em", "A pasta onde fica o texto de tudo o que foi ouvido, com a hora de "
                                "cada frase. Vazio, nada é gravado. Veja o capítulo 7."],
    ["IP, Porta e Token", "Os dados do API Server do Holyrics, preparados no capítulo 3."],
], [0.32, 0.68])
historia.append(PageBreak())
h2("As três linhas de baixo")
tabela(["Linha", "O que mostra"], [
    ["Estado", f"{c('Desativado')}, {c('Carregando…')}, {c('Ouvindo (motor)')} ou uma mensagem de erro. "
               "Depois de um erro, o aplicativo tenta de novo sozinho a cada 5 segundos."],
    ["Ouvido", "O trecho mais recente que o motor de fala entendeu. Serve para conferir se o áudio "
               "está chegando e se o reconhecimento está bom."],
    ["Envio", f"O resultado do último envio ao Holyrics: {c('Selecionado: João 3:16')}, "
              f"{c('Projetado: João 3:16')} ou {c('Falhou (João 3:16): …')} com o motivo. Na volta ao "
              f"texto principal aparece {c('(texto principal)')} no fim."],
], [0.2, 0.8])
p("Tudo o que você altera é salvo na hora. Ao abrir de novo, o aplicativo volta como estava e "
  "começa a ouvir sem precisar clicar em nada.")

# ---------------------------------------------------------------- 5
h1("5. Os modos de trabalho")
p("O modo define até onde o Escriba vai por conta própria. Em todos, menos no último, o "
  "versículo fica apenas <b>selecionado</b> na janela da Bíblia do Holyrics; quem projeta é o operador.")
tabela(["Modo", "O que o aplicativo faz", "Se o preletor disser “João três dezesseis”"], [
    ["Desativado", "Para de ouvir e libera o microfone.", "Nada acontece."],
    ["Só o livro", "Seleciona o livro.", "O Holyrics vai para João 1:1."],
    ["Livro e capítulo", "Seleciona o livro e o capítulo.", "O Holyrics vai para João 3:1."],
    ["Livro, capítulo e versículo", "Seleciona a passagem completa, atualizando à medida que ouve.",
     "O Holyrics vai para João 3 e, em seguida, para João 3:16."],
    ["Livro, capítulo e versículo, e já projeta", "Faz o mesmo e, quando a referência é dita inteira e em "
                                                    "sequência, projeta o versículo.",
     "João 3:16 é selecionado e, um segundo depois, vai para a tela."],
], [0.27, 0.38, 0.35])
caixa("Por que João 1:1 e João 3:1?", "O Holyrics não tem um comando para selecionar só o livro ou só "
      "o capítulo. Por isso, nos modos parciais, o aplicativo seleciona o primeiro versículo.")
h2("Cuidados com o modo que projeta")
itens("O aplicativo só projeta quando ouve livro, capítulo e versículo em sequência. Pedaços "
      "soltos, como “versículo dezessete” dito mais tarde, apenas mudam a seleção.",
      "Há uma espera de 1 segundo antes de projetar. Ela evita mostrar “João 3:20” quando o "
      "preletor ainda está dizendo “vinte e um”.",
      "A volta automática ao texto principal (capítulo 6) nunca projeta: só seleciona.",
      "Se o motor de fala entender errado, o versículo errado vai para a tela. Use este modo só "
      "depois de conferir, em alguns cultos, que o reconhecimento está confiável com o seu áudio.")
historia.append(PageBreak())
h2("A confirmação antes de enviar")
p("Com a opção <b>Pedir confirmação antes de enviar</b> marcada, cada referência detectada "
  "aparece em um aviso no canto inferior direito da tela do computador com Windows:")
figura("aviso.png", 4.4, "O aviso de confirmação.")
itens("<b>Enter</b> ou o botão <b>Enviar</b> manda a referência para o Holyrics.",
      "<b>Esc</b> ou o botão <b>Descartar</b> ignora a referência.",
      "Sem resposta no tempo indicado ao lado da opção (4 segundos, por padrão), a referência é descartada.",
      "Se o preletor citar outra passagem enquanto o aviso está aberto, ele troca para a mais recente.")
atencao("O aviso aparece no computador onde o Escriba está instalado, não no computador do "
        "Holyrics. Só faz sentido ligar a confirmação se houver alguém olhando para essa tela.")

# ---------------------------------------------------------------- 6
h1("6. O texto principal do sermão")
p("Em muitos sermões o preletor lê um texto base e volta a ele várias vezes: começa em "
  "2 Coríntios 4:1, cita Romanos, e minutos depois retoma “o versículo dois”. Sem ajuda, o "
  "Holyrics ficaria parado em Romanos. Com o texto principal definido, o Escriba volta a ele "
  "sozinho.")
h2("Como usar")
passos(f"No campo <b>Texto principal do sermão</b>, digite a passagem: {c('2 Coríntios 4:1')}.",
       f"Confira ao lado do campo o que o aplicativo entendeu: {c('→ 2 Coríntios 4:1')}. Se aparecer "
       f"{c('não entendi')}, reescreva com o nome do livro por extenso e o capítulo.",
       "Em <b>Voltar a ele</b>, escolha quantos segundos esperar depois de outra citação. O padrão é 60.")
p("O campo aceita o que você escreveria normalmente: “2 Coríntios 4:1”, “2 corintios 4 1”, "
  "“Salmo 23”, “segunda coríntios quatro um”. É preciso informar pelo menos o livro e o capítulo.")
h2("O que acontece durante o sermão")
tabela(["Momento", "O que o aplicativo faz"], [
    ["O preletor cita “Romanos oito vinte e oito”.",
     "Seleciona Romanos 8:28 no Holyrics e começa a contar o tempo."],
    ["Passam 60 segundos sem outra citação.",
     "Volta a selecionar 2 Coríntios 4:1. A linha de envio mostra "
     f"{c('Selecionado: 2 Coríntios 4:1 (texto principal)')}."],
    ["O preletor diz “versículo dois”.",
     "Seleciona 2 Coríntios 4:2. O texto principal avança junto: a próxima volta será para o versículo 2."],
    ["O preletor cita outra passagem antes de o tempo acabar.",
     "Vai para a nova passagem e recomeça a contagem."],
    ["O tempo acaba enquanto o preletor está no meio de uma frase.",
     "Espera a frase terminar. Se nela houver outra citação, a citação vale e a contagem "
     "recomeça; se não, volta ao texto principal na pausa."],
], [0.42, 0.58])
h2("Detalhes que convém saber")
itens("<b>O ponto de retorno acompanha a leitura.</b> Cada citação dentro do mesmo livro e capítulo "
      "do texto principal atualiza para onde voltar. O ponto atual aparece ao lado do campo.",
      "<b>“Versículo três” passa a ser do texto principal.</b> Desde que o campo é preenchido, e de "
      "novo a cada volta, “versículo…” e “capítulo…” ditos sem livro valem para ele.",
      "<b>A volta só seleciona.</b> Mesmo no modo que projeta, o retorno nunca vai para a tela "
      "sozinho, e não passa pelo aviso de confirmação.",
      "<b>O modo continua valendo.</b> Em “Só o livro” ou “Livro e capítulo”, a volta seleciona só "
      "até onde o modo permite.",
      "<b>O tempo deve cobrir a leitura da citação.</b> Se o preletor costuma ler e comentar a "
      "passagem citada por dois minutos, use 120 segundos ou mais. O campo aceita de 5 a 900.")
atencao("O texto principal fica salvo de um culto para o outro. Troque-o antes de cada sermão, ou "
        "apague o campo para desligar a volta automática. Se o sermão passar para outro capítulo "
        "(do 4 para o 5, por exemplo), atualize o campo: o aplicativo trata o capítulo novo como "
        "outra citação e voltaria ao capítulo anterior.")

# ---------------------------------------------------------------- 7
h1("7. A transcrição")
p("O Escriba pode guardar em arquivo o texto de tudo o que o motor de fala entendeu, com a hora "
  "de cada frase.")
h2("Como ligar e desligar")
passos("Ao lado de <b>Salvar a transcrição em</b>, clique em <b>Escolher…</b> e aponte uma pasta.",
       "Pronto: a gravação começa na próxima frase, sem precisar clicar em mais nada.",
       "Para desligar, apague o conteúdo do campo.")
LIGADA, DESLIGADA = c('"transcricao": true'), c('"transcricao": false')
caixa("Para tirar a opção da janela:", f"feche o Escriba, abra o arquivo {c('config.json')} em "
      f"{PASTA_CONFIG} no Bloco de Notas e troque {LIGADA} por {DESLIGADA}. A linha some da "
      "janela e nada é gravado, mesmo com uma pasta escolhida. Para trazer de volta, troque de "
      "novo por true.")
h2("O que é gravado")
p(f"Um arquivo de texto por dia, com o nome {c('Transcrição 2026-10-11.txt')} (ano, mês e dia). "
  "Cada frase ocupa uma linha, precedida da hora em que começou a ser dita:")
p(c("[19:42:07] Abram a Bíblia em segunda Coríntios, capítulo quatro.") + "<br/>" +
  c("[19:42:15] Versículo um. Pelo que, tendo este ministério,") + "<br/>" +
  c("[19:42:31] Como diz o apóstolo em Romanos oito, vinte e oito."))
itens("A linha é gravada assim que a frase termina (numa pausa do preletor). Se o computador "
      "desligar no meio do culto, o que já foi dito está salvo.",
      "Dois cultos no mesmo dia vão para o mesmo arquivo; a hora de cada linha os separa.",
      "Só há gravação enquanto o aplicativo está ouvindo. No modo <b>Desativado</b>, nada é gravado.",
      "O arquivo abre no Bloco de Notas, no Word ou em qualquer editor de texto.")
h2("O que esperar do texto")
itens("É o texto como o motor de fala o entendeu: sem revisão, com erros em nomes próprios e "
      "palavras incomuns, e com a pontuação que o motor arrisca (o Vosk não pontua). Serve de "
      "rascunho e de índice do sermão, não de registro fiel.",
      "Tudo o que o microfone captar é transcrito: avisos, orações e letras de cânticos também.",
      "Use o motor <b>sherpa-onnx</b>. O motor <b>Windows</b> só reconhece o vocabulário bíblico e "
      "produz uma transcrição sem serventia.")
atencao("Se a pasta escolhida for sincronizada com a nuvem (Google Drive, OneDrive), a "
        "transcrição sobe para lá. Escolha a pasta de acordo com quem pode ler esse texto.")

# ---------------------------------------------------------------- 8
h1("8. Como falar para o aplicativo entender")
p("O aplicativo reconhece as formas mais comuns de citar a Bíblia em português. A tabela mostra "
  "o que funciona.")
tabela(["O preletor diz", "O aplicativo entende"], [
    ["João três dezesseis", "João 3:16"],
    ["João, capítulo três, versículo dezesseis", "João 3:16"],
    ["Salmo vinte e três", "Salmos 23"],
    ["Salmo cento e dezenove, versículo cento e cinco", "Salmos 119:105"],
    ["Primeira aos Coríntios, capítulo treze", "1 Coríntios 13"],
    ["Segundo livro de Reis, cinco", "2 Reis 5"],
    ["Primeira de João, quatro oito", "1 João 4:8"],
    ["Evangelho de João (sem número)", "João (só o livro)"],
    ["Romanos oito, versículos vinte e oito a trinta", "Romanos 8:28-30"],
    ["Judas cinco (livro de um capítulo só)", "Judas 1:5"],
    ["Apocalipse de João, vinte e dois", "Apocalipse 22"],
], [0.62, 0.38])
h2("As regras")
itens("<b>O número vem logo depois do livro.</b> “João três” vale. “Jonas ficou três dias” não vale, "
      "porque há palavras entre o livro e o número. A palavra “capítulo” pode ficar no meio: "
      "“João, no capítulo três”.",
      "<b>Há um tempo máximo.</b> Entre o livro e o capítulo, e entre o capítulo e o versículo, podem "
      "passar no máximo 3 segundos (ajustável na janela).",
      "<b>O livro sozinho não vale.</b> Dizer apenas “João” não faz nada, pois pode ser a pessoa. "
      "Para selecionar só o livro, diga “livro de…”, “evangelho de…”, “carta aos…”, “epístola…” "
      "ou “abram em…”.",
      "<b>Livros com número precisam do ordinal.</b> “Primeira aos Coríntios”, “Segunda de Pedro”, "
      "“Terceira de João”. Dizer só “Coríntios treze” é ignorado. “João” sem ordinal é o Evangelho.",
      "<b>A passagem precisa existir.</b> “João quarenta e cinco” é ignorado, porque João tem 21 capítulos.",
      "<b>A palavra “um”.</b> Sozinha depois do livro, é tomada como artigo (“Lucas era um médico”). "
      "Diga “Gênesis capítulo um” ou “Gênesis um um”.")
historia.append(PageBreak())
h2("Continuar na mesma passagem")
p("Depois de uma referência, o preletor não precisa repetir o livro:")
itens("“<b>versículo</b> dezessete” muda para o versículo 17 do mesmo capítulo;",
      "“<b>capítulo</b> quatro” muda para o capítulo 4 do mesmo livro.")
p("Nesses casos as palavras “capítulo” e “versículo” são obrigatórias. Um número solto não vale.")
h2("O que ainda não é entendido")
itens("O número antes do livro: “capítulo três de João”.",
      "Versículos separados: “versículos três e cinco” (o aplicativo fica com o primeiro).",
      "Referências por descrição, sem o nome do livro: “a parábola do filho pródigo”.")
atencao("Se o motor de fala não entender o nome de um livro, e o preletor disser em seguida "
        "“capítulo treze, versículo quatro”, o aplicativo aplica esses números ao livro citado "
        "antes. O operador deve conferir a seleção quando o preletor muda de livro.")

# ---------------------------------------------------------------- 9
h1("9. Os motores de fala")
p("O campo <b>Motor de fala</b> oferece três opções. Você pode trocar a qualquer momento; a troca "
  "leva alguns segundos.")
tabela(["Motor", "Precisão no teste", "Memória", "Observações"], [
    ["sherpa-onnx (recomendado)", "26 de 26 frases", "cerca de 310 MB",
     "Reconhece todos os livros. Leva uns 5 segundos para carregar ao abrir."],
    ["Vosk", "21 de 26 frases", "cerca de 175 MB",
     "Carrega em 1 segundo, mas não reconhece 19 livros (lista abaixo)."],
    ["Windows", "não testado em português", "cerca de 60 MB",
     "Usa o reconhecimento do próprio Windows. Exige o pacote de fala em português e só ouve "
     "o microfone padrão do sistema."],
], [0.25, 0.2, 0.17, 0.38])
caixa("Sobre os números.", "O teste usou 26 frases gravadas com voz sintética, limpa e sem ruído. "
      "Com um preletor de verdade, eco e ruído de fundo, o acerto será menor. Use os números para "
      "comparar os motores entre si, não como garantia.")
h2("Livros que o Vosk não reconhece")
p("O modelo de português do Vosk não conhece estes nomes: Deuteronômio, Esdras, Neemias, Oseias, "
  "Amós, Obadias, Miqueias, Naum, Habacuque, Sofonias, Ageu, 1 e 2 Coríntios, Efésios, Filipenses, "
  "Colossenses, 1 e 2 Tessalonicenses e Filemom. Se a sua igreja cita esses livros, use o sherpa-onnx.")
h2("Para usar o motor Windows")
passos("Abra <b>Configurações &gt; Hora e idioma &gt; Idioma e região</b>.",
       "Em <b>Português (Brasil)</b>, clique nos três pontos e em <b>Opções de idioma</b>.",
       "Instale o item <b>Fala</b> (reconhecimento de fala).",
       "Em <b>Configurações &gt; Sistema &gt; Som</b>, escolha como entrada padrão o microfone do preletor.",
       "No Escriba, escolha o motor <b>Windows</b>.")
p("Sem o pacote de fala, a linha de estado mostra “Instale a fala em português (Brasil) no Windows”.")

# ---------------------------------------------------------------- 10
h1("10. Primeiro teste, passo a passo")
p("Faça este teste com calma, fora do horário do culto.")
passos("Abra o Holyrics e deixe a janela da Bíblia à vista.",
       "No computador com Windows, abra o Escriba pelo atalho da área de trabalho.",
       "Em <b>Microfone</b>, escolha a entrada por onde chega a voz do preletor.",
       "Preencha <b>IP</b>, <b>Porta</b> e <b>Token</b> com os dados do capítulo 3.",
       "Escolha o modo <b>Livro, capítulo e versículo</b>.",
       f"Espere a linha de estado mostrar {c('Ouvindo (sherpa-onnx)')}.",
       "Fale ao microfone, em ritmo normal: “João três dezesseis”.",
       "Confira a linha <b>Ouvido</b>: ela deve mostrar o que você disse.",
       f"Confira a linha de envio: ela deve mostrar {c('Selecionado: João 3:16')}.",
       "Confira no Holyrics: João 3:16 deve estar selecionado na janela da Bíblia.",
       "Repita com outras passagens, incluindo livros com número (“Primeira aos Coríntios treze”).",
       "Desligue e religue o microfone ou a interface de áudio. Em alguns segundos o estado deve "
       f"voltar a {c('Ouvindo')} sozinho.")
caixa("Se algum passo falhar,", "procure a mensagem no capítulo 12.")

# ---------------------------------------------------------------- 11
h1("11. Uso no dia a dia")
itens("Abra o Escriba antes do culto. Ele pode ficar minimizado; não feche a janela.",
      "Digite o <b>texto principal</b> do sermão do dia, ou apague o campo se não for usar.",
      "O Holyrics precisa estar aberto, com o API Server ligado, no mesmo IP de sempre.",
      "Se o microfone estiver desligado quando o aplicativo abrir, ele espera: fica tentando a "
      "cada 5 segundos e começa a ouvir assim que o microfone aparecer.",
      "Para parar de ouvir sem fechar o programa, escolha o modo <b>Desativado</b>.",
      "A mesma referência dita duas vezes seguidas é enviada uma vez só.")
h2("Abrir junto com o Windows")
passos(f"Pressione <b>Windows + R</b>, digite {c('shell:startup')} e pressione Enter. Uma pasta se abre.",
       "Copie para essa pasta o atalho <b>Escriba</b> da área de trabalho.")
p("A partir daí o aplicativo abre sozinho quando o computador liga.")

# ---------------------------------------------------------------- 12
h1("12. Problemas e soluções")
tabela(["O que aparece", "Causa provável", "O que fazer"], [
    ["Erro: microfone “…” não encontrado. Tentando de novo…",
     "O microfone escolhido está desligado ou desconectado.",
     "Reconecte o microfone; o aplicativo retoma sozinho. Se trocou de equipamento, "
     "escolha o novo."],
    ["Estado “Ouvindo”, mas a linha “Ouvido” não muda",
     "O áudio não está chegando: microfone errado, mudo, ou bloqueado pelo Windows.",
     "Confira o microfone escolhido e o volume de entrada em Configurações &gt; Sistema &gt; Som. Em "
     "Configurações &gt; Privacidade e segurança &gt; Microfone, permita o acesso de aplicativos da área de trabalho."],
    ["O texto em “Ouvido” sai muito diferente do que foi dito",
     "Áudio ruim (eco, ruído, volume baixo ou estourado) ou motor menos preciso.",
     "Use o motor sherpa-onnx. Melhore o sinal: prefira uma saída da mesa só com a voz."],
    ["…: falta o IP do Holyrics", "O campo IP está vazio.", "Preencha o IP do computador do Holyrics."],
    ["Falhou (…): … timed out", "O computador do Holyrics não respondeu.",
     "Confira se ele está ligado, na mesma rede, e se o IP não mudou. Confira o firewall."],
    ["Falhou (…): … 10061 … recusou",
     "O computador respondeu, mas o API Server não está ouvindo naquela porta.",
     "Abra o Holyrics, ligue o API Server e confira a porta."],
    ["Falhou (…): invalid token", "O token digitado não confere.",
     "Copie de novo o token do Holyrics, sem espaços."],
    ["Falhou (…): … 401 … ou menção a permissão", "O token não tem permissão para a ação.",
     "No Holyrics, marque SelectVerse e ShowVerse para o token, na rede local."],
    ["Selecionado: …, mas nada muda no Holyrics",
     "A janela da Bíblia pode estar fechada, ou a versão é antiga.",
     "Abra a janela da Bíblia no Holyrics. Confira se a versão é 2.21 ou mais nova."],
    ["O versículo selecionado é de outro livro", "O motor não entendeu o nome do livro (capítulo 8).",
     "Corrija à mão no Holyrics. Se acontecer sempre com o mesmo livro no Vosk, troque para o sherpa-onnx."],
    ["Erro: Instale a fala em português (Brasil) no Windows",
     "Motor Windows escolhido sem o pacote de fala.", "Siga os passos do capítulo 9 ou use outro motor."],
    ["“não entendi” ao lado do texto principal",
     "Falta um livro e um capítulo que o aplicativo reconheça.",
     "Escreva o nome do livro por extenso, seguido do capítulo: “2 Coríntios 4:1”."],
    ["O Holyrics volta para uma passagem de outro culto",
     "O texto principal ficou salvo do sermão anterior.",
     "Digite o texto de hoje ou apague o campo."],
    ["Transcrição não gravada: …",
     "A pasta sumiu ou não aceita gravação.",
     "Escolha outra pasta no botão Escolher…"],
    ["O programa não abre, ou o antivírus o bloqueia",
     "Programas sem assinatura digital às vezes são barrados.",
     "Libere a pasta C:\\Escriba no antivírus e instale de novo."],
], [0.3, 0.3, 0.4])

# ---------------------------------------------------------------- 13
h1("13. Limitações e informações técnicas")
h2("O que foi e o que não foi testado")
itens("<b>Testado:</b> o reconhecimento com voz sintética em português; a detecção de referências "
      "(54 testes automáticos); o envio dos comandos, a volta ao texto principal e a transcrição "
      "com um servidor que imita o Holyrics; o instalador e o desinstalador em um computador com "
      "Windows 11; um primeiro uso real da seleção de versículos com o Holyrics.",
      "<b>Não testado:</b> a volta ao texto principal e a transcrição em um culto de verdade; "
      "o motor Windows em português. Por isso o primeiro teste do capítulo 10 é indispensável.")
h2("Pastas e arquivos")
tabela(["Item", "Local"], [
    ["Programa", c("C:\\Escriba")],
    ["Configurações", c("%APPDATA%\\Escriba\\config.json")],
    ["Modelos de fala", c("C:\\Escriba\\_internal\\modelos")],
    ["Transcrições", "A pasta escolhida na janela; um arquivo " + c("Transcrição AAAA-MM-DD.txt") + " por dia"],
], [0.3, 0.7])
atencao("O token do Holyrics fica gravado sem criptografia no arquivo de configurações. Ele só dá "
        "acesso às ações que você marcou, e apenas dentro da sua rede.")
h2("O que trafega na rede")
p(f"O aplicativo envia pedidos HTTP ao endereço {c('http://IP:porta/api/SelectVerse')} (selecionar) e "
  f"{c('…/api/ShowVerse')} (projetar), com o token e o código do versículo. Nenhum áudio e nenhum texto "
  "do sermão saem do computador; o reconhecimento é todo local e funciona sem internet. A "
  "transcrição, se ligada, é gravada apenas na pasta que você escolheu.")
h2("Licenças dos modelos de fala")
itens("Vosk, modelo vosk-model-small-pt-0.3: licença Apache 2.0 (alphacephei.com/vosk).",
      "Kroko ASR, modelo comunitário de português usado pelo sherpa-onnx: licença CC-BY-SA "
      "(huggingface.co/Banafo/Kroko-ASR).")

# ---------------------------------------------------------------- montagem
quadro = Frame(2.2 * cm, 2.2 * cm, LARGURA, A4[1] - 4.4 * cm, id="quadro", leftPadding=0,
               rightPadding=0, topPadding=0, bottomPadding=0)
doc = Manual(str(SAIDA), pagesize=A4, title="Escriba - Manual de instruções",
             author="Escriba", subject="Instalação, configuração e uso")
doc.addPageTemplates([PageTemplate(id="capa", frames=[quadro], onPage=capa),
                      PageTemplate(id="normal", frames=[quadro], onPage=rodape)])
doc.multiBuild(historia)
print(SAIDA)
