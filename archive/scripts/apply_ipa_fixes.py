#!/usr/bin/env python3
"""Apply IPA transcriptions from UPA data using merkmal's UPA adapter.

Reads archive/cldf/forms.csv, converts UPA transcriptions to IPA segments,
applies language-specific post-processing, and writes back.

Usage:
    PYTHONPATH=~/repos/distfeat/src python3 archive/scripts/apply_ipa_fixes.py
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

from merkmal.upa import adapt

# Constants

FORMS_CSV = Path(__file__).resolve().parent.parent / "cldf" / "forms.csv"
LANGUAGES_CSV = Path(__file__).resolve().parent.parent / "cldf" / "languages.csv"

# Language IDs with geminate merging (doubled consonants -> length mark).
# Ingrian, Western Votic, Selkup have many; Komi-Zyrian, Komi-Permyak,
# Udmurt, Erzya have a few.
GEMINATE_LANG_IDS = {"208", "209", "907", "501", "503", "504", "301", "701"}

# Language IDs where post-consonant 'w' means labialization (ʷ).
LABIALIZATION_LANG_IDS = {"701", "807"}  # Sosva Mansi, Vakh-Vasyugan Khanty

# IPA-only language IDs (no UPA, IPA already filled in).
IPA_ONLY_LANG_IDS = {"108", "203", "210", "211", "601"}

# Ligature affricates -> decomposed two-character sequences.
AFFRICATE_DECOMPOSE: dict[str, str] = {
    "\u02A7": "t\u0283",  # ʧ -> tʃ
    "\u02A8": "t\u0255",  # ʨ -> tɕ
    "\u02A4": "d\u0292",  # ʤ -> dʒ
    "\u02A5": "d\u0291",  # ʥ -> dʑ
}

# Inverted breve above (U+0311) used in UPA for backing.
_INVERTED_BREVE_ABOVE = "\u0311"


# Language name lookup

def load_language_names() -> dict[str, str]:
    """Load language ID -> Name mapping from languages.csv."""
    names: dict[str, str] = {}
    with LANGUAGES_CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            names[row["ID"]] = row["Name"]
    return names


# IPA segmentation for IPA-only rows

# IPA modifier letters that attach to the preceding segment.
_IPA_MODIFIERS = frozenset([
    "\u02D0",  # ː length
    "\u02D1",  # ˑ half-length
    "\u02B0",  # ʰ aspiration
    "\u02B2",  # ʲ palatalization
    "\u02B7",  # ʷ labialization
    "\u02E0",  # ˠ velarization
    "\u02E4",  # ˤ pharyngealization
    "\u02BC",  # ʼ ejective
    "\u02C8",  # ˈ primary stress (prefix, but often attached)
    "\u207F",  # ⁿ nasal release
])


def segment_ipa(text: str) -> list[str]:
    """Segment an IPA string into individual sound tokens.

    Groups base characters with their combining marks and modifier letters.
    """
    nfd = unicodedata.normalize("NFD", text)
    segments: list[str] = []
    current: list[str] = []

    for ch in nfd:
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            # Combining mark: attach to current segment.
            if current:
                current.append(ch)
        elif ch in _IPA_MODIFIERS:
            # Modifier letter: attach to current segment.
            if current:
                current.append(ch)
        elif cat in ("Zs", "Cc"):
            # Whitespace/control: flush.
            if current:
                segments.append("".join(current))
                current = []
        elif ch in ("-", ".", ",", ":", ";", "(", ")", "[", "]", "/", " "):
            # Punctuation/boundaries: flush and skip.
            if current:
                segments.append("".join(current))
                current = []
        else:
            # New base character.
            # Check for tie bars / affricates: if the previous segment ends
            # with a tie bar (U+0361, U+035C), keep building.
            if current and current[-1] in ("\u0361", "\u035C"):
                current.append(ch)
            else:
                if current:
                    segments.append("".join(current))
                current = [ch]

    if current:
        segments.append("".join(current))

    return segments


# Pre-processing of UPA text before adapt()

def preprocess_upa(text: str) -> str:
    """Pre-process UPA text before passing to merkmal's adapt().

    - Replace ə + U+0311 (inverted breve above) with plain ə so that
      merkmal returns ə instead of ɤ.
    - Replace combining breve (U+0306, short vowel) with a placeholder
      so merkmal does not convert it to inverted breve below (non-syllabic).
      We restore it in post-processing.
    """
    # NFD-normalize first.
    nfd = unicodedata.normalize("NFD", text)
    # Remove inverted breve above after schwa.
    result = re.sub("\u0259" + _INVERTED_BREVE_ABOVE, "\u0259", nfd)
    # Replace combining breve with a placeholder.
    # We use U+FFFD (replacement character) as placeholder -- it will not appear
    # in UPA or IPA data. We restore it in post-processing.
    result = result.replace("\u0306", _BREVE_PLACEHOLDER)
    return result


_BREVE_PLACEHOLDER = "\uFFFF"  # private use, restored in post-processing


# Post-processing overrides

def apply_universal_overrides(segments: list[str]) -> list[str]:
    """Apply universal post-processing overrides to IPA segments.

    - Replace standalone 'a' with 'ɑ' (not when part of a larger segment
      like diphthongs/affricates).
    - Replace 'lʲ' with 'ʎ'.
    - Replace 'ʒʲ' with 'dʑ' (UPA ʒ́ is an affricate, not palatalized ʒ).
    - Decompose ligature affricates.
    - Replace non-syllabic marker (inverted breve below, U+032F) with
      breve (U+0306) for short vowels, matching UraLex IPA convention.
    """
    result: list[str] = []
    for seg in segments:
        # Decompose ligature affricates.
        for lig, decomposed in AFFRICATE_DECOMPOSE.items():
            seg = seg.replace(lig, decomposed)

        # Replace standalone 'a' with 'ɑ'.
        # A segment is "standalone a" if it equals 'a' possibly with
        # combining marks or length marks, but not if 'a' is embedded
        # in a multi-base-char segment (like an affricate).
        nfd_seg = unicodedata.normalize("NFD", seg)
        base_chars = [ch for ch in nfd_seg if not unicodedata.category(ch).startswith("M")
                      and ch not in ("\u02D0", "\u02D1", "\u02B2", "\u02B7", "\u02B0")]
        if base_chars == ["a"]:
            seg = seg.replace("a", "\u0251")  # ɑ

        # Replace 'lʲ' with 'ʎ'.
        if seg == "l\u02B2":
            seg = "\u028E"  # ʎ

        # Replace 'ʒʲ' with 'dʑ' (UPA ʒ́ = voiced alveolo-palatal affricate).
        if seg == "\u0292\u02B2":
            seg = "d\u0291"  # dʑ

        # Restore breve placeholder to actual combining breve (U+0306).
        # This preserves the distinction: UPA breve (short vowel) stays
        # as breve; UPA inverted breve below (non-syllabic) stays as
        # inverted breve below.
        seg = seg.replace(_BREVE_PLACEHOLDER, "\u0306")

        # Normalize g to ɡ (IPA script g, U+0261).
        seg = seg.replace("g", "\u0261")

        # Normalize combining ring below (U+0325) -- merkmal uses this
        # for devoicing, which is correct IPA. Keep as-is.

        result.append(seg)
    return result


def apply_geminate_merging(segments: list[str]) -> list[str]:
    """Merge consecutive identical consonant segments into geminate with ː.

    Only applied to Ingrian (208) and Western Votic (209).
    """
    if not segments:
        return segments

    result: list[str] = []
    i = 0
    while i < len(segments):
        if i + 1 < len(segments) and segments[i] == segments[i + 1]:
            # Check if it's a consonant (not a vowel).
            seg = segments[i]
            nfd_seg = unicodedata.normalize("NFD", seg)
            # Get the first base character to check if it's a consonant.
            first_base = ""
            for ch in nfd_seg:
                if not unicodedata.category(ch).startswith("M"):
                    first_base = ch
                    break
            # Simple vowel check: IPA vowels.
            vowels = set("aeiouyæøɛɔəɪʊɨʉɯɤɐɑɒœʌɜɞ")
            if first_base.lower() not in vowels:
                result.append(seg + "\u02D0")  # append ː
                i += 2
                continue
        result.append(segments[i])
        i += 1

    return result


# Form-to-UPA variant matching

def _normalize_for_matching(text: str) -> str:
    """Normalize a string for fuzzy matching between Form and UPA variants."""
    s = unicodedata.normalize("NFD", text.strip())
    # Remove hyphens, underscores, asterisks (reconstructed marker).
    s = s.replace("-", "").replace("_", "").replace("*", "")
    # Normalize schwa variants to IPA schwa (U+0259).
    s = s.replace("\u04D9", "\u0259")  # Cyrillic schwa
    s = s.replace("\u01DD", "\u0259")  # Latin turned e
    # Normalize č/tš: UPA č (c+caron) vs Form tš (t + s+caron).
    # After NFD, tš is t + s + combining_caron, č is c + combining_caron.
    # Replace ts+caron with c+caron.
    s = s.replace("ts\u030C", "c\u030C")
    # Also handle precomposed forms and digraph tš (without caron on s).
    s = s.replace("t\u0283", "c\u030C")  # tʃ -> č
    s = s.replace("tš", "c\u030C")
    # Normalize δ/ð: UPA δ (Greek delta) vs Form ð (Latin eth).
    s = s.replace("\u00F0", "\u03B4")  # ð -> δ
    # Normalize ḱ/kʹ: UPA ḱ (k + acute) vs Form kʹ (k + modifier prime).
    s = s.replace("\u02B9", "\u0301")  # modifier prime -> combining acute
    # Normalize ɜ/ə: some Forms use ɜ where UPA uses ə.
    s = s.replace("\u025C", "\u0259")  # ɜ -> ə
    # Normalize spaces (Form uses spaces, UPA uses underscores).
    s = s.replace(" ", "")
    return s


def match_form_to_upa_variant(form: str, variants: list[str]) -> str | None:
    """Find which UPA variant corresponds to the given Form.

    Returns the matched variant or None if no match found.
    """
    # Direct match.
    form_stripped = form.strip()
    for v in variants:
        if v.strip() == form_stripped:
            return v.strip()

    # NFD match.
    nfd_form = unicodedata.normalize("NFD", form_stripped)
    for v in variants:
        if unicodedata.normalize("NFD", v.strip()) == nfd_form:
            return v.strip()

    # Normalized fuzzy match.
    norm_form = _normalize_for_matching(form_stripped)
    for v in variants:
        if _normalize_for_matching(v.strip()) == norm_form:
            return v.strip()

    # If Form contains '~' (alternative separator), try matching each alt.
    if "~" in form_stripped:
        alts = [a.strip() for a in form_stripped.split("~")]
        for alt in alts:
            for v in variants:
                v_clean = v.strip()
                if _normalize_for_matching(alt) == _normalize_for_matching(v_clean):
                    return v_clean

    # Substring/prefix match as last resort: find the variant that shares
    # the longest common prefix with the form.
    norm_form = _normalize_for_matching(form_stripped)
    best_variant = None
    best_score = 0
    for v in variants:
        norm_v = _normalize_for_matching(v.strip())
        # Common prefix length.
        common = 0
        for a, b in zip(norm_form, norm_v):
            if a == b:
                common += 1
            else:
                break
        if common > best_score:
            best_score = common
            best_variant = v.strip()

    # Require at least 50% of the shorter string to match.
    if best_variant:
        min_len = min(len(norm_form), len(_normalize_for_matching(best_variant)))
        if min_len > 0 and best_score / min_len >= 0.5:
            return best_variant

    return None


# Main processing

def apply_labialization(segments: list[str]) -> list[str]:
    """Convert post-consonant 'w' to labialization modifier 'ʷ'.

    In Mansi/Khanty UPA, 'w' after a consonant means labialization,
    not a separate glide segment.
    """
    if len(segments) < 2:
        return segments

    result: list[str] = []
    vowels = set("aeiouyæøɛɔəɪʊɨʉɯɤɐɑɒœʌɜɞ")
    i = 0
    while i < len(segments):
        if (segments[i] == "w" and i > 0
                and result  # have a previous segment
                and result[-1][0].lower() not in vowels):
            # Attach as labialization to previous consonant.
            result[-1] = result[-1] + "\u02B7"  # ʷ
        else:
            result.append(segments[i])
        i += 1
    return result


def _adapt_single_word(word: str, lang_id: str) -> list[str]:
    """Adapt a single UPA word (no spaces, no commas) to IPA segments."""
    # Strip leading asterisk (reconstructed forms).
    word = word.lstrip("*")
    if not word:
        return []

    # Pre-process: replace ə̑ with ə, preserve breve.
    word = preprocess_upa(word)

    # Mansi-specific: low ring modifier (U+02F3) means labialization,
    # not devoicing. Replace with 'w' so adapt() produces a 'w' segment
    # that we then merge as labialization.
    if lang_id == "701":
        word = word.replace("\u02F3", "w")

    # Run merkmal's adapt().
    segments = adapt(word)

    # Apply universal overrides.
    segments = apply_universal_overrides(segments)

    # Apply labialization for Mansi: post-consonant 'w' → ʷ.
    if lang_id == "701":
        segments = apply_labialization(segments)

    # Apply geminate merging for specific languages.
    if lang_id in GEMINATE_LANG_IDS:
        segments = apply_geminate_merging(segments)

    return segments


def process_upa_row(
    upa_text: str,
    form: str,
    lang_id: str,
) -> tuple[str, str]:
    """Process a row with UPA data. Returns (item_IPA, Segments)."""
    upa_text = upa_text.strip()
    form = form.strip()

    if not upa_text:
        return ("", "")

    # Handle multi-form UPA (comma or ~ separated).
    if "," in upa_text or "~" in upa_text:
        variants = re.split(r"[,~]", upa_text)
        variants = [v.strip() for v in variants if v.strip()]

        # Check if the Form itself is also multi-form (contains ~ or ,).
        # If so, process all variants and join with ", ".
        form_has_multi = bool(re.search(r"[,~]", form))
        if form_has_multi:
            # Process each variant independently for item_IPA (comma-joined).
            # For Segments, use only the first variant -- multi-form rows
            # cannot have a meaningful single segmentation. A future revision
            # should split these into separate CLDF rows.
            all_ipa: list[str] = []
            first_seg: str = ""
            for i, v in enumerate(variants):
                ipa_v, seg_v = process_upa_row(v, v, lang_id)
                all_ipa.append(ipa_v)
                if i == 0:
                    first_seg = seg_v
            return (", ".join(all_ipa), first_seg)

        matched = match_form_to_upa_variant(form, variants)
        if matched is None:
            # Fallback: use first variant and log.
            print(f"  WARNING: Could not match Form {form!r} to UPA variants "
                  f"{variants!r}; using first variant", file=sys.stderr)
            matched = variants[0]
        upa_single = matched
    else:
        upa_single = upa_text

    # Split on spaces, underscores, and hyphens (preserving hyphens).
    # Use a regex that captures the separators.
    tokens = re.split(r"([\s_]+|-)", upa_single)
    all_segments: list[str] = []
    ipa_parts: list[str] = []

    for token in tokens:
        if not token or re.match(r"^[\s_]+$", token):
            # Whitespace separator: becomes a space in IPA.
            if ipa_parts and ipa_parts[-1] not in (" ", "-"):
                ipa_parts.append(" ")
        elif token == "-":
            # Hyphen: preserve as-is.
            ipa_parts.append("-")
        else:
            segs = _adapt_single_word(token, lang_id)
            all_segments.extend(segs)
            ipa_parts.append("".join(segs))

    ipa_str = "".join(ipa_parts)
    seg_str = " ".join(all_segments)

    return (ipa_str, seg_str)


def process_ipa_only_row(ipa_text: str) -> str:
    """Process an IPA-only row. Returns Segments string."""
    ipa_text = ipa_text.strip()
    if not ipa_text:
        return ""

    segments = segment_ipa(ipa_text)
    return " ".join(segments)


def main() -> None:
    """Main entry point."""
    print(f"Reading {FORMS_CSV}")
    lang_names = load_language_names()

    # Read all rows.
    with FORMS_CSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    print(f"Loaded {len(rows)} rows, {len(fieldnames)} columns")

    # Statistics.
    stats = {
        "upa_processed": 0,
        "ipa_changed": 0,
        "segments_filled": 0,
        "ipa_only_segmented": 0,
        "skipped_neither": 0,
        "multi_form_matched": 0,
        "multi_form_fallback": 0,
    }

    # Per-language stats.
    lang_stats: dict[str, dict[str, int]] = {}

    for row in rows:
        lang_id = row["Language_ID"]
        upa = row["item_UPA"].strip()
        ipa_existing = row["item_IPA"].strip()
        form = row["Form"].strip()

        if lang_id not in lang_stats:
            lang_stats[lang_id] = {"upa": 0, "ipa_only": 0, "neither": 0}

        if upa:
            # UPA row: convert to IPA.
            new_ipa, new_seg = process_upa_row(upa, form, lang_id)

            if new_ipa and new_ipa != ipa_existing:
                stats["ipa_changed"] += 1

            row["item_IPA"] = new_ipa
            row["Segments"] = new_seg
            stats["upa_processed"] += 1
            if new_seg:
                stats["segments_filled"] += 1
            lang_stats[lang_id]["upa"] += 1

        elif ipa_existing:
            # IPA-only row: segment existing IPA.
            new_seg = process_ipa_only_row(ipa_existing)
            row["Segments"] = new_seg
            stats["ipa_only_segmented"] += 1
            if new_seg:
                stats["segments_filled"] += 1
            lang_stats[lang_id]["ipa_only"] += 1

        else:
            # Neither UPA nor IPA: leave empty.
            stats["skipped_neither"] += 1
            lang_stats[lang_id]["neither"] += 1

    # Write back.
    print(f"Writing {FORMS_CSV}")
    with FORMS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print statistics.
    print()
    print("=" * 60)
    print("Statistics")
    print("=" * 60)
    print(f"  UPA rows processed:      {stats['upa_processed']}")
    print(f"  IPA values changed:      {stats['ipa_changed']}")
    print(f"  Segments filled:         {stats['segments_filled']}")
    print(f"  IPA-only rows segmented: {stats['ipa_only_segmented']}")
    print(f"  Rows with neither:       {stats['skipped_neither']}")
    print()
    print("Per-language breakdown:")
    print(f"  {'ID':<6} {'Name':<30} {'UPA':>6} {'IPA-only':>10} {'Neither':>10}")
    print(f"  {'-'*6} {'-'*30} {'-'*6} {'-'*10} {'-'*10}")
    for lid in sorted(lang_stats.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        ls = lang_stats[lid]
        name = lang_names.get(lid, "?")
        if ls["upa"] > 0 or ls["ipa_only"] > 0:
            print(f"  {lid:<6} {name:<30} {ls['upa']:>6} {ls['ipa_only']:>10} {ls['neither']:>10}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
