#!/bin/python

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
import fparser
from outGeneral import *
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import Paragraph
from  reportlab.lib.styles import ParagraphStyle



fontDir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
pdfmetrics.registerFont(TTFont('CourierPrime', fontDir+'CourierPrime.ttf'))
pdfmetrics.registerFont(TTFont('CourierPrimeB', fontDir+'CourierPrimeBold.ttf'))
pdfmetrics.registerFont(TTFont('CourierPrimeI', fontDir+'CourierPrimeItalic.ttf'))
pdfmetrics.registerFont(TTFont('CourierPrimeBI', fontDir+'CourierPrimeBoldItalic.ttf'))

pstyle = ParagraphStyle('Normal')
pstyle.textColor = 'black'
pstyle.fontSize = 12
pstyle.fontName = "CourierPrime"

pstyleCenter = ParagraphStyle('Center')
pstyleCenter.textColor = 'black'
pstyleCenter.alignment = TA_CENTER
pstyleCenter.fontSize = 12
pstyleCenter.fontName = "CourierPrime"

pstyleRight = ParagraphStyle('Right')
pstyleRight.textColor = 'black'
pstyleRight.alignment = TA_RIGHT
pstyleRight.fontSize = 12
pstyleRight.fontName = "CourierPrime"


def drawMultiString(canvas, x, y, s):
    for ln in s.split('\n'):
        canvas.drawString(x, y, ln)
        y -= canvas._leading
    return y
def drawMultiStringRight(canvas, x, y, s):
    for ln in s.split('\n'):
        canvas.drawRightString(x, y, ln)
        y -= canvas._leading
    return y
def drawMultiStringCentred(canvas, x, y, s):
    for ln in s.split('\n'):
        canvas.drawCentredString(x, y, ln)
        y -= canvas._leading
    return y

def pdfTitlePage(canvas, parse, page, font):
    ypos = 9*inch
    if "title" in parse.titlePage:
        ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["title"]))
    else:
        ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "Untitled")
    ypos = ypos - 2 * font.lineHeight*font.heightEM

    if "credit" in parse.titlePage or "authors" in parse.titlePage:
        if "credit" in parse.titlePage:
            ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["credit"]))
        else:
            ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "written by")
        ypos = ypos - 0.5 * font.lineHeight*font.heightEM
        if "authors" in parse.titlePage:
            ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["authors"]))
        else:
            ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["Anonymous"]))
        ypos = ypos - 2 * font.lineHeight*font.heightEM

    if "source" in parse.titlePage:
        ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["source"]))
        ypos = ypos - 2 * font.lineHeight*font.heightEM

    if "draft date" in parse.titlePage:
        ypos = drawMultiStringCentred(canvas, page.width*0.5*inch, ypos, "\n".join(parse.titlePage["draft date"]))
        ypos = ypos - 2 * font.lineHeight*font.heightEM


    if "copyright" in parse.titlePage:
        ypos = ypos - 3 * font.lineHeight*font.heightEM
        ypos = drawMultiString(canvas, page.marginLeft*inch, ypos, "\n".join(parse.titlePage["copyright"]))

    contactPos = 0
    if "contact" in parse.titlePage:
        contactPos = page.marginBottom*inch + font.lineHeight*font.heightEM * len(parse.titlePage["contact"])
        drawMultiString(canvas, page.marginLeft*inch, contactPos, "\n".join(parse.titlePage["contact"]))

    if "notes" in parse.titlePage:
        y = contactPos + (len(parse.titlePage["notes"])+2)*font.lineHeight*font.heightEM
        drawMultiStringRight(canvas, (page.width-page.marginRight) * inch, y, "\n".join(parse.titlePage["notes"]))

def processPDFLine(canvas, type, text, lineno, page, font, width, height):

    text = re.sub("("+CHAR_BOLDITALUNDER+")([^/]+)(/"+CHAR_BOLDITALUNDER+")", r"<font name=CourierPrimeBI size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_BOLDITAL+")([^/]+)(/"+CHAR_BOLDITAL+")", r"<font name=CourierPrimeBI size=12>\2</font>", text)
    text = re.sub("("+CHAR_BOLDUNDER+")([^/]+)(/"+CHAR_BOLDUNDER+")", r"<font name=CourierPrimeB size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_ITALUNDER+")([^/]+)(/"+CHAR_ITALUNDER+")", r"<font name=CourierPrimeI size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_BOLD+")([^/]+)(/"+CHAR_BOLD+")", r"<font name=CourierPrimeB size=12>\2</font>", text)
    text = re.sub("("+CHAR_ITAL+")([^/]+)(/"+CHAR_ITAL+")", r"<font name=CourierPrimeI size=12>\2</font>", text)
    text = re.sub("("+CHAR_UNDER+")([^/]+)(/"+CHAR_UNDER+")", r"<u>\2</u>", text)

    text = re.sub("("+CHAR_COMMENT+")([^/]+)(/"+CHAR_COMMENT+")", r"</para><para bg=#FAFAD2><u>\2</u></para><para>", text)

    elm = fparser.fromTypeTextToElm(type, text)
    marginLeft = leftMarginForElement(elm)
    marginRight = rightMarginForElement(elm)

    # Styling Additions
    if elm.elmType == "Scene Heading":
        text = "<font name=CourierPrimeB size=12>" + text + "</font>"
    if elm.elmType == "Lyrics":
        text = "<font name=CourierPrimeI size=12>" + text + "</font>"
    if elm.elmType == "Comment":
        text = "</para><para bg=#FAFAD2><u>" + text + "</u></para><para>"

    if elm.elmType == "Transition": # right align
        para = Paragraph(text, pstyleRight)
        para.wrapOn(canvas, width, pstyleRight.fontSize*font.heightEM)
        para.drawOn(canvas,-marginRight*inch, height - (lineno+1)*pstyle.fontSize*font.heightEM - page.marginTop*inch)
    else:
        para = Paragraph(text, pstyle)
        para.wrapOn(canvas, width, pstyle.fontSize*font.heightEM)
        para.drawOn(canvas, marginLeft*inch, height - (lineno+1)*pstyle.fontSize*font.heightEM - page.marginTop*inch)





def pdfout(parse, outfl, enableComments):
    c = Canvas(outfl, pagesize=letter)
    width, height = letter
    c.setFont('CourierPrime', 12)

    page = Page()
    font = Font()
    pgs = splitScriptText(parse, page, font, enableComments)

    if len(parse.titlePage) > 0:
        pdfTitlePage(c, parse, page, font)
        c.showPage()

    title = "UNTITLED"
    if "title" in parse.titlePage:
        title = " ".join(parse.titlePage["title"]).upper()

    for pgno in range(0, len(pgs)):
        c.setFont('CourierPrime', 12)
        if pgno > 0:
            c.drawRightString((page.width - page.marginRight) * inch, height - 0.5*inch, str(pgno+1)+".")
            c.drawString(page.marginLeft*inch, height - 0.5*inch, title)

        lineno = 0
        for e in pgs[pgno]:
            processPDFLine(c, e[0], e[1], lineno, page, font, width, height)
            lineno = lineno + 1

        # Strip off last <br />
        #if len(pgs[pgno]) > 0:
        #    html = html[:-6]

        c.showPage()



    c.save()


enableComments = False
if "comments" in sys.argv:
    enableComments = True

s = sys.argv[1]
parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
html = pdfout(parse, s+".pdf", enableComments)
