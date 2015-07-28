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


def processPDFLine(canvas, type, text, lineno, page, font, width, height):

    text = re.sub("("+CHAR_BOLDITALUNDER+")([^/]+)(/"+CHAR_BOLDITALUNDER+")", r"<font name=CourierPrimeBI size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_BOLDITAL+")([^/]+)(/"+CHAR_BOLDITAL+")", r"<font name=CourierPrimeBI size=12>\2</font>", text)
    text = re.sub("("+CHAR_BOLDUNDER+")([^/]+)(/"+CHAR_BOLDUNDER+")", r"<font name=CourierPrimeB size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_ITALUNDER+")([^/]+)(/"+CHAR_ITALUNDER+")", r"<font name=CourierPrimeI size=12><u>\2</u></font>", text)
    text = re.sub("("+CHAR_BOLD+")([^/]+)(/"+CHAR_BOLD+")", r"<font name=CourierPrimeB size=12>\2</font>", text)
    text = re.sub("("+CHAR_ITAL+")([^/]+)(/"+CHAR_ITAL+")", r"<font name=CourierPrimeI size=12>\2</font>", text)
    text = re.sub("("+CHAR_UNDER+")([^/]+)(/"+CHAR_UNDER+")", r"<u>\2</u>", text)

    elm = fparser.fromTypeTextToElm(type, text)
    marginLeft = leftMarginForElement(elm)
    marginRight = rightMarginForElement(elm)

    # Styling Additions
    if elm.elmType == "Scene Heading":
        text = "<font name=CourierPrimeB size=12>" + text + "</font>"

    if elm.elmType == "Transition": # right align
        para = Paragraph(text, pstyleRight)
        para.wrapOn(canvas, width, pstyleRight.fontSize*font.heightEM)
        para.drawOn(canvas,-marginRight*inch, height - (lineno+1)*pstyle.fontSize*font.heightEM - page.marginTop*inch)
    else:
        para = Paragraph(text, pstyle)
        para.wrapOn(canvas, width, pstyle.fontSize*font.heightEM)
        para.drawOn(canvas, marginLeft*inch, height - (lineno+1)*pstyle.fontSize*font.heightEM - page.marginTop*inch)





def pdfout(parse, outfl):
    c = Canvas(outfl, pagesize=letter)
    width, height = letter
    print(str(width))
    c.setFont('CourierPrime', 12)

    if len(parse.titlePage) > 0:
        # TODO: Title Page
        c.showPage()

    page = Page()
    font = Font()
    pgs = splitScriptText(parse, page, font)

    for pgno in range(0, len(pgs)):
        if pgno > 0:
            c.drawRightString((page.width - page.marginRight) * inch, height - 0.5*inch, str(pgno+1)+".")

        lineno = 0
        for e in pgs[pgno]:
            processPDFLine(c, e[0], e[1], lineno, page, font, width, height)
            lineno = lineno + 1

        # Strip off last <br />
        #if len(pgs[pgno]) > 0:
        #    html = html[:-6]

        c.showPage()




    c.showPage()
    c.save()



s = sys.argv[1]
parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
html = pdfout(parse, s+".pdf")
