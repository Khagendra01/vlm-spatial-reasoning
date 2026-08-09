"""Parse subject/reference object names from VSR orientation statements."""
import re

REL_PATTERNS = [
    (r"\b(?:is|are)\s+(?:not\s+)?facing\s+away\s+from\b", "facing away from"),
    (r"\b(?:is|are)\s+(?:not\s+)?facing\b", "facing"),
    (r"\b(?:is|are)\s+(?:not\s+)?parallel\s+to\b", "parallel to"),
    (r"\b(?:is|are)\s+(?:not\s+)?perpendicular\s+to\b", "perpendicular to"),
]

def parse_orientation_statement(statement):
    """Returns (subject, relation, reference) or None."""
    text = statement.strip()
    for pat, rel in REL_PATTERNS:
        m = re.search(pat, text)
        if m:
            subj = text[:m.start()].strip()
            ref = text[m.end():].strip()
            subj = re.sub(r"^the\s+", "", subj, flags=re.I).strip()
            ref = re.sub(r"^the\s+", "", ref, flags=re.I).strip()
            ref = re.sub(r"\.$", "", ref).strip()
            if subj and ref:
                return subj, rel, ref
    return None
