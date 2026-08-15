#!/usr/bin/env python3
"""One-shot repair: normalize \\eqn macro references in paper/main.tex.

The manuscript was partially rewritten to CamelCase macros; this fixes
any leftover snake_case forms (e.g. \\eqnVOneaugmentation_only_val} ->
\\eqnVOneAugmentationOnlyVal). Idempotent.
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent / "main.tex"


def camel(name: str) -> str:
    return "".join(
        ("VOne" if p == "V1" else "VTwo" if p == "V2"
         else p[:1].upper() + p[1:])
        for p in name.split("_"))


s = P.read_text(encoding="utf-8")
pat = re.compile(r"\\eqn(VOne|VTwo)([a-z0-9_]*)\}")


def repl(m):
    base = "V1" if m.group(1) == "VOne" else "V2"
    rest = m.group(2)
    name = base + (("_" + rest) if rest else "")
    return "\\eqn" + camel(name)


s2, n = pat.subn(repl, s)
P.write_text(s2, encoding="utf-8")
print(f"fixed {n} references")
left = [l.strip() for l in s2.splitlines() if "eqnV" in l and "_" in l]
print("remaining corrupted:", len(left))
