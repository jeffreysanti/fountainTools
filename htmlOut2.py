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
        #return (self.height - self.marginTop - self.marginBottom)*72.0
        return 45


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

def lineHeightForString(text, font, maxInches):
    maxchars = math.floor(maxInches * font.charsPerInch)
    if maxchars <= 0:
        return 0
    s = textwrap.wrap(text, maxchars)
    return len(s)

def lineBeforeElement(elm, font):
    s = set(["Action", "General", "Character", "Transition"])
    if elm.elmType == "Scene Heading":
        return 2
    if elm.elmType in s:
        return 1
    return 0


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

def processText(elm):
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

    html = ""
    if text != "":
        html = html + "<p class='"
        html = html + elm.elmType.lower().replace(" ","-")
        if elm.centered:
            html = html + " center"
        html = html + "'>" + text + "</p>\n"

    return html

def htmlBody(parse):
    html = ""
    pi = 0
    if len(parse.titlePage) > 0:
        html = html + htmlTitlePage(parse)
        pi = pi + 1
        html = html + "<p class='page-break'>"+str(pi)+".</p>\n"


    dialogueTypes = set(["Character", "Dialogue", "Parenthetical"]);
    ignoringTypes = set(["Boneyard", "Comment", "Synopsis", "Section Heading"])
    dualDialogueCharacterCount = 0

    page = Page()
    font = Font()
    ypos = 0
    elmno = 0
    elms = parse.elms
    previousDualDialogueBlockHeight = -1

    ie = -1
    while ie in range(-1, len(elms)-1):
        ie = ie + 1
        e = elms[ie]

        if e.elmType in ignoringTypes:
            continue

        if e.elmType == "Page Break":
            html = html + "</section>\n<section>\n"
            pi = pi + 1
            elmno = 0
            ypos = 0
            html = html + "<p class='page-break'>"+str(pi)+".</p>\n"
            continue

        if e.elmType == "Character":
            spaceBefore = lineBeforeElement(e, font)
            elmHeight = lineHeightForString(e.elmText, font, inchesForElement(e))
            blockHeight = elmHeight
            if elmno > 0: # Need spacing first
                blockHeight = blockHeight + spaceBefore

            # Add dialog height:
            s = set(["Dialogue", "Parenthetical"])
            j = ie
            enext = e
            queue = []
            while ie == j or (j < len(elms) and enext.elmType in s):
                queue.append(enext)
                blockHeight = blockHeight + lineHeightForString(enext.elmText, font, inchesForElement(enext))
                blockHeight = blockHeight + lineBeforeElement(enext, font)
                j = j + 1
                enext = elms[j]
            ie = j - 1

            if e.dualDlg and previousDualDialogueBlockHeight < 0:
                previousDualDialogueBlockHeight = blockHeight;
            elif e.dualDlg:
                blockHeight = abs(previousDualDialogueBlockHeight - blockHeight)
                previousDualDialogueBlockHeight = -1

            # Now add Elements
            if blockHeight + ypos >= page.usableHeight():
                if ypos + blockHeight - page.usableHeight() >= 4: # At least 4 lines spill over
                    bi = -1
                    maxTmpElements = len(queue)
                    partialHeight = 0
                    pageOverflow  = blockHeight + ypos - page.usableHeight()

                    # Fit as many elements as possible
                    while partialHeight < pageOverflow and bi < maxTmpElements - 1:
                        bi = bi + 1
                        h  = lineHeightForString(queue[bi].elmText, font, inchesForElement(queue[bi]))
                        s  = lineBeforeElement(queue[bi], font)
                        partialHeight += h + s;

                    if bi > 0: # We have an element which we may be able to squeze in
                        spiller = queue[bi]
                        if spiller.elmType == "Parenthetical":
                            if bi > 1:
                                for z in range(0, bi):
                                    html = html + processText(queue[z])

                                # Add (MORE) note without padding before
                                html = html + processText(parser.newElmCharacter("(MORE)"))

                                # Close page
                                html = html + "</section>\n<section>\n"
                                pi = pi + 1
                                ypos = 0
                                blockHeight = 0
                                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                                # Continue on next page
                                characterCueElm = copy.copy(queue[0])
                                characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                                blockHeight = lineHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                                html = html + processText(characterCueElm)
                                elmno = 1

                                # Remaining temp Elements
                                for z in range(bi, maxTmpElements):
                                    padding = lineBeforeElement(queue[z], font)
                                    if elmno > 0 and padding > 0:
                                        blockHeight = blockHeight + padding
                                        for z in range(0, padding):
                                            html = html + "<br class='padding' />\n"
                                    text = processText(te)
                                    html = html + text
                                    elmno = elmno + 1
                                    blockHeight = blockHeight + lineHeightForString(queue[z].elmText, font, inchesForElement(queue[z]))

                                ypos = blockHeight
                            else:
                                # new line
                                html = html + "</section>\n<section>\n"
                                pi = pi + 1
                                elmno = 0
                                ypos = 0
                                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                                # place
                                for te in queue:
                                    padding = lineBeforeElement(te, font)
                                    if elmno > 0 and padding > 0:
                                        for z in range(0, padding):
                                            html = html + "<br class='padding' />\n"
                                    text = processText(te)
                                    html = html + text
                                    elmno = elmno + 1
                                ypos = ypos + blockHeight
                        else:
                            distanceToBottom  = page.usableHeight() - ypos - 2
                            if distanceToBottom < 5: # Don't bother - not enough lines left
                                # new line
                                html = html + "</section>\n<section>\n"
                                pi = pi + 1
                                elmno = 0
                                ypos = 0
                                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                                # place
                                for te in queue:
                                    padding = lineBeforeElement(te, font)
                                    if elmno > 0 and padding > 0:
                                        for z in range(0, padding):
                                            html = html + "<br class='padding' />\n"
                                    text = processText(te)
                                    html = html + text
                                    elmno = elmno + 1
                                ypos = ypos + blockHeight
                                continue

                            heightBeforeDialogue = 0
                            for z in range(0, bi):
                                heightBeforeDialogue = heightBeforeDialogue + lineBeforeElement(queue[z], font)
                                heightBeforeDialogue = heightBeforeDialogue + lineHeightForString(queue[z].elmText, font, inchesForElement(queue[z]))
                            dialogueHeight = heightBeforeDialogue
                            sentenceIndex = -1
                            sentences = [m.group(1) for m in re.finditer("(.+?[\\.\\?\\!]+\\s*)", spiller.elmText) if m]
                            maxSentences = len(sentences)

                            dialogueBeforeBreak = ""
                            while dialogueHeight < distanceToBottom and sentenceIndex < maxSentences - 1:
                                sentenceIndex = sentenceIndex + 1
                                text = dialogueBeforeBreak + sentences[sentenceIndex]
                                dialogueHeight = lineHeightForString(text, font, inchesForElement(queue[bi]))
                                dialogueHeight = dialogueHeight + lineBeforeElement(parser.newElmDialogue(text), font)

                                if dialogueHeight < distanceToBottom:
                                    dialogueBeforeBreak = dialogueBeforeBreak + sentences[sentenceIndex]

                            # Break sentences up
                            preBreakDialogue = parser.newElmDialogue(dialogueBeforeBreak)
                            if preBreakDialogue.elmText == "":
                                # new line
                                html = html + "</section>\n<section>\n"
                                pi = pi + 1
                                elmno = 0
                                ypos = 0
                                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                                # place
                                for te in queue:
                                    padding = lineBeforeElement(te, font)
                                    if elmno > 0 and padding > 0:
                                        for z in range(0, padding):
                                            html = html + "<br class='padding' />\n"
                                    text = processText(te)
                                    html = html + text
                                    elmno = elmno + 1
                                ypos = ypos + blockHeight
                                continue
                            else:
                                for z in range(0, bi):
                                    padding = lineBeforeElement(queue[z], font)
                                    if elmno > 0 and padding > 0:
                                        for z in range(0, padding):
                                            html = html + "<br class='padding' />\n"
                                    text = processText(queue[z])
                                    html = html + text
                                    elmno = elmno + 1

                                # Add Dialog & (MORE) note
                                html = html + processText(preBreakDialogue)
                                html = html + processText(parser.newElmCharacter("(MORE)"))

                                # Close page
                                html = html + "</section>\n<section>\n"
                                pi = pi + 1
                                elmno = 0
                                ypos = 0
                                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                            blockHeight = 0
                            characterCueElm = copy.copy(queue[0])
                            characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                            blockHeight = blockHeight + lineHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                            html = html + processText(characterCueElm)

                            # Add remaining sentences
                            if sentenceIndex < 0:
                                sentenceIndex = 0
                            dialogueAfterBreak = ""
                            for z in range(sentenceIndex, maxSentences):
                                dialogueAfterBreak = dialogueAfterBreak + sentences[z]
                            postBreakDialogue = parser.newElmDialogue(dialogueAfterBreak)
                            html = html + processText(postBreakDialogue)
                            blockHeight = blockHeight + lineBeforeElement(postBreakDialogue, font)
                            blockHeight = blockHeight + lineHeightForString(postBreakDialogue.elmText, font, inchesForElement(postBreakDialogue))

                            # Remaining temp Elements
                            for z in range(bi+1, maxTmpElements):
                                padding = lineBeforeElement(queue[z], font)
                                if elmno > 0 and padding > 0:
                                    for z in range(0, padding):
                                        html = html + "<br class='padding' />\n"
                                text = processText(queue[z])
                                html = html + text
                                elmno = elmno + 1
                                blockHeight = blockHeight + lineBeforeElement(queue[z], font)
                                blockHeight = blockHeight + lineHeightForString(queue[z].elmText, font, inchesForElement(queue[z]))
                            ypos = blockHeight
                    else:
                        # new line
                        html = html + "</section>\n<section>\n"
                        pi = pi + 1
                        elmno = 0
                        ypos = 0
                        html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                        # place
                        for te in queue:
                            padding = lineBeforeElement(te, font)
                            if elmno > 0 and padding > 0:
                                for z in range(0, padding):
                                    html = html + "<br class='padding' />\n"
                            text = processText(te)
                            html = html + text
                            elmno = elmno + 1
                        ypos = ypos + blockHeight
                else:
                    # new line
                    html = html + "</section>\n<section>\n"
                    pi = pi + 1
                    elmno = 0
                    ypos = 0
                    html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                    # place
                    for te in queue:
                        padding = lineBeforeElement(te, font)
                        if elmno > 0 and spaceBefore > 0:
                            for z in range(0, padding):
                                html = html + "<br class='padding' />\n"
                        text = processText(te)
                        html = html + text
                        elmno = elmno + 1
                    ypos = ypos + blockHeight
            else:
                # Safe - place it all :D
                for te in queue:
                    padding = lineBeforeElement(te, font)
                    if elmno > 0 and spaceBefore > 0:
                        for z in range(0, padding):
                            html = html + "<br class='padding' />\n"
                    text = processText(te)
                    html = html + text
                    elmno = elmno + 1
                ypos = ypos + blockHeight
            continue

        # All other types:
        spaceBefore = lineBeforeElement(e, font)
        elmHeight = lineHeightForString(e.elmText, font, inchesForElement(e))
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore


        # Don't want scene heading last entry on page
        if e.elmType == "Scene Heading" and ie+1 < len(elms):
            enext = elms[ie+1]
            nextHeight = lineHeightForString(enext.elmText, font, inchesForElement(enext))
            nextHeight = nextHeight + lineBeforeElement(enext, font)

            if blockHeight + ypos + nextHeight >= page.usableHeight() and nextHeight >= 1:
                html = html + "</section>\n<section>\n"
                pi = pi + 1
                elmno = 0
                ypos = 0
                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"
            elif enext.elmType == "Character" and blockHeight + ypos + nextHeight + 8 >= page.usableHeight():
                html = html + "</section>\n<section>\n"
                pi = pi + 1
                elmno = 0
                ypos = 0
                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

        # Recalculate space required - in case "Scene Heading" changed it
        spaceBefore = lineBeforeElement(e, font)
        elmHeight = lineHeightForString(e.elmText, font, inchesForElement(e))
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore

        # Check if we are overflowing - if so, next page:
        print(str(blockHeight))
        if blockHeight + ypos >= page.usableHeight():
            html = html + "</section>\n<section>\n"
            pi = pi + 1
            elmno = 0
            ypos = 0
            html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

        # Recalculate space required - in case page changed
        spaceBefore = lineBeforeElement(e, font)
        elmHeight = lineHeightForString(e.elmText, font, inchesForElement(e))
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore

        # Padding Before Element:
        if elmno > 0 and spaceBefore > 0:
            for z in range(0, spaceBefore):
                html = html + "<br class='padding' />\n"

        # Now -- The Element
        text = processText(e)
        html = html + text
        ypos = ypos + blockHeight
        elmno = elmno + 1

    return html





'''
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
'''

def htmlout(parse):

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
    htmlText = htmlText + htmlBody(parse)
    htmlText = htmlText + "</div></body>\n"
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
