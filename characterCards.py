#!/bin/python

import fparser
import sys
import re

class CharacterLine:
    def __init__(self):
        self.text = ""
        self.voiceOver = False
        self.offScreen = False
        self.wordCount = 0

class CharacterCard:
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.words = 0
        self.voWords = 0
        self.osWords = 0
        self.voLines = 0
        self.osLines = 0

    def addLine(self, text, vo, os):
        line = CharacterLine()
        line.text = text
        line.voiceOver = vo
        line.offScreen = os
        line.wordCount = len(text.split(" "))
        self.lines.append(line)
        self.words = self.words + line.wordCount
        if vo:
            self.voWords = self.voWords + line.wordCount
            self.voLines = self.voLines + 1
        if os:
            self.osWords = self.osWords + line.wordCount
            self.osLines = self.osLines + 1


def characterCards(elms):
    char = ""
    vo = False
    os = False

    chars = dict()

    for e in elms:
        if e.elmType == "Character":
            if e.elmText.find("(V.O.)") > -1:
                vo = True
            else:
                vo = False
            if e.elmText.find("(O.S.)") > -1:
                os = True
            else:
                os = False

            char = e.elmText
            char = char.replace("(V.O.)", "")
            char = char.replace("(O.S.)", "")
            char = re.sub(r'\([^)]*\)', '', char) # In case any remain
            char = char.strip()

        elif e.elmType == "Dialogue":
            if char in chars:
                chars[char].addLine(e.elmText, vo, os)
            else:
                chars[char] = CharacterCard(char)
                chars[char].addLine(e.elmText, vo, os)

    for k in chars:
        fl = open("char."+chars[k].name+".txt", 'w')
        fl.write(chars[k].name + "\n")
        fl.write("WORDS: "+str(chars[k].words) + "\n")
        fl.write("WORDS (V.O.): "+str(chars[k].voWords) + "\n")
        fl.write("WORDS (O.S.): "+str(chars[k].osWords) + "\n")
        fl.write("LINES: "+str(len(chars[k].lines)) + "\n")
        fl.write("LINES (V.O.): "+str(chars[k].voLines) + "\n")
        fl.write("LINES (O.S.): "+str(chars[k].osLines) + "\n")
        fl.write("\n\n")

        for l in chars[k].lines:
            if l.voiceOver:
                fl.write("V.O.\n")
            if l.offScreen:
                fl.write("O.S.\n")
            fl.write(l.text+"\n\n")

        fl.close()

s = sys.argv[1]
parse = fparser.FParser(open(s, "r", encoding="utf-8").read())
characterCards(parse.elms)
