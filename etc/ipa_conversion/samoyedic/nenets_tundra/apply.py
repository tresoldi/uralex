"""Apply Tundra Nenets IPA conversion to all UraLex items and validate."""

import csv, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import validate_ipa_chars
from rules import convert, convert_and_segment

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URALEX = os.path.dirname(BASE)


def main():
    # Load UraLex data for nenets_tundra
    with open(os.path.join(URALEX, "raw", "Data.tsv")) as f:
        reader = csv.DictReader(f, delimiter="\t")
        all_rows = list(reader)

    rows = [r for r in all_rows if r["uralex_lang"].lower() == "nenets_tundra"
            and r.get("item", "").strip() and not r.get("status", "").strip()]

    # Load NEL crossref
    crossref = {}
    nel_path = os.path.join(os.path.dirname(__file__), "nel_crossref.tsv")
    with open(nel_path) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = (r["uralex_mng"], r["uralex_item"])
            crossref[key] = r

    # Convert all items
    output = []
    ipa_issues = []
    nel_matches = {"exact": 0, "close": 0, "different_word": 0, "mismatch": 0, "no_nel": 0}

    for r in rows:
        item = r["item"].strip()
        mng = r["uralex_mng"].strip()
        ipa, segments = convert_and_segment(item)

        # Validate IPA characters
        bad_chars = validate_ipa_chars(ipa)
        if bad_chars:
            ipa_issues.append((mng, item, ipa, bad_chars))

        # Compare with NEL
        nel = crossref.get((mng, item))
        nel_ipa = ""
        nel_status = "no_nel"
        if nel and nel["nel_form"]:
            nel_ipa = nel["nel_segments"].replace(" ", "")
            nel_value = nel["nel_value"].lower()
            if item.lower() != nel_value:
                nel_status = "different_word"
            elif ipa == nel_ipa:
                nel_status = "exact"
            else:
                # Check if close (only known systematic differences)
                # Our e vs NEL ɛ, our o vs NEL ɔ, our u vs NEL ʊ, our ø vs NEL œ, our h vs NEL x
                normalized_ours = ipa.replace("e", "ɛ").replace("o", "ɔ").replace("u", "ʊ").replace("ø", "œ")
                normalized_nel = nel_ipa.replace("x", "h")
                if normalized_ours == normalized_nel:
                    nel_status = "close"
                else:
                    nel_status = "mismatch"

        nel_matches[nel_status] += 1

        output.append({
            "uralex_mng": mng,
            "item": item,
            "item_ipa": ipa,
            "segments": segments,
            "nel_ipa": nel_ipa,
            "nel_status": nel_status,
        })

    # Write output
    out_path = os.path.join(os.path.dirname(__file__), "output.tsv")
    with open(out_path, "w") as f:
        cols = ["uralex_mng", "item", "item_ipa", "segments", "nel_ipa", "nel_status"]
        f.write("\t".join(cols) + "\n")
        for o in output:
            f.write("\t".join(o[c] for c in cols) + "\n")

    # Report
    print(f"=== Tundra Nenets IPA conversion ===")
    print(f"Total items: {len(rows)}")
    print(f"IPA character issues: {len(ipa_issues)}")
    print(f"\nNEL comparison:")
    for k, v in nel_matches.items():
        print(f"  {k}: {v}")

    if ipa_issues:
        print(f"\nIPA issues:")
        for mng, item, ipa, bad in ipa_issues[:10]:
            print(f"  {mng}: {item} -> {ipa} -- bad chars: {bad}")

    # Show mismatches
    mismatches = [o for o in output if o["nel_status"] == "mismatch"]
    if mismatches:
        print(f"\nMismatches with NEL ({len(mismatches)}):")
        for o in mismatches[:20]:
            print(f"  {o['uralex_mng']:<18} {o['item']:<20} ours={o['item_ipa']:<20} NEL={o['nel_ipa']}")


if __name__ == "__main__":
    main()
