#!/bin/python

# HTML Output is based on Fountain Sample Code (in Objective-C)
# https://github.com/nyousefi/Fountain/blob/master/Fountain/FNPaginator.m



import parser
import sys
import re
import textwrap
import math
import os
import copy

class Font:
    def __init__(self):
        self.name = "Courier"
        self.pointsize = 12
        self.heightEM = 1.2
        self.lineHeight = (self.pointsize*self.heightEM)
        self.charsPerInch = 10

class Page:
    def __init__(self):
        self.name = "Letter"
        self.width = 8.5
        self.height = 11
        self.marginTop = 1
        self.marginBottom = 1
        self.marginRight = 1
        self.marginLeft = 1

    def usableHeight(self):
        return (self.height - self.marginTop - self.marginBottom)*72.0


def inchesForElement(elm):
    if elm.elmType == "Action" or elm.elmType == "General" or elm.elmType == "Scene Heading":
        return 6
    if elm.elmType == "Character" or elm.elmType == "Dialogue":
        return 3.3
    if elm.elmType == "Parenthetical":
        return 2
    if elm.elmType == "Transition":
        return 1.5
    return 0

def inchesForLeftMargin(elm):
    if elm.elmType == "Action" or elm.elmType == "General" or elm.elmType == "Scene Heading":
        return 1.5
    if elm.elmType == "Character":
        return 4.2
    if elm.elmType == "Dialogue":
        return 2.9
    if elm.elmType == "Parenthetical":
        return 3.6
    if elm.elmType == "Transition":
        return 6

def ptHeightForString(text, font, maxInches):
    maxchars = math.floor(maxInches * font.charsPerInch)
    if maxchars <= 0:
        return 0
    s = textwrap.wrap(text, maxchars)
    return len(s) * font.lineHeight

def ptBeforeElement(elm, font):
    s = set(["Action", "General", "Character", "Transition"])
    if elm.elmType == "Scene Heading":
        return 2*font.lineHeight
    if elm.elmType in s:
        return 1*font.lineHeight
    return 0


def split(elms):

    page = Page()
    font = Font()

    peTmp = []
    pe = []
    pages = []

    ypos = 0
    blockHeight = 0

    previousDualDialogueBlockHeight = -1

    ie = -1
    while ie in range(-1, len(elms)-1):
        ie = ie + 1
        e = elms[ie]

        if len(pages) == 72 and e.elmText == "EDWARD (CONT'D)":
            print(e.elmText + " elm " + str(len(pe)))
            print(str(ypos))

        if e.elmType == "Page Break":
            for x in peTmp:
                pe.append(x)
            peTmp = []

            pe.append(e)
            pages.append(pe)

            pe = []
            ypos = 0
            continue

        spaceBefore = ptBeforeElement(e, font)
        elmWidth = inchesForElement(e)
        elmHeight = ptHeightForString(e.elmText, font, elmWidth)

        if elmHeight <= 0:
            continue

        blockHeight = blockHeight + elmHeight
        #if len(pe) > 0: # Need spacing first
        blockHeight = blockHeight + spaceBefore

        if e.elmType == "Scene Heading" and ie+1 < len(elms):
            enext = elms[ie+1]
            nextWidth = inchesForElement(enext)
            nextHeight = ptHeightForString(enext.elmText, font, nextWidth)
            nextHeight = nextHeight + ptBeforeElement(enext, font)

            if blockHeight + ypos + nextHeight >= page.usableHeight() and nextHeight >= font.lineHeight:
                peTmp.append(parser.newElmPageBreak(""))

            peTmp.append(e)
            continue
        if e.elmType == "Character" and ie+1 < len(elms):
            s = set(["Dialogue", "Parenthetical"])
            j = ie
            enext = e
            while ie == j or (j < len(elms) and enext.elmType in s):
                peTmp.append(enext)
                blockHeight = blockHeight + ptHeightForString(enext.elmText, font, inchesForElement(enext))
                blockHeight = blockHeight + ptBeforeElement(enext, font)
                j = j + 1
                enext = elms[j]
            ie = j - 1

            if e.dualDlg and previousDualDialogueBlockHeight < 0:
                previousDualDialogueBlockHeight = blockHeight;
            elif e.dualDlg:
                blockHeight = abs(previousDualDialogueBlockHeight - blockHeight)
                previousDualDialogueBlockHeight = -1
        else:
            peTmp.append(e)

        totalHeightInUse = blockHeight + ypos

        if totalHeightInUse <= page.usableHeight(): # All is good
            ypos = ypos + blockHeight
        else:
            if len(peTmp) > 0 and peTmp[0].elmType == "Character" and totalHeightInUse - page.usableHeight() >= font.lineHeight * 4:
                bi = -1
                maxTmpElements = len(peTmp)
                partialHeight = 0
                pageOverflow  = totalHeightInUse - page.usableHeight()

                while partialHeight < pageOverflow and bi < maxTmpElements - 1:
                    bi = bi + 1
                    h  = ptHeightForString(peTmp[bi].elmText, font, inchesForElement(peTmp[bi]))
                    s  = ptBeforeElement(peTmp[bi], font)
                    if len(pages) == 72 and e.elmText == "EDWARD (CONT'D)":
                        print("BI / "+str(bi)+" h: "+str(h)+" s: "+str(s))
                    partialHeight += h + s;

                if len(pages) == 72 and e.elmText == "EDWARD (CONT'D)":
                    print(pageOverflow)
                    print(bi)

                if bi > 0: # We have an element which we may be able to squeze in
                    spiller = peTmp[bi]
                    if spiller.elmType == "Parenthetical":
                        if bi > 1:
                            for z in range(0, bi):
                                pe.append(peTmp[z])

                            # Add (MORE) note
                            pe.append(parser.newElmCharacter("(MORE)"))

                            # Close page
                            pages.append(pe)
                            pe = []
                            blockHeight = 0

                            # Continue on next page
                            characterCueElm = copy.copy(peTmp[0])
                            characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                            blockHeight = blockHeight + ptHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                            blockHeight = blockHeight + ptBeforeElement(characterCueElm, font)
                            pe.append(characterCueElm)

                            # Remaining temp Elements
                            for z in range(bi, maxTmpElements):
                                pe.append(peTmp[z])
                                blockHeight = blockHeight + ptHeightForString(peTmp[z].elmText, font, inchesForElement(peTmp[z]))
                                blockHeight = blockHeight + ptBeforeElement(peTmp[z], font)
                            ypos = blockHeight
                            peTmp = []
                    else:
                        distanceToBottom  = page.usableHeight() - ypos - (font.lineHeight * 2)
                        if distanceToBottom < font.lineHeight * 5: # Don't bother - not enough lines left
                            pages.append(pe)
                            pe = []
                            ypos = blockHeight - spaceBefore;
                            blockHeight = 0
                            continue

                        heightBeforeDialogue = 0
                        for z in range(0, bi):
                            heightBeforeDialogue = heightBeforeDialogue + ptBeforeElement(peTmp[z], font)
                            heightBeforeDialogue = heightBeforeDialogue + ptHeightForString(peTmp[z].elmText, font, inchesForElement(peTmp[z]))
                        dialogueHeight = heightBeforeDialogue
                        sentenceIndex = -1
                        sentences = [m.group(1) for m in re.finditer("(.+?[\\.\\?\\!]+\\s*)", spiller.elmText) if m]
                        maxSentences = len(sentences)

                        dialogueBeforeBreak = ""
                        while dialogueHeight < distanceToBottom and sentenceIndex < maxSentences - 1:
                            sentenceIndex = sentenceIndex + 1
                            text = dialogueBeforeBreak + sentences[sentenceIndex]
                            dialogueHeight = ptHeightForString(text, font, inchesForElement(peTmp[bi]))
                            dialogueHeight = dialogueHeight + ptBeforeElement(parser.newElmDialogue(text), font)

                            if dialogueHeight < distanceToBottom:
                                dialogueBeforeBreak = dialogueBeforeBreak + sentences[sentenceIndex]

                        # Break sentences up
                        preBreakDialogue = parser.newElmDialogue(dialogueBeforeBreak)
                        if preBreakDialogue.elmText == "":
                            pages.append(pe)
                            pe = []
                            for z in range(1, bi):
                                pe.append(peTmp[z])
                        else:
                            for z in range(0, bi):
                                pe.append(peTmp[z])

                            # Add Dialog & (MORE) note
                            pe.append(preBreakDialogue)
                            pe.append(parser.newElmCharacter("(MORE)"))

                            # Close page
                            pages.append(pe)
                            pe = []

                        # Finish page, and start next
                        blockHeight = 0
                        characterCueElm = copy.copy(peTmp[0])
                        characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                        blockHeight = blockHeight + ptHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                        blockHeight = blockHeight + ptBeforeElement(characterCueElm, font)
                        pe.append(characterCueElm)

                        # Add remaining sentences
                        if sentenceIndex < 0:
                            sentenceIndex = 0
                        dialogueAfterBreak = ""
                        for z in range(sentenceIndex, maxSentences):
                            dialogueAfterBreak = dialogueAfterBreak + sentences[z]
                        postBreakDialogue = parser.newElmDialogue(dialogueAfterBreak)
                        pe.append(postBreakDialogue)
                        blockHeight = blockHeight + ptBeforeElement(postBreakDialogue, font)
                        blockHeight = blockHeight + ptHeightForString(postBreakDialogue.elmText, font, inchesForElement(postBreakDialogue))

                        # Remaining temp Elements
                        for z in range(bi+1, maxTmpElements):
                            pe.append(peTmp[z])
                            blockHeight = blockHeight + ptBeforeElement(peTmp[z], font)
                            blockHeight = blockHeight + ptHeightForString(peTmp[z].elmText, font, inchesForElement(peTmp[z]))
                        ypos = blockHeight
                        peTmp = []

                else: # Nothing else can fit
                    pages.append(pe)
                    pe = []
                    ypos = blockHeight - spaceBefore;
            else:
                pages.append(pe)
                pe = []
                ypos = blockHeight - spaceBefore;
                blockHeight = 0

        blockHeight = 0
        for x in peTmp:
            pe.append(x)
        peTmp = []

    for x in peTmp:
        pe.append(x)

    if len(pe) > 0:
        pages.append(pe)

    return pages

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

    html = html + "</div>\n"
    return html

def htmlBody(parse, pages):
    html = ""
    if len(parse.titlePage) > 0:
        html = html + htmlTitlePage(parse)

    dialogueTypes = set(["Character", "Dialogue", "Parenthetical"]);
    ignoringTypes = set(["Boneyard", "Comment", "Synopsis", "Section Heading"])
    dualDialogueCharacterCount = 0
    maxPages = len(pages)

    for pi in range(0, maxPages):
        html = html + "<p class='page-break'>"+str(pi+1)+".</p>\n"

        for elm in pages[pi]:
            if elm.elmType in ignoringTypes:
                continue

            if elm.elmType == "Page Break":
                html = html + "</section>\n<section>\n"
                continue

            if elm.elmType == "Character" and elm.dualDlg:
                dualDialogueCharacterCount = dualDialogueCharacterCount + 1
                if dualDialogueCharacterCount == 1:
                    html = html + "<div class='dual-dialogue'>\n"
                    html = html + "<div class='dual-dialogue-left'>\n"
                else:
                    html = html + "</div>\n<div class='dual-dialogue-right'>\n"
            if dualDialogueCharacterCount >= 2 and not elm.elmType in dialogueTypes:
                dualDialogueCharacterCount = 0
                html = html + "</div>\n</div>\n"

            text = ""
            if elm.elmType == "Scene Heading" and elm.sceneNo >= 0:
                text = text + "<span class='scene-number-left'>"+str(elm.sceneNo)+"</span>"
                text = text + elm.elmText
                text = text + "<span class='scene-number-right'>"+str(elm.sceneNo)+"</span>"
            else:
                text = text + elm.elmText

            if elm.elmType == "Character" and elm.dualDlg:
                text = text.replace("^", "")
            if elm.elmType == "Character":
                text = re.sub("^@", "", text) # Remove starting hash

            if elm.elmType == "Scene Heading":
                text = re.sub("^\\.", "", text) # Remove starting dot

            if elm.elmType == "Lyrics":
                text = re.sub("^~", "", text) # Remove starting ~

            if elm.elmType == "Action":
                text = re.sub("^\\!", "", text) # Remove starting bang

            text = re.sub(parse.PATTERN_BOLD_ITALIC_UNDERLINE, "<strong><em><u>\2</strong></em></u>", text)
            text = re.sub(parse.PATTERN_BOLD_ITALIC, "<strong><em>\2</strong></em>", text)
            text = re.sub(parse.PATTERN_BOLD_UNDERLINE, "<strong><u>\2</strong></u>", text)
            text = re.sub(parse.PATTERN_ITALIC_UNDERLINE, "<em><u>\2</em></u>", text)
            text = re.sub(parse.PATTERN_BOLD, "<strong>\2</strong>", text)
            text = re.sub(parse.PATTERN_ITALIC, "<em>\2</em>", text)
            text = re.sub(parse.PATTERN_UNDERLINE, "<u>\2</u>", text)

            # Strip comments [[...]]
            text = re.sub("\\[{2}(.*?)\\]{2}", "", text)

            if text != "":
                html = html + "<p class='"
                html = html + elm.elmType.lower().replace(" ","-")
                if elm.centered:
                    html = html + " center"
                html = html + "'>" + text + "</p>\n"


    return html

def htmlout(parse):

    cssDir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"

    pages = split(parse.elms)
    htmlText = ""
    htmlText = htmlText + "<!DOCTYPE html>\n"
    htmlText = htmlText + "<html>\n"
    htmlText = htmlText + "<head>\n"
    htmlText = htmlText + "<style type='text/css'>\n"
    htmlText = htmlText + open(cssDir+"ScriptCSS.css", "r", encoding="utf-8").read()
    htmlText = htmlText + "</style>\n"
    htmlText = htmlText + "</head>\n"
    htmlText = htmlText + "<body>\n<div width='100%'><article>\n<section>\n"
    htmlText = htmlText + htmlBody(parse, pages)
    htmlText = htmlText + "</section>\n</div></article>\n</body>\n"
    htmlText = htmlText + "</html>"
    #print(htmlText)
    return htmlText




s = sys.argv[1]
parse = parser.FParser(open(s, "r", encoding="utf-8").read())
html = htmlout(parse)

fl = open(s+".html", "w")
fl.write(html)
fl.close()

#characterCards(parse.elms)
