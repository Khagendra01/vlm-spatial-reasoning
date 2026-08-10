# Convert the CVPR-format main.tex into the official WACV 2027 template.
src = r'C:\Users\Khage\AppData\Local\Temp\opencode\pdv\paper\main.tex'
dst = r'C:\Users\Khage\AppData\Local\Temp\opencode\pdv\submission\wacv2027\source\main.tex'
t = open(src, encoding='utf-8').read()

head_end = t.index(r'\newcommand{\vsr}{VSR}')
NL = chr(10)
new_head = (
    "% WACV 2027 paper - Evaluations & Dataset track." + NL +
    "% Official WACV 2027 author kit (wacv.sty). Review version, anonymous." + NL +
    "% Compile:  tectonic main.tex    (main paper; 8 pages max incl. figures/tables," + NL +
    "%                                 additional reference-only pages allowed)" + NL +
    "%           tectonic suppl.tex   (supplementary; does not count toward the limit)" + NL +
    NL +
    "\\documentclass[10pt,twocolumn,letterpaper]{article}" + NL +
    NL +
    "% REVIEW version for the Evaluations & Dataset track (anonymous, page numbers)." + NL +
    "% Camera-ready: \\usepackage{wacv}" + NL +
    "\\usepackage[review,datasets]{wacv}" + NL +
    "% \\usepackage[pagenumbers]{wacv} % arXiv version" + NL +
    NL +
    "\\input{preamble}" + NL +
    NL +
    "\\definecolor{wacvblue}{rgb}{0.21,0.49,0.74}" + NL +
    "\\usepackage[pagebackref,breaklinks,colorlinks,allcolors=wacvblue]{hyperref}" + NL +
    "\\usepackage[capitalize,noabbrev]{cleveref}" + NL +
    NL +
    "\\def\\wacvPaperID{*****} % assigned at OpenReview enrollment" + NL +
    "\\def\\confName{WACV}" + NL +
    "\\def\\confYear{2027}" + NL +
    NL
)
t = new_head + t[head_end:]

t = t.replace(r'\includegraphics[width=\columnwidth]{../results/figures/',
              r'\includegraphics[width=\columnwidth]{fig/')

auth_old = "\\author{Anonymous Authors\\\\" + NL + "Anonymous Institution\\\\" + NL + "\\texttt{anonymous@anonymous.edu}}"
auth_new = "\\author{Anonymous Authors\\\\" + NL + "Anonymous Institution}"
assert auth_old in t, 'author block not found'
t = t.replace(auth_old, auth_new)

open(dst, 'w', encoding='utf-8').write(t)
print('main.tex written;', len(t), 'chars')
