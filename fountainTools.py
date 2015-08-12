#!/bin/python

from tkinter import *
from tkinter.ttk import *

import tkinter.filedialog
import tkinter.messagebox
import os


# ALL ActionClasses:
import fparser
import semanticLineFeed
import characterCards
import htmlOut
import pdfOut
from outGeneral import *

class Example(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.parent.title("FountainTools")
        self.style = Style()
        self.style.theme_use("default")

        self.pack(fill=BOTH, expand=1)

        # ----------File Selection------------------
        ftmp = Frame(self)
        tmp = Label(ftmp, text="File:")
        tmp.pack(side=LEFT, padx=5)
        self.filePathEdit = Entry(ftmp)
        self.filePathEdit.pack(side=LEFT, padx=5)
        self.filePathBtn = Button(ftmp, text="...", command=self.onFilePathBtn)
        self.filePathBtn.pack(side=LEFT, padx=5)
        ftmp.pack()

        # ----------Output Dir Selection------------------
        ftmp = Frame(self)
        tmp = Label(ftmp, text="Output:")
        tmp.pack(side=LEFT, padx=5)
        self.outPathEdit = Entry(ftmp)
        self.outPathEdit.pack(side=LEFT, padx=5)
        self.outPathBtn = Button(ftmp, text="...", command=self.onOutPathBtn)
        self.outPathBtn.pack(side=LEFT, padx=5)
        ftmp.pack()

        # -----------Output Formats-------------------
        tmp = Label(self, text="Output Formats:")
        tmp.pack()
        self.opPDF = BooleanVar()
        self.opPDF.set(True)
        tmp = Checkbutton(self, text="PDF", variable=self.opPDF)
        tmp.pack()
        self.opHTML = BooleanVar()
        tmp = Checkbutton(self, text="HTML", variable=self.opHTML)
        tmp.pack()
        self.opCharCard = BooleanVar()
        tmp = Checkbutton(self, text="Character Dialogue", variable=self.opCharCard)
        tmp.pack()
        self.opSemanticLF = BooleanVar()
        tmp = Checkbutton(self, text="Semantic Linefeed Version", variable=self.opSemanticLF)
        tmp.pack()

        # -----------Misc Options-------------------
        tmp = Label(self, text="Output Formats:")
        tmp.pack()

        self.opPaperSize = StringVar()
        ftmp = Frame(self)
        tmp = Label(ftmp, text="Paper:")
        tmp.pack(side=LEFT, padx=5)
        tmp = Combobox(ftmp, textvariable=self.opPaperSize, state='readonly', values=['Letter', 'A4'])
        tmp.current(0)
        tmp.pack()
        ftmp.pack()

        self.opComments = BooleanVar()
        self.opComments.set(False)
        tmp = Checkbutton(self, text="Include Comments", variable=self.opComments)
        tmp.pack()

        #------------------OK---------------------
        self.okBtn = Button(self, text="OK", command=self.onOK)
        self.okBtn.pack()





    def onFilePathBtn(self):
        ftypes = [('Fountain Files', '*.fountain'), ('All files', '*')]
        dlg = tkinter.filedialog.Open(self, filetypes = ftypes, initialfile=self.filePathEdit.get())
        fl = dlg.show()

        if fl != '':
            self.filePathEdit.delete(0, END)
            self.filePathEdit.insert(0, fl)

            if self.outPathEdit.get() == "":
                self.outPathEdit.delete(0, END)
                self.outPathEdit.insert(0, os.path.dirname(fl))

    def onOutPathBtn(self):
        fl = tkinter.filedialog.askdirectory(initialdir=self.outPathEdit.get())
        if fl != '':
            self.outPathEdit.delete(0, END)
            self.outPathEdit.insert(0, fl)

    def onOK(self):
        self.okBtn.config(state=DISABLED)
        self.run()
        tkinter.messagebox.showinfo("Fountain Tools", "Operation has completed.")
        self.okBtn.config(state=NORMAL)

    def run(self):

        inFileName = self.filePathEdit.get()
        inFileNameBase = os.path.basename(inFileName)
        inFile = open(inFileName, "r", encoding="utf-8").read()
        outDir = self.outPathEdit.get()+"/"

        parse = fparser.FParser(inFile)

        page = Page(self.opPaperSize.get())
        font = Font()

        if self.opSemanticLF.get():
            print("SemLF")
            txt = semanticLineFeed.semanticLineFeed(inFile)
            fl = open(outDir+inFileNameBase+".slf", "w")
            fl.write(txt)
            fl.close()
        if self.opCharCard.get():
            print("CharCards")
            characterCards.characterCards(parse.elms, outDir)
        if self.opHTML.get():
            print("HTML")
            html = htmlOut.htmlout(parse, self.opComments.get())
            fl = open(outDir+inFileNameBase+".html", "w")
            fl.write(html)
            fl.close()
        if self.opPDF.get():
            print("PDF")
            pdfOut.pdfout(parse, outDir+inFileNameBase+".pdf", self.opComments.get(), font, page)




def main():

    root = Tk()
    #root.geometry("250x150+300+300")
    app = Example(root)
    root.mainloop()

if __name__ == '__main__':
    main()
