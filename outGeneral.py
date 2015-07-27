#!/bin/python

import fparser
import math
import re
import textwrap

class Font:
    def __init__(self):
        self.name = "Courier-New"
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

def wordWrapString(text, font, maxInches):
    maxchars = math.floor(maxInches * font.charsPerInch)
    if maxchars <= 0:
        return []
    return textwrap.wrap(text, maxchars)
