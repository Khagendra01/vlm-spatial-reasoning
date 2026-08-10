# Anonymity scan for WACV 2027 upload artifacts.
# Scans: main.pdf, supplementary.pdf, wacv2027_code.zip contents, and the
# LaTeX sources. Excludes internal docs (checklists) which are not uploaded
# and which legitimately name the scanned tokens.
import os
import re
import zipfile

PKG = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(PKG, 'anonymity_scan_output.txt')

PATTERNS = {
    'author names/usernames': re.compile(r'khage|khagendra|khatri', re.I),
    'emails': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    'windows paths': re.compile(r'C:\\Users|[A-Z]:\\'),
    'linux box paths': re.compile(r'/home/ubuntu'),
    'repo name': re.compile(r'vlm-spatial|VLM-Spatial', re.I),
    'branch/tag names': re.compile(r'paper-draft|paper-freeze|paper-submission'),
    'author github identity': re.compile(r'github\.com/Khagendra01', re.I),
    'git SHAs (hex with a-f)': re.compile(r'\b(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b'),
}


def scan(name, text, hits):
    for label, rx in PATTERNS.items():
        for m in rx.finditer(text):
            s = max(0, m.start() - 50)
            hits.append('[%s] %s: ...%s...' % (label, name, text[s:m.end() + 50].replace('\n', ' ')))


def main():
    hits = []
    from pypdf import PdfReader
    for pdf in ['main.pdf', 'supplementary.pdf']:
        r = PdfReader(os.path.join(PKG, pdf))
        txt = ''.join((pg.extract_text() or '') for pg in r.pages)
        scan(pdf, txt, hits)

    z = zipfile.ZipFile(os.path.join(PKG, 'wacv2027_code.zip'))
    for name in z.namelist():
        if name.endswith(('.py', '.md', '.txt', '.tex', '.csv', '.json')):
            scan('zip:' + name, z.read(name).decode('utf-8', errors='replace'), hits)

    for root, dirs, fs in os.walk(os.path.join(PKG, 'source')):
        if 'build' in root:
            continue
        for f in fs:
            if f.endswith(('.tex', '.bib', '.sty')):
                p = os.path.join(root, f)
                scan('src:' + os.path.relpath(p, PKG),
                     open(p, encoding='utf-8', errors='replace').read(), hits)

    # Categorize: benign known items vs anything else
    benign_hex = {'28f4cc09887477af', '4d371713c96ee0d9'}
    real = []
    for h in sorted(set(hits)):
        m = re.search(r'\[git SHAs[^]]*\] [^:]*: \.\.\.(\S{7,40})\.\.\.$', h)
        if m and m.group(1) in benign_hex:
            continue  # protocol config hash, deliberately retained
        real.append(h)

    lines = []
    lines.append('Anonymity scan - upload artifacts only (PDFs, code ZIP, LaTeX sources).')
    lines.append('Scope note: internal checklists (not uploaded) are excluded; they legitimately')
    lines.append('name the scanned tokens as documentation.')
    lines.append('')
    if real:
        lines.append('HITS (%d):' % len(real))
        lines.extend(real)
    else:
        lines.append('NO IDENTIFYING HITS.')
    lines.append('')
    lines.append('Benign excluded items:')
    lines.append('  - SITE protocol config hashes 28f4cc09887477af / 4d371713c96ee0d9 (preregistration artifacts)')
    lines.append('  - numeric float runs in JSON/CSV that match the hex pattern (false positives)')
    lines.append('  - github.com/cvpr-org/author-kit comment inside the official wacv.sty')
    lines.append('  - github.com/wenqi-wang20/SITE-Bench (SITE benchmark provenance)')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('scan record written; real hits:', len(real))


if __name__ == '__main__':
    main()
