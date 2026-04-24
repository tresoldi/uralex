"""Integrate IPA conversions from research into raw/Data.tsv."""

import csv
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
URALEX = os.path.dirname(BASE)

# Language -> (family_folder, lang_folder)
LANG_PATHS = {
    "karelian_proper": ("finnic", "karelian_proper"),
    "veps": ("finnic", "veps"),
    "estonian_south": ("finnic", "estonian_south"),
    "livonian_courland": ("finnic", "livonian_courland"),
    "saami_north": ("saami", "saami_north"),
    "saami_inari": ("saami", "saami_inari"),
    "saami_skolt": ("saami", "saami_skolt"),
    "saami_south": ("saami", "saami_south"),
    "saami_pite": ("saami", "saami_pite"),
    "saami_ume": ("saami", "saami_ume"),
    "mari_hill": ("volgaic", "mari_hill"),
    "moksha": ("volgaic", "moksha"),
    "nenets_tundra": ("samoyedic", "nenets_tundra"),
    "proto_uralic": ("reconstruction", "proto_uralic"),
}


def load_ipa_output(family, lang):
    """Load IPA conversion output for a language."""
    path = os.path.join(BASE, family, lang, "output.tsv")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found")
        return {}

    lookup = {}
    with open(path) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = (r["uralex_mng"], r["item"])
            lookup[key] = (r["item_ipa"], r["segments"])
    return lookup


def main():
    # Load raw data
    data_path = os.path.join(URALEX, "raw", "Data.tsv")
    with open(data_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from raw/Data.tsv")
    print(f"Columns: {fieldnames}")

    # Load all IPA outputs
    all_ipa = {}
    for lang, (family, folder) in LANG_PATHS.items():
        lookup = load_ipa_output(family, folder)
        all_ipa[lang] = lookup
        print(f"  {lang}: {len(lookup)} IPA entries loaded")

    # Integrate
    filled = 0
    skipped_existing = 0
    skipped_no_match = 0
    skipped_status = 0
    per_lang = {}

    for row in rows:
        lang = row["uralex_lang"]
        if lang not in all_ipa:
            continue

        mng = row["uralex_mng"]
        item = row["item"].strip()
        status = row.get("status", "").strip()

        # Skip status rows (no form)
        if status:
            skipped_status += 1
            continue

        # Skip if no item
        if not item:
            continue

        # Skip if already has IPA
        if row["item_ipa"].strip():
            skipped_existing += 1
            continue

        # Look up IPA
        key = (mng, item)
        if key in all_ipa[lang]:
            ipa, segments = all_ipa[lang][key]
            row["item_ipa"] = ipa
            row["segments"] = segments
            filled += 1
            per_lang[lang] = per_lang.get(lang, 0) + 1
        else:
            skipped_no_match += 1

    print(f"\nIntegration results:")
    print(f"  Filled: {filled}")
    print(f"  Skipped (existing IPA): {skipped_existing}")
    print(f"  Skipped (status row): {skipped_status}")
    print(f"  Skipped (no match): {skipped_no_match}")
    print(f"\nPer language:")
    for lang in sorted(per_lang):
        print(f"  {lang}: {per_lang[lang]}")

    # Write back
    with open(data_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {data_path}")


if __name__ == "__main__":
    main()
