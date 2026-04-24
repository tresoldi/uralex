#!/usr/bin/env python3
"""Compare existing item_IPA with merkmal's UPA-to-IPA conversion.

Produces a structured discrepancy report grouped by language and type.
"""

import csv
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# merkmal must be importable (pip install -e from distfeat)
from merkmal.upa import adapt, adapt_segment, segment_upa


def normalize_ipa(s: str) -> str:
    """NFD-normalize and strip leading asterisks (reconstructed forms)."""
    s = s.lstrip("*")
    return unicodedata.normalize("NFD", s)


def segments_to_string(segments: list[str]) -> str:
    """Join IPA segments back into a single string."""
    return "".join(segments)


def classify_discrepancy(upa: str, existing_ipa: str, merkmal_ipa: str) -> str:
    """Classify the type of discrepancy."""
    # Normalize both for comparison
    e_nfd = unicodedata.normalize("NFD", existing_ipa)
    m_nfd = unicodedata.normalize("NFD", merkmal_ipa)

    if e_nfd == m_nfd:
        return "match"

    # Check if it's just NFC vs NFD
    if unicodedata.normalize("NFC", existing_ipa) == unicodedata.normalize("NFC", merkmal_ipa):
        return "encoding:nfc-vs-nfd"

    # Check for systematic vowel mapping differences
    vowel_pairs = {
        ("a", "ɑ"), ("ɑ", "a"),
        ("ɨ", "ɯ"), ("ɯ", "ɨ"),
    }
    # Compare character by character after NFD
    if len(e_nfd) == len(m_nfd):
        diffs = [(e, m) for e, m in zip(e_nfd, m_nfd) if e != m]
        if all((e, m) in vowel_pairs or (m, e) in vowel_pairs for e, m in diffs):
            pairs_str = ", ".join(f"{e}→{m}" for e, m in diffs)
            return f"systematic:{pairs_str}"

    return "other"


def main():
    forms_path = Path(__file__).parent.parent / "cldf" / "forms.csv"
    langs_path = Path(__file__).parent.parent / "cldf" / "languages.csv"

    # Load language names
    lang_names = {}
    with open(langs_path) as f:
        for row in csv.DictReader(f):
            lang_names[row["ID"]] = row["Name"]

    # Process forms
    stats = {
        "total": 0,
        "has_upa_and_ipa": 0,
        "ipa_only": 0,
        "neither": 0,
        "match": 0,
        "mismatch": 0,
    }
    discrepancies = []  # list of dicts
    by_language = defaultdict(lambda: {"total": 0, "match": 0, "mismatch": 0})
    by_type = defaultdict(int)
    errors = []  # merkmal adapter errors

    with open(forms_path) as f:
        for row in csv.DictReader(f):
            stats["total"] += 1
            upa = row["item_UPA"].strip()
            ipa = row["item_IPA"].strip()
            lang_id = row["Language_ID"]
            lang_name = lang_names.get(lang_id, lang_id)

            if not upa and not ipa:
                stats["neither"] += 1
                continue
            if not upa and ipa:
                stats["ipa_only"] += 1
                continue

            stats["has_upa_and_ipa"] += 1
            by_language[lang_name]["total"] += 1

            # Skip reconstructed forms (Proto-Uralic)
            clean_upa = upa.lstrip("*")
            if not clean_upa:
                continue

            try:
                segments = adapt(clean_upa)
                merkmal_ipa = segments_to_string(segments)
            except Exception as e:
                errors.append({
                    "lang": lang_name,
                    "id": row["ID"],
                    "upa": upa,
                    "ipa": ipa,
                    "error": str(e),
                })
                continue

            clean_ipa = ipa.lstrip("*")
            disc_type = classify_discrepancy(clean_upa, clean_ipa, merkmal_ipa)

            if disc_type == "match":
                stats["match"] += 1
                by_language[lang_name]["match"] += 1
            else:
                stats["mismatch"] += 1
                by_language[lang_name]["mismatch"] += 1
                by_type[disc_type] += 1
                discrepancies.append({
                    "lang": lang_name,
                    "lang_id": lang_id,
                    "id": row["ID"],
                    "form": row["Form"],
                    "upa": upa,
                    "existing_ipa": ipa,
                    "merkmal_ipa": merkmal_ipa,
                    "merkmal_segments": " ".join(segments),
                    "type": disc_type,
                })

    # === Print report ===
    print("# UraLex IPA discrepancy report")
    print()
    print("## Overview")
    print()
    print(f"- Total forms: {stats['total']}")
    print(f"- With UPA+IPA: {stats['has_upa_and_ipa']}")
    print(f"- IPA only: {stats['ipa_only']}")
    print(f"- Neither: {stats['neither']}")
    print(f"- Match (UPA→IPA agrees): {stats['match']}")
    print(f"- Mismatch: {stats['mismatch']}")
    print()

    if errors:
        print("## Adapter errors")
        print()
        for e in errors:
            print(f"- {e['lang']} ({e['id']}): UPA `{e['upa']}` -- {e['error']}")
        print()

    print("## By language")
    print()
    print(f"| Language | Total | Match | Mismatch | % match |")
    print(f"|----------|-------|-------|----------|---------|")
    for lang in sorted(by_language):
        d = by_language[lang]
        pct = 100 * d["match"] / d["total"] if d["total"] else 0
        print(f"| {lang} | {d['total']} | {d['match']} | {d['mismatch']} | {pct:.0f}% |")
    print()

    print("## By discrepancy type")
    print()
    for dtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"- `{dtype}`: {count}")
    print()

    # Group discrepancies by language, then show examples
    print("## Discrepancies by language")
    print()
    by_lang_disc = defaultdict(list)
    for d in discrepancies:
        by_lang_disc[d["lang"]].append(d)

    for lang in sorted(by_lang_disc):
        items = by_lang_disc[lang]
        print(f"### {lang} ({len(items)} discrepancies)")
        print()
        print(f"| Form | UPA | Existing IPA | merkmal IPA | Type |")
        print(f"|------|-----|-------------|-------------|------|")
        for d in items:
            print(f"| {d['form']} | {d['upa']} | {d['existing_ipa']} | {d['merkmal_ipa']} | {d['type']} |")
        print()

    # Also write a CSV for machine processing
    csv_path = Path(__file__).parent / "discrepancies.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "lang", "lang_id", "id", "form", "upa",
            "existing_ipa", "merkmal_ipa", "merkmal_segments", "type",
        ])
        writer.writeheader()
        writer.writerows(discrepancies)
    print(f"CSV written to {csv_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
