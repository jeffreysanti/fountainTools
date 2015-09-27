#!/bin/python

import fparser
import math
import re
import textwrap
import sys
import os
import copy

# *** TODO: Split handle multi-line formatting character codes

CHAR_BOLD = u"\u2BD2"
CHAR_BOLDITAL = u"\u2BD3"
CHAR_BOLDITALUNDER = u"\u2BD4"
CHAR_ITAL = u"\u2BD5"
CHAR_ITALUNDER = u"\u2BD6"
CHAR_BOLDUNDER = u"\u2BD7"
CHAR_UNDER = u"\u2BD8"
CHAR_COMMENT = u"\u2BD9"


class Font:
    def __init__(self):
        self.name = "Courier-New"
        self.pointsize = 12
        self.heightEM = 1.0
        self.lineHeight = (self.pointsize*self.heightEM)
        self.charsPerInch = 10

class Page:
    def __init__(self, name):
        self.name = name
        if self.name == "A4" or self.name == "a4":
            self.name = "A4"
            self.width = 8.3
            self.height = 11.7
            self.marginLeft = 1.5
            self.marginRight = 1
            self.marginTop = 0.7
            self.marginBottom = 0.7
        else:
            self.name = "Letter"
            self.width = 8.5
            self.height = 11
            self.marginLeft = 1.5
            self.marginRight = 1
            self.marginTop = 0.7
            self.marginBottom = 0.7

    def usableHeight(self, font):
        m = math.floor((self.height - self.marginTop - self.marginBottom)*72 / (font.lineHeight * font.heightEM))
        return m


def inchesForElement(elm, page):
    if elm.elmType == "Action" or elm.elmType == "General" or elm.elmType == "Scene Heading" or elm.elmType == "Comment":
        if page.name == "A4":
            return 5.8
        return 6
    if elm.elmType == "Character" or elm.elmType == "Dialogue":
        return 3.3
    if elm.elmType == "Lyrics":
        return 4.3
    if elm.elmType == "Parenthetical":
        return 2
    if elm.elmType == "Transition":
        return 1.5
    return 0

def leftMarginForElement(elm, page):
    if elm.elmType == "Action" or elm.elmType == "General" or elm.elmType == "Scene Heading" or elm.elmType == "Comment":
        return 1.5
    if elm.elmType == "Character":
        return 4.2
    if elm.elmType == "Dialogue":
        return 2.9
    if elm.elmType == "Lyrics":
        return 3.2
    if elm.elmType == "Parenthetical":
        return 3.6
    return 0

def rightMarginForElement(elm, page):
    if elm.elmType == "Transition":
        return 1.5
    return 0

def lineBeforeElement(elm, font):
    s = set(["Action", "General", "Character", "Transition", "Comment"])
    if elm.elmType == "Scene Heading":
        return 2
    if elm.elmType in s:
        return 1
    return 0

def preProcessElmText(elm, enableComments):
    text = elm.elmText

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

    text = re.sub(fparser.PATTERN_BOLD_ITALIC_UNDERLINE, CHAR_BOLDITALUNDER + r"\2/" + CHAR_BOLDITALUNDER, text)
    text = re.sub(fparser.PATTERN_BOLD_ITALIC, CHAR_BOLDITAL + r"\2/" + CHAR_BOLDITAL, text)
    text = re.sub(fparser.PATTERN_BOLD_UNDERLINE, CHAR_BOLDUNDER + r"\2/" + CHAR_BOLDUNDER, text)
    text = re.sub(fparser.PATTERN_ITALIC_UNDERLINE, CHAR_ITALUNDER + r"\2/" + CHAR_ITALUNDER, text)
    text = re.sub(fparser.PATTERN_BOLD, CHAR_BOLD + r"\2/" + CHAR_BOLD, text)
    text = re.sub(fparser.PATTERN_ITALIC, CHAR_ITAL + r"\2/" + CHAR_ITAL, text)
    text = re.sub(fparser.PATTERN_UNDERLINE, CHAR_UNDER + r"\2/" + CHAR_UNDER, text)

    # Strip comments [[...]]
    if enableComments:
        text = re.sub("\\[{2}(.*?)\\]{2}", CHAR_COMMENT + r"{[[ \1 ]]}/" + CHAR_COMMENT, text)
    else:
        text = re.sub("\\[{2}(.*?)\\]{2}", "", text)

    if elm.elmType == "Comment":
        text = "{[[ "+text+" ]]}"

    return text

def lineHeightForElm(elm, font, page):
    maxchars = math.floor(inchesForElement(elm, page) * font.charsPerInch)
    if maxchars <= 0:
        return 0
    s = textwrap.wrap(elm.elmText, maxchars)
    return len(s)

def pushElement(retln, elm, font, page):
    maxchars = math.floor(inchesForElement(elm, page) * font.charsPerInch)
    if maxchars <= 0:
        return
    s = textwrap.wrap(elm.elmText, maxchars)

    for ln in s:
        retln.append([elm.elmType, ln])



def splitScriptText(parse, page, font, enableComments):

    for ie in range(0, len(parse.elms)):
        parse.elms[ie].elmText = preProcessElmText(parse.elms[ie], enableComments)

    retpgs = []
    retln = []
    pi = 0

    ignoringTypes = set(["Boneyard", "Synopsis", "Section Heading"])
    if not enableComments:
        ignoringTypes.add("Comment")

    dualDialogueCharacterCount = 0

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
            retpgs.append(retln)
            retln = []
            pi = pi + 1
            elmno = 0
            ypos = 0
            continue

        if e.elmType == "Character":
            spaceBefore = lineBeforeElement(e, font)
            elmHeight = lineHeightForElm(e, font, page)

            # Initial character tag
            spaceBefore = lineBeforeElement(e, font)
            elmHeight = lineHeightForElm(e, font, page)
            blockHeight = elmHeight
            if elmno > 0: # Need spacing first
                blockHeight = blockHeight + spaceBefore

            if ypos + blockHeight + 3 >= page.usableHeight(font):
                # new page
                retpgs.append(retln)
                retln = []
                pi = pi + 1
                elmno = 0
                ypos = 0
                blockHeight = elmHeight # First element now

            # Now, add character cue
            if elmno > 0:
                for z in range(0, spaceBefore):
                    retln.append(["/", ""])
            pushElement(retln, e, font, page)
            ypos = ypos + blockHeight
            elmno = elmno + 1

            # Absord entire cue's contents:
            s = set(["Dialogue", "Parenthetical","Lyrics"])
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
                spaceAvail = page.usableHeight(font) - ypos



                height_needed = lineHeightForElm(de, font, page)
                if elmno > 0:
                    height_needed = height_needed + lineBeforeElement(de, font)

                if spaceAvail < 3 or (spaceAvail < 3+height_needed and de.elmType == "Parenthetical"):
                    pushElement(retln, fparser.newElmCharacter("(MORE)"), font, page)

                    # new page
                    retpgs.append(retln)
                    retln = []
                    pi = pi + 1
                    elmno = 0
                    ypos = 0

                    # (CONT'D)
                    characterCueElm = copy.copy(queue[0])
                    characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                    ypos = lineHeightForElm(characterCueElm, font, page)
                    pushElement(retln, characterCueElm, font, page)
                    elmno = 1

                spaceAvail = page.usableHeight(font) - ypos
                height_needed = lineHeightForElm(de, font, page)
                if elmno > 0:
                    height_needed = height_needed + lineBeforeElement(de, font)

                if de.elmType == "Parenthetical": # Just Dump It!
                    if elmno > 0:
                        for z in range(0, lineBeforeElement(de, font)):
                            retln.append(["/", ""])
                    pushElement(retln, de, font, page)
                    ypos = ypos + height_needed
                    elmno = elmno + 1
                else:
                    usableLines = spaceAvail - 1 # Leaves 1 line for (CONT'D)
                    if elmno > 0:
                        for z in range(0, lineBeforeElement(de, font)):
                            retln.append(["/", ""])
                            usableLines = usableLines - 1

                    # Split by Sentence
                    sentences = [m.group(1) for m in re.finditer("(.+?[\\.\\?\\!]+\\s*)", de.elmText+".") if m]
                    if len(sentences) > 0:
                        sentences[len(sentences) -1] = sentences[len(sentences) -1][:-1] # remove "."
                        if sentences[len(sentences) -1] == "":
                            sentences = sentences[:-1]
                    maxSentences = len(sentences)

                    # Count Sentences We can Fit
                    dialogueBeforeBreak = ""
                    dialogueHeight = 0
                    sentenceIndex = -1
                    allSentencesFit = True
                    while sentenceIndex+1 < maxSentences:
                        sentenceIndex = sentenceIndex + 1
                        text = dialogueBeforeBreak + sentences[sentenceIndex]
                        tmpElm = fparser.FElement()
                        tmpElm.elmText = text
                        tmpElm.elmType = de.elmType
                        dialogueHeight = lineHeightForElm(tmpElm, font, page)
                        dialogueHeight = dialogueHeight + lineBeforeElement(fparser.newElmDialogue(text), font)

                        # Second case only considered when this is the last sentence
                        if (dialogueHeight < usableLines) or False: #(dialogueHeight<=usableLines+1 and sentenceIndex==maxSentences-1 and ):
                            dialogueBeforeBreak = dialogueBeforeBreak + sentences[sentenceIndex]
                        else:
                            allSentencesFit = False
                            break

                    # Prepare rest of dialog -> we want to redo this element with updated text
                    if sentenceIndex < 0:
                        sentenceIndex = 0
                    dialogueAfterBreak = ""
                    if not allSentencesFit:
                        for z in range(sentenceIndex, maxSentences):
                            dialogueAfterBreak = dialogueAfterBreak + sentences[z]
                    queue[dei].elmText = dialogueAfterBreak

                    # Add Dialog:
                    preBreakDialogue = fparser.newElmDialogue(dialogueBeforeBreak)
                    preBreakDialogue.elmType = de.elmType
                    pushElement(retln, preBreakDialogue, font, page)
                    ypos = ypos + lineHeightForElm(preBreakDialogue, font, page)
                    ypos = ypos + lineBeforeElement(preBreakDialogue, font)

                    if queue[dei].elmText != "": # Need to continue this block
                        pushElement(retln, fparser.newElmCharacter("(MORE)"), font, page)

                        # new page
                        retpgs.append(retln)
                        retln = []
                        pi = pi + 1
                        elmno = 0
                        ypos = 0

                        # (CONT'D)
                        characterCueElm = copy.copy(queue[0])
                        characterCueElm.elmText = characterCueElm.elmText + " (CONT'D)"
                        ypos = lineHeightForElm(characterCueElm, font, page)
                        pushElement(retln, characterCueElm, font, page)
                        elmno = 1

                        dei = dei - 1

            continue

        # All other types:
        spaceBefore = lineBeforeElement(e, font)
        if e.elmType == "Lyrics" and ie > 0 and elms[ie-1].elmType != "Lyrics":
            spaceBefore = 1

        elmHeight = lineHeightForElm(e, font, page)
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore


        # Don't want scene heading last entry on page
        if e.elmType == "Scene Heading" and ie+1 < len(elms):
            enext = elms[ie+1]
            nextHeight = lineHeightForElm(enext, font, page)
            nextHeight = nextHeight + lineBeforeElement(enext, font)
            if enext.elmType == "Lyrics":
                nextHeight = nextHeight + 1

            if blockHeight + ypos + nextHeight >= page.usableHeight(font) and nextHeight >= 1:
                retpgs.append(retln)
                retln = []
                pi = pi + 1
                elmno = 0
                ypos = 0
            elif enext.elmType == "Character" and blockHeight + ypos + nextHeight + 8 >= page.usableHeight(font):
                retpgs.append(retln)
                retln = []
                pi = pi + 1
                elmno = 0
                ypos = 0

        # Recalculate space required - in case "Scene Heading" changed it
        spaceBefore = lineBeforeElement(e, font)
        if e.elmType == "Lyrics" and ie > 0 and elms[ie-1].elmType != "Lyrics":
            spaceBefore = 1

        elmHeight = lineHeightForElm(e, font, page)
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore

        # Check if we are overflowing - if so, next page:
        if blockHeight + ypos >= page.usableHeight(font):
            retpgs.append(retln)
            retln = []
            pi = pi + 1
            elmno = 0
            ypos = 0

        # Recalculate space required - in case page changed
        spaceBefore = lineBeforeElement(e, font)
        if e.elmType == "Lyrics" and ie > 0 and elms[ie-1].elmType != "Lyrics":
            spaceBefore = 1

        elmHeight = lineHeightForElm(e, font, page)
        if elmHeight <= 0:
            continue
        blockHeight = elmHeight
        if elmno > 0: # Need spacing first
            blockHeight = blockHeight + spaceBefore

        # Padding Before Element:
        if elmno > 0 and spaceBefore > 0:
            for z in range(0, spaceBefore):
                retln.append(["/", ""])

        # Now -- The Element
        pushElement(retln, e, font, page)
        ypos = ypos + blockHeight
        elmno = elmno + 1


    # Strip last page added
    #print(html)
    #html = html[:html.rfind("<section>")]

    if len(retln) > 0:
        retpgs.append(retln)

    return retpgs

"""
s = sys.argv[1]
parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
proccess = splitScriptText(parse, Page(), Font())

for pg in proccess:
    for ln in pg:
        typ = ln[0]
        s = ln[1]
        print(s)
"""
