"""Apply IPA→UPA reverse conversion for all 4 languages and integrate."""

import csv
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_reverse import expand_length, strip_narrow_diacritics, apply_reverse_rules

BASE = os.path.dirname(os.path.abspath(__file__))
URALEX = os.path.dirname(os.path.dirname(BASE))


# === Per-language IPA->UPA rules ===

ESTONIAN_RULES = [
    ("ɑ", "a"),
    ("æ", "ä"),
    ("ɤ", "ə̑"),
    ("ø", "ö"),
    ("y", "ü"),
    ("ʔ", "ˀ"),
    ("ŋ", "ŋ"),
    ("ɣ", "ɣ"),
]

FINNISH_RULES = [
    ("ɑ", "a"),
    ("æ", "ä"),
    ("ø", "ö"),
    ("y", "ü"),
    ("ɦ", "h"),      # voiced glottal fricative -> plain h in UPA
    ("ç", "h"),       # voiceless palatal fricative (allophone of h) -> h
    ("ʋ", "v"),       # labiodental approximant -> v
    ("ŋ", "ŋ"),
    ("x", "h"),       # voiceless velar fricative (allophone of h) -> h
]

HUNGARIAN_RULES = [
    # Affricates (must come before single chars)
    ("t͡ʃ", "č"),
    ("d͡ʒ", "ǯ"),
    ("t͡s", "c"),
    ("d͡z", "ʒ́"),     # voiced alveolar affricate... actually use dz

    # Vowels
    ("ɛ", "e"),
    ("ɒ", "a"),       # open back rounded -> a in UPA (Hungarian-specific)
    ("ø", "ö"),
    ("y", "ü"),
    ("ɡ", "g"),       # IPA g -> Latin g

    # Consonants
    ("ʃ", "š"),
    ("ʒ", "ž"),
    ("ɲ", "ń"),
    ("ɟ", "ǵ"),       # voiced palatal stop
    ("ɦ", "h"),
    ("ŋ", "ŋ"),
    ("ɾ", "r"),       # tap -> r
]

KILDIN_RULES = [
    # Palatalization
    ("ʲ", "ʹ"),       # palatalization -> modifier prime

    # Consonants
    ("ʃ", "š"),
    ("ʒ", "ž"),
    ("ɲ", "ń"),
    ("ʎ", "lʹ"),      # palatal lateral -> l + prime (will get ʹ from ʲ too)
    ("ɨ", "ə̑"),       # close central unrounded -> UPA convention

    # Vowels
    ("ɒ", "a"),        # open back rounded
]


def convert_estonian(ipa):
    text = strip_narrow_diacritics(ipa)
    text = expand_length(text)
    return apply_reverse_rules(text, ESTONIAN_RULES)


def convert_finnish(ipa):
    text = strip_narrow_diacritics(ipa)
    text = expand_length(text)
    return apply_reverse_rules(text, FINNISH_RULES)


def convert_hungarian(ipa):
    text = strip_narrow_diacritics(ipa)
    text = expand_length(text)
    return apply_reverse_rules(text, HUNGARIAN_RULES)


def convert_kildin(ipa):
    text = strip_narrow_diacritics(ipa)
    text = expand_length(text)
    return apply_reverse_rules(text, KILDIN_RULES)


CONVERTERS = {
    "estonian_standard": convert_estonian,
    "finnish_standard": convert_finnish,
    "hungarian": convert_hungarian,
    "saami_kildin": convert_kildin,
}


def main():
    data_path = os.path.join(URALEX, "raw", "Data.tsv")
    with open(data_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    filled = 0
    skipped = 0
    per_lang = {}

    for row in rows:
        lang = row["uralex_lang"]
        if lang not in CONVERTERS:
            continue

        ipa = row.get("item_ipa", "").strip()
        upa = row.get("item_upa", "").strip()
        status = row.get("status", "").strip()

        if status or not ipa:
            continue

        # Don't overwrite existing UPA
        if upa:
            skipped += 1
            continue

        converter = CONVERTERS[lang]
        new_upa = converter(ipa)
        row["item_upa"] = new_upa
        filled += 1
        per_lang[lang] = per_lang.get(lang, 0) + 1

    print(f"Reverse UPA integration:")
    print(f"  Filled: {filled}")
    print(f"  Skipped (existing UPA): {skipped}")
    for lang in sorted(per_lang):
        print(f"  {lang}: {per_lang[lang]}")

    # Show samples
    print("\n=== Samples ===")
    for lang in sorted(CONVERTERS):
        print(f"\n{lang}:")
        count = 0
        for row in rows:
            if row["uralex_lang"] == lang and row.get("item_ipa", "").strip() and row.get("item_upa", "").strip():
                print(f"  {row['item']:<22} IPA:{row['item_ipa']:<22} UPA:{row['item_upa']}")
                count += 1
                if count >= 8:
                    break

    # Write back
    with open(data_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote to {data_path}")


if __name__ == "__main__":
    main()
