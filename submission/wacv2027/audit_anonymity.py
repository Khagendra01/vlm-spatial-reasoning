# Anonymity scan: search every submission artifact for identifying tokens.
import os
import re
import zipfile

PKG = r'C:\Users\Khage\AppData\Local\Temp\opencode\pdv\submission\wacv2027'
OUT = os.path.join(PKG, 'anonymity_scan_output.txt')

PATTERNS = {
    'author names': re.compile(r'khage|khagendra|khatri', re.I),
    'emails': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    'windows paths': re.compile(r'C:\\Users|[A-Z]:\\'),
    'linux box paths': re.compile(r'/home/ubuntu'),
    'repo name': re.compile(r'vlm-spatial-reasoning|VLM-Spatial', re.I),
    'branch/tag': re.compile(r'paper-draft|paper-freeze|paper-submission'),
    'github identity': re.compile(r'github\.com/[A-Za-z0-9_-]+', re.I),
    'git SHAs': re.compile(r'\b[0-9a-f]{7,40}\b'),
}

lines = []
lines.append('Anonymity scan — %s' % PKG)
lines.append('')

def scan_text(name, text):
    hits = []
    for label, rx in PATTERNS.items():
        for m in rx.finditer(text):
            s = max(0, m.start() - 40)
            ctx = text[s:m.end() + 40].replace('\n', ' ')
            hits.append('  [%s] %s ... %s' % (label, name, ctx))
    return hits

files = []
for root, dirs, fs in os.walk(PKG):
    for f in fs:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, PKG)
        if rel.startswith('source' + os.sep + 'build'):
            continue
        if f.endswith(('.pdf', '.zip')):
            continue
        files.append((rel, p))

total = 0
for rel, p in sorted(files):
    try:
        data = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    h = scan_text(rel, data)
    if h:
        lines.append('== %s ==' % rel)
        lines.extend(h)
        total += len(h)

# PDF metadata
try:
    from pypdf import PdfReader
    for pdf in ['main.pdf', 'supplementary.pdf']:
        r = PdfReader(os.path.join(PKG, pdf))
        md = {k: str(v) for k, v in (r.metadata or {}).items()}
        lines.append('== %s metadata ==' % pdf)
        lines.append('  ' + str(md))
except Exception as e:
    lines.append('metadata check skipped: %s' % e)

# ZIP listing
z = zipfile.ZipFile(os.path.join(PKG, 'wacv2027_code.zip'))
for name in z.namelist():
    if name.endswith(('.py', '.md', '.txt', '.tex', '.csv', '.json')):
        try:
            txt = z.read(name).decode('utf-8', errors='replace')
        except Exception:
            continue
        h = scan_text('zip:' + name, txt)
        if h:
            lines.append('== zip:%s ==' % name)
            lines.extend(h)
            total += len(h)

lines.append('')
lines.append('TOTAL IDENTIFYING HITS: %d' % total)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('scan written; hits:', total)
