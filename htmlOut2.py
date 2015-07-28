#!/bin/python

# HTML Output is based on Fountain Sample Code (in Objective-C)
# https://github.com/nyousefi/Fountain/blob/master/Fountain/FNPaginator.m



import fparser
from outGeneral import *


def htmlTitlePage(parse):
    html = "<div id='script-title'>\n"

    if "title" in parse.titlePage:
        title = "<br />".join(parse.titlePage["title"]) + "<br />"
        html = html + "<p class='title'>"+title+"</p>\n"
    else:
        html = html + "<p class='title'>Untitled</p>\n"

    if "credit" in parse.titlePage or "authors" in parse.titlePage:
        if "credit" in parse.titlePage:
            credit = "<br />".join(parse.titlePage["credit"]) + "<br />"
            html = html + "<p class='credit'>"+credit+"</p>\n"
        else:
            html = html + "<p class='credit'>written by</p>\n"
        if "authors" in parse.titlePage:
            authors = "<br />".join(parse.titlePage["authors"]) + "<br />"
            html = html + "<p class='authors'>"+authors+"</p>\n"
        else:
            html = html + "<p class='authors'>Anonymous</p>\n"

    if "source" in parse.titlePage:
        source = "<br />".join(parse.titlePage["source"]) + "<br />"
        html = html + "<p class='source'>"+source+"</p>\n"

    if "draft date" in parse.titlePage:
        dd = "<br />".join(parse.titlePage["draft date"]) + "<br />"
        html = html + "<p class='draft date'>"+dd+"</p>\n"

    if "contact" in parse.titlePage:
        contact = "<br />".join(parse.titlePage["contact"]) + "<br />"
        html = html + "<p class='contact'>"+contact+"</p>\n"

    if "notes" in parse.titlePage:
        notes = "<br />".join(parse.titlePage["notes"]) + "<br />"
        html = html + "<p class='notes'>"+notes+"</p>\n"

    if "copyright" in parse.titlePage:
        copyright = "<br />".join(parse.titlePage["copyright"]) + "<br />"
        html = html + "<p class='copyright'>"+copyright+"</p>\n"

    html = html + "</div>\n"
    print(parse.titlePage)
    return html

def processHTMLLine(type, text):

    text = re.sub("("+CHAR_BOLDITALUNDER+")([^/]+)(/"+CHAR_BOLDITALUNDER+")", r"<strong><em><u>\2</u></em></strong>", text)
    text = re.sub("("+CHAR_BOLDITAL+")([^/]+)(/"+CHAR_BOLDITAL+")", r"<strong><em>\2</em></strong>", text)
    text = re.sub("("+CHAR_BOLDUNDER+")([^/]+)(/"+CHAR_BOLDUNDER+")", r"<strong><u>\2</u></strong>", text)
    text = re.sub("("+CHAR_ITALUNDER+")([^/]+)(/"+CHAR_ITALUNDER+")", r"<em><u>\2</u></em>", text)
    text = re.sub("("+CHAR_BOLD+")([^/]+)(/"+CHAR_BOLD+")", r"<strong>\2</strong>", text)
    text = re.sub("("+CHAR_ITAL+")([^/]+)(/"+CHAR_ITAL+")", r"<em>\2</em>", text)
    text = re.sub("("+CHAR_UNDER+")([^/]+)(/"+CHAR_UNDER+")", r"<u>\2</u>", text)

    text = re.sub("("+CHAR_COMMENT+")([^/]+)(/"+CHAR_COMMENT+")", r'<u><span style="background-color:#FAFAD2;">\2</span></u>', text)

    html = ""
    if text != "":
        html = html + "<span class='"
        html = html + type.lower().replace(" ","-")
        html = html + "'>" + text + "</span>\n"

    html = html + "<br />"

    return html

def htmlBody(parse, enableComments):
    html = ""
    page = Page()
    font = Font()
    page.textLines = 43
    font.charsPerInch = 9

    pgs = splitScriptText(parse, page, font, enableComments)

    if len(parse.titlePage) > 0:
        html = html + htmlTitlePage(parse)
        html = html + "<p class='page-break'></p>\n"

    for pgno in range(0, len(pgs)):

        if pgno > 0:
            html = html + "<br /><br />\n"

        for e in pgs[pgno]:
            html = html + processHTMLLine(e[0], e[1])

        # Strip off last <br />
        #if len(pgs[pgno]) > 0:
        #    html = html[:-6]

    return html



def htmlout(parse, enableComments):

    cssDir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"

    htmlText = ""
    htmlText = htmlText + "<!DOCTYPE html>\n"
    htmlText = htmlText + "<html>\n"
    htmlText = htmlText + "<head>\n"
    htmlText = htmlText + "<style type='text/css'>\n"
    htmlText = htmlText + open(cssDir+"ScriptCSS.css", "r", encoding="utf-8").read()
    htmlText = htmlText + "</style>\n"
    htmlText = htmlText + "</head>\n"
    htmlText = htmlText + "<body><div width='100%'>\n"
    htmlText = htmlText + htmlBody(parse, enableComments)
    htmlText = htmlText + "</div></body>\n"
    htmlText = htmlText + "</html>"
    #print(htmlText)
    return htmlText


s = sys.argv[1]

enableComments = False
if "comments" in sys.argv:
    enableComments = True

parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
html = htmlout(parse, enableComments)

fl = open(s+".html", "w")
fl.write(html)
fl.close()

#characterCards(parse.elms)
