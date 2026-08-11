# Finalize the WACV 2027 upload PDFs with the real OpenReview paper ID.
#
# WHEN: after Aug 21 enrollment, OpenReview assigns a paper number.
# USAGE: python set_paper_id.py YOUR_PAPER_ID
#   e.g.  python set_paper_id.py 1234
#
# It updates main.tex + suppl.tex, rebuilds both PDFs (Tectonic), and
# replaces the copies in 01_UPLOAD_THIS/ with the finalized versions.
import os
import re
import shutil
import subprocess
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(KIT, '04_LATEX_SOURCE', 'wacv2027_source')
UPLOAD = os.path.join(KIT, '01_UPLOAD_THIS')
TECTONIC = r'C:\Users\Khage\AppData\Local\Temp\opencode\tectonic\tectonic.exe'

if len(sys.argv) != 2 or not sys.argv[1].isdigit():
    sys.exit('usage: python set_paper_id.py <paper id, digits only>')

pid = sys.argv[1]
print('setting WACV paper ID to:', pid)

for name in ('main.tex', 'suppl.tex'):
    p = os.path.join(SRC, name)
    t = open(p, encoding='utf-8').read()
    t2 = re.sub(r'\\def\\wacvPaperID\{[^}]*\}', '\\def\\wacvPaperID{%s}' % pid, t)
    assert t2 != t, 'wacvPaperID not found in ' + name
    open(p, 'w', encoding='utf-8').write(t2)
    print('updated', name)

build = os.path.join(SRC, 'build')
os.makedirs(build, exist_ok=True)
for name, out in (('main.tex', 'main.pdf'), ('suppl.tex', 'supplementary.pdf')):
    subprocess.run([TECTONIC, name, '--outdir', 'build'],
                   cwd=SRC, check=True, capture_output=True)
    shutil.copy2(os.path.join(build, 'main.pdf' if name == 'main.tex' else 'suppl.pdf'),
                 os.path.join(UPLOAD, out))
    print('rebuilt and copied', out)

print('done. Verify hashes and header ("Submission #%s") before uploading.' % pid)
