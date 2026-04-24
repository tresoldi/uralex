"""Apply Ume Saami IPA conversion to all UraLex items and validate."""

import csv, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import validate_ipa_chars
from rules import convert, convert_and_segment

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URALEX = os.path.dirname(BASE)


def main():
    with open(os.path.join(URALEX, "raw", "Data.tsv")) as f:
        reader = csv.DictReader(f, delimiter="\t")
        all_rows = list(reader)

    rows = [r for r in all_rows if r["uralex_lang"].lower() == "saami_ume"
            and r.get("item", "").strip() and not r.get("status", "").strip()]

    # Convert all items
    output = []
    ipa_issues = []

    for r in rows:
        item = r["item"].strip()
        mng = r["uralex_mng"].strip()
        ipa, segments = convert_and_segment(item)

        bad_chars = validate_ipa_chars(ipa)
        if bad_chars:
            ipa_issues.append((mng, item, ipa, bad_chars))

        output.append({
            "uralex_mng": mng,
            "item": item,
            "item_ipa": ipa,
            "segments": segments,
        })

    # Write output
    out_path = os.path.join(os.path.dirname(__file__), "output.tsv")
    with open(out_path, "w") as f:
        cols = ["uralex_mng", "item", "item_ipa", "segments"]
        f.write("\t".join(cols) + "\n")
        for o in output:
            f.write("\t".join(o[c] for c in cols) + "\n")

    # Report
    print(f"=== Ume Saami IPA conversion ===")
    print(f"Total items: {len(rows)}")
    print(f"IPA character issues: {len(ipa_issues)}")

    if ipa_issues:
        print(f"\nIPA issues:")
        for mng, item, ipa, bad in ipa_issues[:10]:
            print(f"  {mng}: {item} -> {ipa} -- bad chars: {bad}")

    # Show phonological inventory
    from collections import Counter
    seg_counts = Counter()
    for o in output:
        for seg in o["segments"].split():
            seg_counts[seg] += 1
    print(f"\nSegment inventory ({len(seg_counts)} unique segments):")
    for seg, count in seg_counts.most_common():
        print(f"  {seg:<6} {count}")


if __name__ == "__main__":
    main()
