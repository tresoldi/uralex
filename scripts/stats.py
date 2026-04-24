#!/usr/bin/env python3
"""
Print dataset statistics from the raw data directory.

Usage:
    python3 scripts/stats.py [directory]

Default directory: raw/
"""

import csv
import os
import sys
from collections import Counter


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "raw"
    data_path = os.path.join(data_dir, "Data.tsv")

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # Normalize column names for old/new format
        rows = []
        for row in reader:
            norm = {}
            for k, v in row.items():
                norm[k.lower()] = v
            rows.append(norm)

    langs = sorted(set(r["uralex_lang"] for r in rows))
    mngs = sorted(set(r["uralex_mng"] for r in rows))

    # Detect format (new has "status" column, old has markers in "item")
    has_status_col = "status" in rows[0]
    status_markers = {"[No equivalent]", "[Form not found]", "[Not reconstructable]"}

    status_count = 0
    form_count = 0
    with_ipa = 0
    with_upa = 0
    with_seg = 0
    with_borr = 0
    forms_per_pair = Counter()

    for r in rows:
        is_status = False
        if has_status_col:
            is_status = bool(r.get("status", ""))
        else:
            is_status = r.get("item", "") in status_markers

        if is_status:
            status_count += 1
        else:
            form_count += 1
            forms_per_pair[(r["uralex_lang"], r["uralex_mng"])] += 1

        if r.get("item_ipa", ""):
            with_ipa += 1
        if r.get("item_upa", ""):
            with_upa += 1
        if r.get("segments", ""):
            with_seg += 1
        if r.get("borr_source", ""):
            with_borr += 1

    synonymy = form_count / len(forms_per_pair) if forms_per_pair else 0

    upa_langs = sorted(set(r["uralex_lang"] for r in rows if r.get("item_upa", "")))
    ipa_langs = sorted(set(r["uralex_lang"] for r in rows if r.get("item_ipa", "")))

    print(f"- **Languages:** {len(langs)} (including Proto-Uralic)")
    print(f"- **Meanings:** {len(mngs)}")
    print(f"- **Rows:** {len(rows)} ({form_count} lexical forms, {status_count} status entries)")
    print(f"- **Synonymy:** {synonymy:.2f}")
    print(f"- **With UPA transcription:** {with_upa} ({len(upa_langs)} languages)")
    print(f"- **With IPA transcription:** {with_ipa} ({len(ipa_langs)} languages)")
    print(f"- **With segments:** {with_seg}")
    print(f"- **Borrowings:** {with_borr}")


if __name__ == "__main__":
    main()
