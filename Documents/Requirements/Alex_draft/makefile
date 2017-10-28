LATEX	= /usr/local/apps/tex_live/current/bin/x86_64-linux/latex -shell-escape
LATEX2	= pdflatex -shell-escape
DVIPS	= dvips
DVIPDF  = dvipdft
XDVI	= xdvi -gamma 4
GH		= gv

EXAMPLES = $(wildcard *.c)
SRC	:= $(shell egrep -l '^[^%]*\\begin\{document\}' *.tex)
TRG	= $(SRC:%.tex=%.dvi)
PSF	= $(SRC:%.tex=%.ps)
PDF	= $(SRC:%.tex=%.pdf)

all: pdf assignment1

pdf: $(PDF)

ps: $(PSF)

$(TRG): %.dvi: %.tex $(EXAMPLES)
	#one way of including source code is to use pygments
#	pygmentize -f latex -o __${EXAMPLES}.tex ${EXAMPLES}
	#requires that you \include{pygments.tex} in your preamble

	$(LATEX) $<
#	$(BIBTEX) $(<:%.tex=%)
	$(LATEX) $<
	$(LATEX2) $<
	#remove the pygmentized output to avoid cluttering up the directory
	#rm __${SRC}.tex


$(PSF):%.ps: %.dvi
	$(DVIPS) -R -Poutline -t letter $< -o $@

$(PDF): %.pdf: %.ps
	ps2pdf $<

show: $(TRG)
	@for i in $(TRG) ; do $(XDVI) $$i & done

showps: $(PSF)
	@for i in $(PSF) ; do $(GH) $$i & done

assignment1: hw1.c
	gcc -pthread hw1.c -o hw1

#all: pdf

clean:
	rm -f *.ps *.dvi *.out *.log *.aux *.bbl *.blg *.pyg *.o *.toc

.PHONY: all show clean ps pdf showps
