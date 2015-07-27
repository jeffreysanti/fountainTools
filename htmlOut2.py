#!/bin/python

# HTML Output is based on Fountain Sample Code (in Objective-C)
# https://github.com/nyousefi/Fountain/blob/master/Fountain/FNPaginator.m



import fparser
import sys
import os
import copy

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

    html = html + "</div>\n"
    return html

def processText(elm, font):
    ww = wordWrapString(elm.elmText, font, inchesForElement(elm))
    newElmText = ""
    for w in ww:
        newElmText = newElmText + w + "<br/>"
    newElmText = newElmText[:-5]

    text = ""
    if elm.elmType == "Scene Heading" and elm.sceneNo >= 0:
        text = text + "<span class='scene-number-left'>"+str(elm.sceneNo)+"</span>"
        text = text + newElmText
        text = text + "<span class='scene-number-right'>"+str(elm.sceneNo)+"</span>"
    else:
        text = text + newElmText

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

    text = re.sub(parse.PATTERN_BOLD_ITALIC_UNDERLINE, r"<strong><em><u>\2</strong></em></u>", text)
    text = re.sub(parse.PATTERN_BOLD_ITALIC, r"<strong><em>\2</strong></em>", text)
    text = re.sub(parse.PATTERN_BOLD_UNDERLINE, r"<strong><u>\2</strong></u>", text)
    text = re.sub(parse.PATTERN_ITALIC_UNDERLINE, r"<em><u>\2</em></u>", text)
    text = re.sub(parse.PATTERN_BOLD, r"<strong>\2</strong>", text)
    text = re.sub(parse.PATTERN_ITALIC, r"<em>\2</em>", text)
    text = re.sub(parse.PATTERN_UNDERLINE, r"<u>\2</u>", text)

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

        html = html + "<!-- "+ str(ypos) +" -->"

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

            # Initial character tag
            spaceBefore = lineBeforeElement(e, font)
            elmHeight = lineHeightForString(e.elmText, font, inchesForElement(e))
            blockHeight = elmHeight
            if elmno > 0: # Need spacing first
                blockHeight = blockHeight + spaceBefore

            if ypos + blockHeight + 3 >= page.usableHeight():
                # new page
                html = html + "</section>\n<section>\n"
                pi = pi + 1
                elmno = 0
                ypos = 0
                html = html + "<p class='page-break'>"+str(pi)+".</p>\n"
                blockHeight = elmHeight # First element now

            # Now, add character cue
            if elmno > 0:
                for z in range(0, spaceBefore):
                    html = html + "<br class='padding' />\n"
            text = processText(e, font)
            html = html + text
            ypos = ypos + blockHeight
            elmno = elmno + 1

            # Absord entire cue's contents:
            s = set(["Dialogue", "Parenthetical"])
            j = ie
            enext = e
            queue = []
            while ie == j or (j < len(elms) and enext.elmType in s):
                queue.append(copy.copy(enext))
                j = j + 1
                enext = elms[j]
            ie = j - 1

            dei = 0
            while dei+1 < len(queue):
                dei = dei + 1
                de = queue[dei]
                spaceAvail = page.usableHeight() - ypos

                height_needed = lineHeightForString(de.elmText, font, inchesForElement(de))
                if elmno > 0:
                    height_needed = height_needed + lineBeforeElement(de, font)

                if spaceAvail < 3 or (spaceAvail < 3+height_needed and de.elmType == "Parenthetical"):
                    html = html + processText(parser.newElmCharacter("(MORE)"), font)

                    # new page
                    html = html + "</section>\n<section>\n"
                    pi = pi + 1
                    elmno = 0
                    ypos = 0
                    html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                    # (CONT'D)
                    characterCueElm = copy.copy(queue[0])
                    characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                    ypos = lineHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                    html = html + processText(characterCueElm, font)
                    elmno = 1

                spaceAvail = page.usableHeight() - ypos
                height_needed = lineHeightForString(de.elmText, font, inchesForElement(de))
                if elmno > 0:
                    height_needed = height_needed + lineBeforeElement(de, font)

                if de.elmType == "Parenthetical": # Just Dump It!
                    if elmno > 0:
                        for z in range(0, lineBeforeElement(de, font)):
                            html = html + "<br class='padding' />\n"
                    text = processText(de, font)
                    html = html + text
                    ypos = ypos + height_needed
                    elmno = elmno + 1
                else:
                    isLastElm = (de == queue[:-1])
                    usableLines = spaceAvail - 1
                    if elmno > 0:
                        for z in range(0, lineBeforeElement(de, font)):
                            html = html + "<br class='padding' />\n"
                            usableLines = usableLines - 1

                    # Split by Sentence
                    sentences = [m.group(1) for m in re.finditer("(.+?[\\.\\?\\!]+\\s*)", de.elmText) if m]
                    maxSentences = len(sentences)

                    # Count Sentences We can Fit
                    dialogueBeforeBreak = ""
                    dialogueHeight = 0
                    sentenceIndex = -1
                    while sentenceIndex < maxSentences - 1:
                        sentenceIndex = sentenceIndex + 1
                        text = dialogueBeforeBreak + sentences[sentenceIndex]
                        dialogueHeight = lineHeightForString(text, font, inchesForElement(de))
                        dialogueHeight = dialogueHeight + lineBeforeElement(fparser.newElmDialogue(text), font)

                        if dialogueHeight < usableLines:
                            dialogueBeforeBreak = dialogueBeforeBreak + sentences[sentenceIndex]
                        else:
                            break

                    # Prepare rest of dialog -> we want to redo this element with updated text
                    if sentenceIndex < 0:
                        sentenceIndex = 0
                    dialogueAfterBreak = ""
                    if sentenceIndex < maxSentences - 1:
                        for z in range(sentenceIndex, maxSentences):
                            dialogueAfterBreak = dialogueAfterBreak + sentences[z]
                    queue[dei].elmText = dialogueAfterBreak

                    # Add Dialog:
                    preBreakDialogue = fparser.newElmDialogue(dialogueBeforeBreak)
                    html = html + processText(preBreakDialogue, font)
                    ypos = ypos + lineHeightForString(dialogueBeforeBreak, font, inchesForElement(de))
                    ypos = ypos + lineBeforeElement(preBreakDialogue, font)

                    if queue[dei].elmText != "": # Need to continue this block
                        html = html + processText(fparser.newElmCharacter("(MORE)"), font)

                        # new page
                        html = html + "</section>\n<section>\n"
                        pi = pi + 1
                        elmno = 0
                        ypos = 0
                        html = html + "<p class='page-break'>"+str(pi)+".</p>\n"

                        # (CONT'D)
                        characterCueElm = copy.copy(queue[0])
                        characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                        ypos = lineHeightForString(characterCueElm.elmText, font, inchesForElement(characterCueElm))
                        html = html + processText(characterCueElm, font)
                        elmno = 1

                        dei = dei - 1

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
        text = processText(e, font)
        html = html + text
        ypos = ypos + blockHeight
        elmno = elmno + 1


    # Strip last page added
    #print(html)
    #html = html[:html.rfind("<section>")]

    return html



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
parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
html = htmlout(parse)

fl = open(s+".html", "w")
fl.write(html)
fl.close()

#characterCards(parse.elms)
