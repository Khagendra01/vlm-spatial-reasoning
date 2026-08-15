#!/usr/bin/env python3
"""Extract OpenReview-ready title/abstract from the compiled paper source.

Resolves \\eqn macros to their values from numbers.tex and strips LaTeX
markup, producing plain text for the OpenReview form.
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent
tex = (P / "main.tex").read_text(encoding="utf-8")
nums = (P / "numbers.tex").read_text(encoding="utf-8")

# macro -> value
macros = dict(re.findall(r"\\def\\(eqn\w+)\{([^}]*)\}", nums))

title = re.search(r"\\title\{(.*?)\}", tex, re.S).group(1)
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
                     tex, re.S).group(1)


def plain(s: str) -> str:
    # resolve eqn macros first
    s = re.sub(r"\\eqn\w+",
               lambda m: macros.get(m.group(0)[1:], "?"), s)
    s = s.replace(r"$\times$", "\u00d7")
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)          # commands
    s = re.sub(r"[{}\$~`]", "", s)                # markup chars
    s = s.replace("\\", "")                        # stray backslashes
    s = s.replace("--", "\u2013")                  # en-dashes
    s = re.sub(r"\s+", " ", s).strip()
    return s


t = plain(title)
a = plain(abstract)
print("TITLE:", t)
print()
print("ABSTRACT:")
print(a)
print()
print("chars:", len(a))
