"""Tier-B semantic interventions (axis S): pixels fixed, language changes.

Per research/GROUNDING_PROTOCOL_FREEZE.md section 5 and
research/SPATIAL_GROUNDING_LORA_STUDY.md sections 9 and 18:

- A transform-validity table with eligible IDs is committed BEFORE any full
  semantic run (freeze_tier_b.py writes it; it is never regenerated after
  results are inspected without a decision-log entry).
- subject/object reversal requires the parser audit (reconstruction
  verification) before use.
- `parallel <-> perpendicular` is NEVER a universal strict complement.

Transforms (all strict, expected truth behavior predeclared):

- relcomp   strict relation complement (flip law):
    expected_transformed_label = NOT original label.
    Only same-axis, mutually exclusive AND exhaustive pairs:
    left of <-> right of; at the left side of <-> at the right side of;
    above <-> below; in front of <-> behind.
- sorev     subject/object reversal on symmetric relations (stability law):
    expected_transformed_label = original label.
    Only relations that are logically symmetric (R(a,b) <=> R(b,a)).
- continv   containment inverse paraphrase (paraphrase law):
    in/inside/within <-> contains with argument roles swapped.
    expected_transformed_label = original label.
"""

import csv
import json
import re

from . import config
from .eligibility import load_ids_payload

# --------------------------------------------------------------------------
# Predeclared transform definitions (frozen before any Tier-B result)
# --------------------------------------------------------------------------

# Same spatial axis, mutually exclusive AND exhaustive for that axis, in the
# image frame. Verified pair memberships (no self-pairs, no parallel/
# perpendicular anywhere).
STRICT_COMPLEMENT_PAIRS = {
    "left of": "right of",
    "right of": "left of",
    "at the left side of": "at the right side of",
    "at the right side of": "at the left side of",
    "above": "below",
    "below": "above",
    "in front of": "behind",
    "behind": "in front of",
}

# R(a,b) <=> R(b,a) for the VSR noun phrases in scope.
SYMMETRIC_RELATIONS = {
    "touching", "next to", "beside", "near", "close to", "far from",
    "far away from", "away from", "across from", "opposite to",
    "adjacent to", "alongside", "at the side of", "attached to",
    "connected to", "with", "against", "detached from",
}

# Containment inverse paraphrase: original relation -> inverse wording.
CONTAINMENT_INVERSE_MAP = {
    "in": "contains",
    "inside": "contains",
    "within": "contains",
    "contains": "in",
}

# Relations deliberately NOT used, with the reason recorded in the validity
# table (soft = directionally plausible but not logically guaranteed;
# unsafe = logically invalid as a universal transform).
SOFT_EXCLUDED = {
    ("on top of", "beneath"): "contact condition makes the pair non-exclusive "
                              "(an object above without contact is neither)",
    ("over", "under"): "contact semantics of 'over' make exclusivity with "
                       "'on top of' ambiguous",
    ("ahead of", "at the back of"): "intrinsic-orientation reading of 'at the "
                                    "back of' is not equivalent to 'behind'",
    ("by", "beside"): "'by' is ambiguous (proximity vs. authorship) and is "
                      "not a verified symmetric relation",
    ("on", "off"): "contact-relation pair; not exhaustive (an object near but "
                   "not contacting is neither) and 'off' has directional uses",
    ("at", "near"): "'at' is region-ambiguous (at the edge of vs. in the "
                    "middle of); no strict complement partner",
    ("at the edge of", "in the middle of"): "region relations; not mutually "
                                            "exclusive with other regions",
    ("beyond", "in front of"): "directional distance reading; 'beyond' is "
                               "ambiguous (through vs. behind)",
    ("down from", "above"): "directional; 'down from' is not a strict "
                            "exhaustive complement of a single relation",
    ("outside", "inside"): "containment boundary relations; 'outside' does not "
                           "imply non-containment for open containers",
    ("out of", "in"): "directional (entering/leaving); not a static complement",
    ("facing", "facing away from"): "not complementary (two objects can face "
                                    "each other neither toward nor away; "
                                    "oblique orientations)",
}

UNSAFE_EXCLUDED = {
    ("parallel to", "perpendicular to"): "not a universal strict complement; "
                                         "oblique configurations make both false",
    ("toward", "away from"): "directional; not invertible by reversal",
    ("along", "across"): "directional/path semantics; reversal not symmetric",
    ("across", "alongside"): "path semantics; not a static spatial axis pair",
    ("around", "inside"): "enclosing-path semantics; not a strict complement",
    ("through", "in"): "path semantics (passing through); not a static "
                       "containment complement",
    ("into", "in"): "directional (entry); not a static complement",
    ("part of", "has as a part"): "mereology verbs; argument structure is not "
                                  "reversible by the VSR template and the "
                                  "inverse wording is not in the relation set",
    ("consists of", "part of"): "mereology; inverse requires re-parsing of "
                                "plural/collective subjects; excluded",
    ("enclosed by", "in"): "passive containment; inverse wording not in the "
                           "relation set",
    ("surrounding", "inside"): "collective subject semantics ('surrounding' "
                               "requires a plural surrounding object); excluded",
    ("in the middle of", "at the edge of"): "geometric region; two objects can "
                                            "be neither (offset within the "
                                            "region)",
}

# map: relation -> (transform, status, reason) for table generation
RELATION_TAXONOMY = {}
for _r, _c in STRICT_COMPLEMENT_PAIRS.items():
    RELATION_TAXONOMY[_r] = ("relcomp", "strict_included", "")
for _r in SYMMETRIC_RELATIONS:
    RELATION_TAXONOMY[_r] = ("sorev", "strict_included", "")
for _r in CONTAINMENT_INVERSE_MAP:
    RELATION_TAXONOMY[_r] = ("continv", "strict_included", "")
for (_r, _p), _reason in SOFT_EXCLUDED.items():
    RELATION_TAXONOMY[_r] = ("none", "soft_excluded", _reason)
for (_r, _p), _reason in UNSAFE_EXCLUDED.items():
    RELATION_TAXONOMY[_r] = ("none", "unsafe_excluded", _reason)

TRANSFORMS = ["relcomp", "sorev", "continv"]

LAW_NAMES = {
    "relcomp": "flip_law",
    "sorev": "stability_law",
    "continv": "paraphrase_law",
}

# --------------------------------------------------------------------------
# Subject/object parser audit (study plan section 18)
# --------------------------------------------------------------------------

_CONTAINS_VERBS = {"contains", "has as a part", "consists of"}


def parse_subject_object(statement: str, relation: str) -> tuple:
    """Parse (subject, object) from a VSR statement; (None, None) if unparsable.

    Template: "The <subject> is <relation> the <object>" or, for the
    contain-verb templates, "The <subject> <verb> the <object>".
    """
    text = statement.strip()
    if relation in _CONTAINS_VERBS:
        m = re.match(
            r"^The (.+?) " + re.escape(relation) + r" the (.+?)[.?!]?$",
            text, re.IGNORECASE,
        )
    else:
        m = re.match(
            r"^The (.+?) is " + re.escape(relation) + r" the (.+?)[.?!]?$",
            text, re.IGNORECASE,
        )
    if not m:
        return None, None
    subject, obj = m.group(1).strip(), m.group(2).strip()
    if not subject or not obj or subject.lower() == obj.lower():
        return None, None
    return subject, obj


def reconstruct_statement(subject: str, relation: str, obj: str) -> str:
    if relation in _CONTAINS_VERBS:
        return f"The {subject} {relation} the {obj}"
    return f"The {subject} is {relation} the {obj}"


def canonicalize_statement(text: str) -> str:
    """Strip framing whitespace and sentence-final punctuation for comparison.

    VSR captions may or may not carry a trailing period; transforms emit
    canonically unpunctuated statements, so comparisons must be punctuation-
    insensitive while raw outputs stay verbatim.
    """
    return text.strip().rstrip(".?!")


def audit_parser(records: list) -> dict:
    """Full parser audit over the frozen eligible set (study plan section 18).

    For every record reports success/failure and reconstruction equality.
    Returns stats dict; per-row results are attached in-place.
    """
    stats = {"total": 0, "parsed": 0, "parse_failed": 0, "reconstruct_failed": 0}
    for rec in records:
        stats["total"] += 1
        s, o = parse_subject_object(rec["statement"], rec["relation"])
        rec["audit_subject"], rec["audit_object"] = s, o
        if s is None:
            rec["audit_reason"] = "parse_failed"
            stats["parse_failed"] += 1
            continue
        rebuilt = reconstruct_statement(s, rec["relation"], o)
        if canonicalize_statement(rebuilt) != canonicalize_statement(rec["statement"]):
            rec["audit_reason"] = "reconstruct_failed"
            stats["reconstruct_failed"] += 1
            continue
        rec["audit_reason"] = "ok"
        stats["parsed"] += 1
    return stats


# --------------------------------------------------------------------------
# Transform builders (deterministic; every row carries expected behavior)
# --------------------------------------------------------------------------

def build_transform(record: dict, transform: str) -> dict:
    """Build the transformed input row for one record, or None if ineligible.

    Input record must already carry audit_subject/audit_object (see
    audit_parser). Returns a dict with:
      example_id, statement (transformed), original_statement, label,
      relation, family, expected_transformed_label, expected_prediction_behavior,
      transform_name, transform_version, transform_metadata, subject, object.
    """
    relation = record["relation"]
    label = bool(record["label"])
    s, o = record.get("audit_subject"), record.get("audit_object")
    if s is None or record.get("audit_reason") != "ok":
        return None

    base = {
        "example_id": record["example_id"],
        "original_statement": record["statement"].strip(),
        "label": label,
        "relation": relation,
        "family": record["family"],
        "subject": s,
        "object": o,
        "transform_version": config.TRANSFORM_VERSION_TIER_B,
    }

    if transform == "relcomp":
        if relation not in STRICT_COMPLEMENT_PAIRS:
            return None
        comp = STRICT_COMPLEMENT_PAIRS[relation]
        statement = reconstruct_statement(s, comp, o)
        if canonicalize_statement(statement) == canonicalize_statement(base["original_statement"]):
            return None
        return {
            **base,
            "statement": statement,
            "expected_transformed_label": (not label),
            "expected_prediction_behavior": LAW_NAMES["relcomp"],
            "transform_name": "relcomp",
            "transform_metadata": {
                "axis": "semantic",
                "transform": "relcomp",
                "law": LAW_NAMES["relcomp"],
                "original_relation": relation,
                "complement_relation": comp,
                "note": "strict complement; expected label flips",
            },
        }

    if transform == "sorev":
        if relation not in SYMMETRIC_RELATIONS:
            return None
        statement = reconstruct_statement(o, relation, s)
        if canonicalize_statement(statement) == canonicalize_statement(base["original_statement"]):
            return None
        return {
            **base,
            "statement": statement,
            "expected_transformed_label": label,
            "expected_prediction_behavior": LAW_NAMES["sorev"],
            "transform_name": "sorev",
            "transform_metadata": {
                "axis": "semantic",
                "transform": "sorev",
                "law": LAW_NAMES["sorev"],
                "relation": relation,
                "note": "symmetric relation; subject/object reversal keeps truth",
            },
        }

    if transform == "continv":
        if relation not in CONTAINMENT_INVERSE_MAP:
            return None
        if relation == "contains":
            statement = f"The {o} is in the {s}"
        else:
            statement = f"The {o} contains the {s}"
        if canonicalize_statement(statement) == canonicalize_statement(base["original_statement"]):
            return None
        return {
            **base,
            "statement": statement,
            "expected_transformed_label": label,
            "expected_prediction_behavior": LAW_NAMES["continv"],
            "transform_name": "continv",
            "transform_metadata": {
                "axis": "semantic",
                "transform": "continv",
                "law": LAW_NAMES["continv"],
                "original_relation": relation,
                "inverse_relation": CONTAINMENT_INVERSE_MAP[relation],
                "note": "containment inverse paraphrase; truth preserved",
            },
        }

    return None


def eligible_rows(records: list, transform: str) -> list:
    """All build_transform results for a transform, in frozen record order."""
    out = []
    for rec in records:
        row = build_transform(rec, transform)
        if row is not None:
            out.append(row)
    return out


# --------------------------------------------------------------------------
# Freeze artifacts: validity table + eligible IDs (committed pre-result)
# --------------------------------------------------------------------------

def _exclusion_reason(record: dict, transform: str) -> str:
    relation = record["relation"]
    if record.get("audit_reason") != "ok":
        return f"parser: {record.get('audit_reason')}"
    if transform == "relcomp":
        if relation not in STRICT_COMPLEMENT_PAIRS:
            return "relation not a strict complement pair"
    elif transform == "sorev":
        if relation not in SYMMETRIC_RELATIONS:
            return "relation not verified symmetric"
    elif transform == "continv":
        if relation not in CONTAINMENT_INVERSE_MAP:
            return "relation not a containment inverse pair"
    return ""


def build_validity_table(records: list) -> list:
    """One CSV row per relation x transform: status, reason, eligible counts."""
    audit_parser(records)
    rows = []
    for transform in TRANSFORMS:
        eligible_ids = set()
        for rec in records:
            row = build_transform(rec, transform)
            if row is not None:
                eligible_ids.add(rec["example_id"])
        for relation in sorted({r["relation"] for r in records}):
            n_el = sum(
                1 for r in records
                if r["relation"] == relation and r["example_id"] in eligible_ids
            )
            n_ex = sum(
                1 for r in records
                if r["relation"] == relation and r["example_id"] not in eligible_ids
            )
            if transform == "relcomp" and relation in _SOFT_RELCOMP_REASONS:
                status, reason = "soft_excluded", _SOFT_RELCOMP_REASONS[relation]
            elif transform == "relcomp" and relation in _UNSAFE_RELCOMP_REASONS:
                status, reason = "unsafe_excluded", _UNSAFE_RELCOMP_REASONS[relation]
            elif relation in STRICT_COMPLEMENT_PAIRS and transform == "relcomp":
                status, reason = "strict_included", ""
            elif relation in SYMMETRIC_RELATIONS and transform == "sorev":
                status, reason = "strict_included", ""
            elif relation in CONTAINMENT_INVERSE_MAP and transform == "continv":
                status, reason = "strict_included", ""
            else:
                status, reason = "not_in_scope", _not_in_scope_reason(relation, transform)
            rows.append({
                "transform": transform,
                "relation": relation,
                "status": status,
                "expected_truth_behavior": LAW_NAMES.get(transform, "na"),
                "reason": reason,
                "eligible_n": n_el,
                "excluded_n": n_ex,
            })
    return rows


_SOFT_RELCOMP_REASONS = {r1: reason for (r1, r2), reason in SOFT_EXCLUDED.items()}
_UNSAFE_RELCOMP_REASONS = {r1: reason for (r1, r2), reason in UNSAFE_EXCLUDED.items()}


def _not_in_scope_reason(relation: str, transform: str) -> str:
    if transform == "relcomp":
        return ("no strict complement partner for this relation in the VSR "
                "relation set (not mutually exclusive + exhaustive on one axis)")
    if transform == "sorev":
        return "relation not verified symmetric for this statement template"
    if transform == "continv":
        return "relation is not a containment inverse pair (in/inside/within/contains)"


def build_eligible_ids_doc(records: list) -> dict:
    """Deterministic eligible-ID document for all transforms (frozen)."""
    audit_parser(records)
    out = {
        "protocol_version": "v0.1",
        "authority": str(config.PROTOCOL_AUTHORITY.relative_to(config.REPO_ROOT)),
        "freeze_note": ("validity table and eligible IDs are committed before "
                        "any full Tier-B result is inspected; never regenerate "
                        "after results (study plan section 22)"),
        "parser_audit": audit_parser(records),
        "transforms": {},
    }
    for transform in TRANSFORMS:
        entries = {}
        for rec in records:
            row = build_transform(rec, transform)
            if row is None:
                continue
            entries[rec["example_id"]] = {
                "relation": row["relation"],
                "family": row["family"],
                "subject": row["subject"],
                "object": row["object"],
                "original_label": bool(row["label"]),
                "expected_transformed_label": bool(row["expected_transformed_label"]),
                "expected_prediction_behavior": row["expected_prediction_behavior"],
                "transformed_statement": row["statement"],
            }
        out["transforms"][transform] = {
            "law": LAW_NAMES[transform],
            "n_eligible": len(entries),
            "entries": entries,
        }
    return out


def write_freeze_files(records: list, force: bool = False) -> dict:
    """Write the two frozen Tier-B artifacts; refuse to overwrite unless forced."""
    if config.SEMANTIC_ELIGIBLE_FILE.exists() and not force:
        raise FileExistsError(
            f"{config.SEMANTIC_ELIGIBLE_FILE} already exists; use --force only "
            "with a decision-log entry (study plan section 22)"
        )
    rows = build_validity_table(records)
    config.PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SEMANTIC_VALIDITY_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    doc = build_eligible_ids_doc(records)
    with open(config.SEMANTIC_ELIGIBLE_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    return {
        "validity_file": str(config.SEMANTIC_VALIDITY_FILE.relative_to(config.REPO_ROOT)),
        "validity_sha256": config.sha256_file(config.SEMANTIC_VALIDITY_FILE),
        "eligible_file": str(config.SEMANTIC_ELIGIBLE_FILE.relative_to(config.REPO_ROOT)),
        "eligible_sha256": config.sha256_file(config.SEMANTIC_ELIGIBLE_FILE),
        "parser_audit": doc["parser_audit"],
        "n_eligible": {t: doc["transforms"][t]["n_eligible"] for t in TRANSFORMS},
    }
