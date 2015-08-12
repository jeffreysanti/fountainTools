#!/bin/python

import re
import sys

def semanticLineFeed(s):
    s = s.replace("\\r\\n", "\n")
    s = s.replace("\\n\\r", "\n")

    # Some Script Oddities:
    s = s.replace("(V.O.)", "")
    s = s.replace("(O.S.)", "")
    s = s.replace("INT.", "INT")
    s = s.replace("EXT.", "EXT")

    s = s.replace(",\"", ",\n")
    s = s.replace(".\"", ".\n")
    s = s.replace(";\"", ";\n")
    s = s.replace("?\"", "?\n")
    s = s.replace("!\"", "!\n")

    s = s.replace("\"", "\n")

    s = s.replace(".", ".\n")
    s = s.replace(";", ";\n")
    s = s.replace(":", ":\n")
    s = s.replace("?", "?\n")
    s = s.replace("!", "!\n")

    final = ""
    lines = s.split("\n")
    for line in lines:
        line = line.strip()
        if line != "" and len(line) > 1:
            final = final + line + "\n"

    return final


if __name__ == '__main__':
    s = sys.argv[1]
    txt = open(s, "r", encoding="utf-8").read()
    txt = semanticLineFeed(txt)

    fl = open(s+".slf", "w")
    fl.write(txt)
    fl.close()
