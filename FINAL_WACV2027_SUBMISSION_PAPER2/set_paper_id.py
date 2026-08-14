# Finalize the WACV 2027 upload PDFs with the real OpenReview paper ID.
# Paper 2 (paper2_source). Adapted for the local MiKTeX (pdflatex) toolchain.
#
# WHEN: after Aug 21 enrollment, OpenReview assigns a paper number.
# USAGE: python set_paper_id.py YOUR_PAPER_ID
#   e.g.  python set_paper_id.py 1234
#
# It updates main.tex + suppl.tex, rebuilds both PDFs (pdflatex+bibtex), and
# replaces the copies in 01_UPLOAD_THIS/ with the finalized versions.
import os
import re
import shutil
import subprocess
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(KIT, '04_LATEX_SOURCE', 'paper2_source')
UPLOAD = os.path.join(KIT, '01_UPLOAD_THIS')
PDFLATEX = r'C:\Users\Khage\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
BIBTEX = r'C:\Users\Khage\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'

if len(sys.argv) != 2 or not sys.argv[1].isdigit():
    sys.exit('usage: python set_paper_id.py <paper id, digits only>')

pid = sys.argv[1]
print('setting WACV paper ID to:', pid)

for name in ('main.tex', 'suppl.tex'):
    p = os.path.join(SRC, name)
    t = open(p, encoding='utf-8').read()
    assert re.search(r'\\def\\wacvPaperID\{[^}]*\}', t), 'wacvPaperID not found in ' + name
    t2 = re.sub(r'\\def\\wacvPaperID\{[^}]*\}',
                lambda m: '\\def\\wacvPaperID{%s}' % pid, t)
    if t2 != t:
        open(p, 'w', encoding='utf-8').write(t2)
        print('updated', name)
    else:
        print('already set in', name)

build = os.path.join(SRC, 'build')
os.makedirs(build, exist_ok=True)

def run(*args, cwd=None):
    subprocess.run(list(args), cwd=cwd or SRC, check=True,
                   capture_output=True, text=True)

def build_doc(tex, upload_pdf):
    # build output is always <tex>.pdf; upload name may differ
    out_pdf = tex[:-4] + '.pdf'
    # bibtex needs the .bib + .bst visible from the build dir
    for extra in ('references.bib', 'ieeenat_fullname.bst'):
        src = os.path.join(SRC, extra)
        if os.path.exists(src) and not os.path.exists(os.path.join(build, extra)):
            shutil.copy2(src, build)
    # pdflatex (pass 1), bibtex (if aux requests it), pdflatex (passes 2-3)
    run(PDFLATEX, '-interaction=nonstopmode', '-halt-on-error', '-output-directory', build, tex)
    aux = os.path.join(build, tex[:-4] + '.aux')
    if os.path.exists(aux) and re.search(r'\\bibdata', open(aux, encoding='utf-8', errors='ignore').read()):
        run(BIBTEX, tex[:-4], cwd=build)
        run(PDFLATEX, '-interaction=nonstopmode', '-halt-on-error', '-output-directory', build, tex)
    run(PDFLATEX, '-interaction=nonstopmode', '-halt-on-error', '-output-directory', build, tex)
    src = os.path.join(build, out_pdf)
    dst = os.path.join(UPLOAD, upload_pdf)
    shutil.copy2(src, dst)
    print('rebuilt and copied', upload_pdf)

build_doc('main.tex', 'main.pdf')
build_doc('suppl.tex', 'supplementary.pdf')

print('done. Verify hashes and header ("Submission #%s") before uploading.' % pid)
