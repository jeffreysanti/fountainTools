#!/bin/python

# Parser is based on Fountain Sample Parser (in Objective-C)
# https://github.com/nyousefi/Fountain/blob/master/Fountain/FastFountainParser.m

import re

class FElement:
    def __init__(self):
        self.elmType = ""
        self.elmText = ""
        self.centered = False

        self.sceneNo = -1
        self.dualDlg = False
        self.sectionDepth = -1


def newElmLyric(t):
    e = FElement()
    e.elmType = "Lyrics"
    e.elmText = t
    return e

def newElmAction(t):
    e = FElement()
    e.elmType = "Action"
    e.elmText = t
    return e

def newElmCharacter(t):
    e = FElement()
    e.elmType = "Character"
    e.elmText = t
    return e

def newElmDialogue(t):
    e = FElement()
    e.elmType = "Dialogue"
    e.elmText = t
    return e

def newElmBoneyard(t):
    e = FElement()
    e.elmType = "Boneyard"
    e.elmText = t
    return e

def newElmPageBreak(t):
    e = FElement()
    e.elmType = "Page Break"
    e.elmText = t
    return e

def newElmSynopsis(t):
    e = FElement()
    e.elmType = "Synopsis"
    e.elmText = t
    return e

def newElmComment(t):
    e = FElement()
    e.elmType = "Comment"
    e.elmText = t
    return e

def newElmSectionHeading(t, d):
    e = FElement()
    e.elmType = "Section Heading"
    e.elmText = t
    e.sectionDepth = d
    return e

def newElmSceneHeading(t):
    e = FElement()
    e.elmType = "Scene Heading"
    e.elmText = t
    return e

def newElmTransition(t):
    e = FElement()
    e.elmType = "Transition"
    e.elmText = t
    return e

def newElmParenthetical(t):
    e = FElement()
    e.elmType = "Parenthetical"
    e.elmText = t
    return e


class FParser:

    PATERN_INLINE = "^([^\\t\\s][^:]+):\\s*([^\\t\\s].*$)"
    PATERN_DIRECTIVE = "^([^\\t\\s][^:]+):([\\t\\s]*$)"
    TRANSITIONS = set(["FADE OUT.", "CUT TO BLACK.", "FADE TO BLACK."])

    def __init__(self, iodev):
        self.iodev = iodev
        self.titlePage = {}
        self.elms = []
        self.parseString(self.iodev.read())

    def parseString(self, s):
        # remove starting whitespace
        s = re.sub("^\\s*", "", s)

        # use linux line endings
        s = re.sub("^\\s*", "", s)
        s = re.sub("\\r\\n", "\n", s)
        s = re.sub("\\n\\r", "\n", s)

        s = s+"\n\n"

        # --------------------TITLE page-----------------------
        firstSection = s.partition("\n\n")[0]
        foundTitlePage = False
        key = ""
        vals = []

        for line in firstSection.split("\n"):
            if line == "" or re.match(self.PATERN_DIRECTIVE, line) != None:
                foundTitlePage = True

                if key != "":
                    self.titlePage[key] = vals

                key = re.match(self.PATERN_DIRECTIVE, line).group(1)
                if key == "author":
                    key = "authors"
            elif re.match(self.PATERN_INLINE, line) != None:
                foundTitlePage = True

                if key != "":
                    self.titlePage[key] = vals
                    key = ""
                    vals = []

                newkey = re.match(self.PATERN_INLINE, line).group(1).lower()
                newval = re.match(self.PATERN_INLINE, line).group(2)
                if newkey == "author":
                    newkey = "authors"
                self.titlePage[newkey] = [newval]
                key = ""
                vals = []
            elif foundTitlePage:
                vals.append(line.strip())

        if foundTitlePage:
            if key == "" or len(vals) != 0 or len(self.titlePage) != 0:
                if key != "":
                    self.titlePage[key] = vals
                    key = ""
                    vals = []

                # Clear Title Section
                s = s.replace(firstSection, "")

        #------------BODY----------------------------------------------
        s = "\n" + s
        newlinesBefore = 0;
        index = -1;
        isCommentBlock = False;
        isInsideDialogueBlock = False;
        commentText = ""
        lines = s.split("\n")

        for line in lines:
            index = index + 1

            # Lyrics
            if len(line) > 0 and line[0] == '~':
                if len(self.elms) == 0:
                    self.elms.append(newElmLyric(line))
                    newlinesBefore = 0
                    continue

                if self.elms[-1].elmType == "Lyrics" and newlinesBefore > 0:
                    self.elms.append(newElmLyric(" "))

                self.elms.append(newElmLyric(line))
                newlinesBefore = 0
                continue

            # Action
            if len(line) > 0 and line[0] == '!':
                self.elms.append(newElmAction(line))
                newlinesBefore = 0
                continue

            # Character
            if len(line) > 0 and line[0] == '@':
                self.elms.append(newElmCharacter(line))
                newlinesBefore = 0
                isInsideDialogueBlock = True
                continue

            # Empty Dialog Lines (Two Spaces by Fountain Specs)
            if isInsideDialogueBlock and re.match("^\\s{2}$", line) != None:
                newlinesBefore = 0;
                if self.elms[-1].elmType == "Dialogue":
                    self.elms[-1].elmText = self.elms[-1].elmText + "\n" + line
                else:
                    self.elms.append(newElmDialogue(line))
                continue;

            if re.match("^\\s{2,}$", line) != None:
                newlinesBefore = 0;
                self.elms.append(newElmAction(line))
                continue;

            if line == "" and not isCommentBlock:
                isInsideDialogueBlock = False
                newlinesBefore = newlinesBefore + 1
                continue

            # Match comment "/*"
            if re.match("^\\/\\*", line) != None:
                if re.match("\\*\\/\\s*$", line) != None:
                    text = line.replace("/*", "").replace("*/", "")
                    isCommentBlock = False
                    self.elms.append(newElmBoneyard(text))
                    newlinesBefore = 0
                else:
                    isCommentBlock = True
                    commentText = commentText + "\n"
                continue

            # Match comment end "*/"
            if re.match("\\*\\/\\s*$", line) != None:
                text = line.replace("*/", "")
                if text == "" or re.match("^\\s*$", line) != None:
                    commentText = commentText + text.strip()
                isCommentBlock = NO;
                self.elms.append(newElmBoneyard(commentText))
                commentText = ""
                newlinesBefore = 0;
                continue;

            # Inside a comment block
            if isCommentBlock:
                commentText = commentText + line + "\n"
                continue

            # Manual Page Break
            if re.match("^={3,}\\s*$", line) != None:
                self.elms.append(newElmPageBreak(line))
                newlinesBefore = 0
                continue

            # Synopsis (=)
            if len(line.strip()) > 0 and line.strip()[0] == '=':
                self.elms.append(newElmSynopsis(line.partition("=")[2]))
                continue

            # [[Comment]]
            if newlinesBefore > 0 and re.match("^\\s*\\[{2}\\s*([^\\]\\n])+\\s*\\]{2}\\s*$", line) != None:
                text = line.replace("[[", "").replace("]]", "").strip()
                self.elms.append(newElmComment(text))
                continue

            # Section Heading:
            if len(line.strip()) > 0 and line.strip()[0] == '#':
                newlinesBefore = 0;
                m = re.match("^\\s*#+", line)
                depth = m.end() - m.start()
                text = line[m.end()]
                if (text == ""):
                    raise Exception("Empty Section Heading!")
                self.elms.append(newElmSectionHeading(text, depth))
                continue

            # Forced Scene Heading (.HEADING)
            if len(line) > 1 and line[0] == '.' and line[1] != '.':
                newlinesBefore = 0;
                sceneNumber = None;
                text = "";

                if re.match("#([^\\n#]*?)#\\s*$", line) != None:
                    sceneNumber = re.match("#([^\\n#]*?)#\\s*$", line).group(1)
                    text = re.sub("#([^\\n#]*?)#\\s*$", "", line)
                    text = text[1:].strip()
                else:
                    text = line[1:].strip()

                elm = newElmSceneHeading()
                if sceneNumber != None:
                    elm.sceneNumber = sceneNumber;
                self.elms.append(elm)
                continue;

            # Normal Scene Headings
            if newlinesBefore > 0 and re.match("^(INT|EXT|EST|(I|INT)\\.?\\/(E|EXT)\\.?)[\\.\\-\\s][^\\n]+$", line, re.IGNORECASE) != None:
                newlinesBefore = 0
                sceneNumber = None
                text = ""

                if re.match("#([^\\n#]*?)#\\s*$", line) != None:
                    sceneNumber = re.match("#([^\\n#]*?)#\\s*$", line).group(1)
                    text = re.sub("#([^\\n#]*?)#\\s*$", "", line)
                else:
                    text = line

                elm = newElmSceneHeading(text)
                if sceneNumber != None:
                    elm.sceneNumber = sceneNumber;
                self.elms.append(elm)
                continue

            # Transitions
            if re.match("[^a-z]*TO:$", line) != None:
                newlinesBefore = 0
                self.elms.append(newElmTransition(line))
                continue

            lineWithTrimmedLeading = re.sub("^\\s*", "", line)
            if lineWithTrimmedLeading in self.TRANSITIONS:
                newlinesBefore = 0
                self.elms.append(newElmTransition(line))
                continue

            # Foced Transition >...
            if len(line) > 0 and line[0] == '>':
                if len(line) > 1 and line[-1] == '<':
                    newlinesBefore = 0
                    text = line[1:].strip()[:-1].strip()
                    elm = newElmAction(text)
                    elm.centered = True
                    self.elms.append(elm)
                    continue
                else:
                    newlinesBefore = 0
                    text = line[1:].strip()
                    self.elms.append(newElmTransition(text))
                    continue

            # Character
            if newlinesBefore > 0 and re.match("^[^a-z]+(\\(cont'd\\))?$", line) != None:
                if index + 1 < len(lines) and lines[index+1] != "":
                    newlinesBefore = 0
                    elm = newElmCharacter(line)

                    if re.match("\\^\\s*$", line) != None:
                        elm.dualDlg = True
                        elm.elmText = re.sub("\\s*\\^\\s*$", "", elm.elmText)
                        ind = len(self.elms) -1
                        while ind > 0:
                            if self.elms[ind].elmType == "Character":
                                self.elms[ind].dualDlg = True
                                break
                            ind = ind - 1

                    self.elms.append(elm)
                    isInsideDialogueBlock = True
                    continue

            #Dialogue and Parentheticals
            if isInsideDialogueBlock:
                if newlinesBefore == 0 and re.match("^\\s*\\(", line) != None:
                    self.elms.append(newElmParenthetical(line))
                    continue
                else:
                    if self.elms[-1].elmType == "Dialogue":
                        self.elms[-1].elmText = self.elms[-1].elmText + "\n" + line
                    else:
                        self.elms.append(newElmDialogue(line))
                    continue

            # A few checks: Certain Elements need new lines before
            # Since, newlinesBefore=0 correct these tags
            if newlinesBefore == 0 and len(self.elms) > 0:
                if self.elms[-1].elmType == "Scene Heading":
                    self.elms[-1] = newElmAction(self.elms[-1].elmText)

                self.elms[-1].elmText = self.elms[-1].elmText + "\n" + line
                newlinesBefore = 0
                continue
            else:
                self.elms.append(newElmAction(line))
                newlinesBefore = 0
                continue

        for e in self.elms:
            print(e.elmType + "///" + e.elmText)





x = FParser(open("examples/Big-Fish.fountain", "r", encoding="utf-8"))
