# Orientation Heuristic Subset — Definition & Justification

**Status: FROZEN (preregistered 2026-08-09) before evaluation. Non-official,
supporting subset only — never the headline result.**

## Why this subset exists

The official SITE-Bench release (`franky-veteran/SITE-Bench`) provides only
six coarse `category` labels per example:
counting & existence · object localization & positioning ·
3d information understanding · multi-view & cross-image reasoning ·
spatial relationship reasoning · movement prediction & navigation.

It provides **no per-example orientation tag**, even though the paper's
taxonomy describes "spatial visualization and orientation" as an SI factor.
Our VSR finding is specifically about **object/direction-related
orientation** (facing / facing-away, front / behind, parallel /
perpendicular). No official SITE subset isolates that, so we constructed one
with a transparent keyword heuristic — clearly labeled non-official in every
report.

## Definition

A SITE example belongs to the orientation-heuristic subset iff its
**question text or any text option** contains at least one of the keywords
below (case-insensitive, word-boundary match). `<image>` placeholders are
excluded from matching.

### Keyword list (`src/datasets/site.py` → `ORIENTATION_KEYWORDS`)

```
orientation, oriented, orient,
facing, face, faces,
direction, directional,
view, viewpoint, view angle,
angle, turned, rotate, rotated, rotation,
toward, towards, away from,
left, right, front, behind, in front of,
parallel, perpendicular,
clockwise, counterclockwise
```

### Examples of matched questions

- "Is the camera taking the photo looking up or down?"
- "what is on the left of the person in yellow clothes"
- "the fire hydrant is in the upper-right quadrant of the image."
- "which object is facing the camera"

## Numbers

| | n |
|---|---|
| Full heuristic subset (images + videos) | 3,272 |
| Image-only (used in step-1 zero-shot report) | 1,824 |
| By modality (full subset) | single-image 1,012 · multi-image 1,012 · video 1,248 |
| Top source datasets (full subset) | MVBench 404 · VSIBench 324 · exoego4d 316 · egoexo4d 288 · ActivityNetQA 269 |

Example IDs are **frozen** in `results/site/site_protocol.json`
(`frozen_ids.secondary`).

## Known limitations (why it is supporting, not headline)

1. **Keyword-derived, not curated**: noise both ways — misses orientation
   questions phrased without keywords, and may catch non-orientation
   questions (e.g., "left" in a non-spatial sense).
2. **Not official**: reviewers can attack the construction; that is why the
   preregistration designates the official `spatial relationship reasoning`
   category as the headline subset and this one as corroborating evidence.
3. Heuristic matches the question/option TEXT only; it does not verify that
   the image content involves orientation.

## Usage in the project

- `src/datasets/site.py` → `get_orientation_subset(records)`
- `results/site/site_protocol.json` → `subsets.secondary` (frozen IDs)
- `results/site/zeroshot_image_report.md` → step-1 result:
  image-only orientation subset raw 47.3% / CAA 22.6% (vs 31.1% overall,
  59.2% primary) — the VSR orientation weakness generalizes to SITE.
- Related docs: `results/site/site_protocol.md`, `results/site/site_dataset_report.md`.
