"""Fill the remaining 112 items missing IPA."""

import csv
import os
import unicodedata
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "shared"))
from conversion_utils import apply_rules, segment_ipa

URALEX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# === Hungarian orthography -> IPA ===

HUNGARIAN_RULES = [
    # Digraphs (must come first)
    ("dzs", "d͡ʒ"),
    ("dz", "d͡z"),
    ("cs", "t͡ʃ"),
    ("sz", "s"),       # orthographic sz = /s/
    ("zs", "ʒ"),
    ("gy", "ɟ"),
    ("ny", "ɲ"),
    ("ty", "c"),
    ("ly", "j"),       # historical ly = /j/ in modern Hungarian

    # Long vowels (accented)
    ("á", "aː"),
    ("é", "eː"),
    ("í", "iː"),
    ("ó", "oː"),
    ("ú", "uː"),
    ("ö", "ø"),
    ("ü", "y"),
    ("ő", "øː"),
    ("ű", "yː"),

    # Short vowels
    ("a", "ɒ"),        # Hungarian a = open back rounded
    ("e", "ɛ"),        # Hungarian e = open-mid front
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants
    ("s", "ʃ"),        # orthographic s = /ʃ/ in Hungarian!
    ("c", "t͡s"),
    ("g", "ɡ"),
    ("j", "j"),
]

def convert_hungarian(text):
    text = text.lower().replace("(", "").replace(")", "")
    return apply_rules(text, HUNGARIAN_RULES)


# === Estonian Standard orthography -> IPA ===

ESTONIAN_RULES = [
    # Double vowels/consonants
    ("aa", "ɑː"), ("ee", "eː"), ("ii", "iː"), ("oo", "oː"), ("uu", "uː"),
    ("ää", "æː"), ("öö", "øː"), ("üü", "yː"), ("õõ", "ɤː"),
    ("kk", "kː"), ("pp", "pː"), ("tt", "tː"), ("ss", "sː"),
    ("ll", "lː"), ("mm", "mː"), ("nn", "nː"), ("rr", "rː"),

    # Vowels
    ("õ", "ɤ"),
    ("ä", "æ"),
    ("ö", "ø"),
    ("ü", "y"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
]

def convert_estonian(text):
    text = text.lower().replace("(", "").replace(")", "")
    return apply_rules(text, ESTONIAN_RULES)


# === Finnish Standard orthography -> IPA ===

FINNISH_RULES = [
    # Double vowels/consonants -> long
    ("aa", "ɑː"), ("ee", "eː"), ("ii", "iː"), ("oo", "oː"), ("uu", "uː"),
    ("ää", "æː"), ("öö", "øː"), ("yy", "yː"),
    ("kk", "kː"), ("pp", "pː"), ("tt", "tː"), ("ss", "sː"),
    ("ll", "lː"), ("mm", "mː"), ("nn", "nː"), ("rr", "rː"),

    # Vowels
    ("ä", "æ"),
    ("ö", "ø"),
    ("y", "y"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
]

def convert_finnish(text):
    text = text.lower().replace("(", "").replace(")", "")
    return apply_rules(text, FINNISH_RULES)


# === Votic Western (Finnish-like) -> IPA ===

VOTIC_RULES = [
    # Digraphs
    ("tš", "t͡ʃ"),

    # Double vowels/consonants -> long
    ("aa", "ɑː"), ("ee", "eː"), ("ii", "iː"), ("oo", "oː"), ("uu", "uː"),
    ("ää", "æː"), ("öö", "øː"), ("üü", "yː"),
    ("kk", "kː"), ("pp", "pː"), ("tt", "tː"), ("ss", "sː"),
    ("ll", "lː"), ("mm", "mː"), ("nn", "nː"), ("rr", "rː"),

    # Special vowels
    ("ä", "æ"),
    ("ö", "ø"),
    ("ü", "y"),
    ("õ", "ɤ"),
    ("ǟ", "æː"),

    # Basic vowels
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    ("š", "ʃ"),
]

def convert_votic(text):
    text = text.lower().replace("(", "").replace(")", "")
    return apply_rules(text, VOTIC_RULES)


# === UPA-notation languages (already covered, fill gaps) ===
# These use notation similar to what merkmal handles, but without merkmal
# we do direct character mapping

def preprocess_upa(text):
    """Normalize UPA-like notation."""
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    text = text.replace("'", "ʹ")  # apostrophe -> prime
    # Handle combining breve below (i̮ -> ɨ)
    nfd = unicodedata.normalize("NFD", text)
    result = []
    i = 0
    while i < len(nfd):
        if i + 1 < len(nfd) and nfd[i + 1] == "\u032E":
            base = nfd[i]
            if base == "i":
                result.append("ɨ")
            elif base == "e":
                result.append("ə")  # e̮ -> ə in some notations
            elif base == "u":
                result.append("ʉ")
            else:
                result.append(base)
            i += 2
        # Handle combining inverted breve above (ə̑ -> ə)
        elif i + 1 < len(nfd) and nfd[i + 1] == "\u0311":
            result.append(nfd[i])  # just keep base
            i += 2
        else:
            result.append(nfd[i])
            i += 1
    text = unicodedata.normalize("NFC", "".join(result))
    # Handle macron vowels
    for v, long in [("ā", "ɑː"), ("ē", "eː"), ("ī", "iː"), ("ō", "oː"), ("ū", "uː")]:
        text = text.replace(v, long)
    return text


UPA_RULES = [
    # Palatalized consonants
    ("ś", "sʲ"), ("ź", "zʲ"), ("ń", "nʲ"), ("ŕ", "rʲ"),
    ("ĺ", "lʲ"), ("ć", "t͡sʲ"),
    ("t´", "tʲ"), ("d´", "dʲ"),  # with backtick

    # Prime-based palatalization
    ("lʹ", "lʲ"), ("nʹ", "nʲ"), ("rʹ", "rʲ"), ("sʹ", "sʲ"),
    ("tʹ", "tʲ"), ("dʹ", "dʲ"), ("kʹ", "kʲ"), ("mʹ", "mʲ"),
    ("bʹ", "bʲ"), ("pʹ", "pʲ"), ("vʹ", "vʲ"), ("zʹ", "zʲ"),
    ("gʹ", "ɡʲ"), ("čʹ", "t͡ʃʲ"),

    # Affricates
    ("č̣", "t͡ʃ"),    # č with dot below (Khanty)
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("cc", "t͡sː"),
    ("c", "t͡s"),

    # Fricatives
    ("šš", "ʃː"), ("š", "ʃ"),
    ("žž", "ʒː"), ("ž", "ʒ"),
    ("χ", "x"),
    ("ɣ", "ɣ"),
    ("δ", "ð"),
    ("β", "β"),

    # Special Khanty/Nganasan characters
    ("ŋ", "ŋ"),
    ("ə", "ə"),
    ("ɨ", "ɨ"),

    # Double consonants -> geminates
    ("bb", "bː"), ("dd", "dː"), ("ff", "fː"), ("gg", "ɡː"),
    ("hh", "hː"), ("jj", "jː"), ("kk", "kː"), ("ll", "lː"),
    ("mm", "mː"), ("nn", "nː"), ("pp", "pː"), ("rr", "rː"),
    ("ss", "sː"), ("tt", "tː"), ("vv", "vː"),

    # Vowels
    ("ä", "æ"), ("ö", "ø"), ("ü", "y"),
    ("a", "ɑ"), ("e", "e"), ("i", "i"), ("o", "o"), ("u", "u"),

    # Special
    ("ˀ", "ʔ"),     # glottal stop variants
    ("ˊ", "ʲ"),     # another palatalization mark
    ("g", "ɡ"),
]

# Ingrian uses ᴅ (small capital D, U+1D05) -- likely a flap or similar
INGRIAN_EXTRA = [
    ("ᴅ", "d"),      # small capital D -> regular d (approximation)
]

def convert_upa_generic(text, extra_rules=None):
    text = preprocess_upa(text)
    rules = (extra_rules or []) + UPA_RULES
    ipa = apply_rules(text, rules)
    # Strip hyphens
    ipa = ipa.replace("-", "").strip()
    return ipa


# === Main ===

CONVERTERS = {
    "hungarian": lambda t: convert_hungarian(t),
    "estonian_standard": lambda t: convert_estonian(t),
    "finnish_standard": lambda t: convert_finnish(t),
    "votic_western": lambda t: convert_votic(t),
    "khanty_vakh_vasyugan": lambda t: convert_upa_generic(t),
    "nganasan": lambda t: convert_upa_generic(t),
    "selkup_northern": lambda t: convert_upa_generic(t),
    "komi_zyrian": lambda t: convert_upa_generic(t),
    "udmurt": lambda t: convert_upa_generic(t),
    "ingrian": lambda t: convert_upa_generic(t, INGRIAN_EXTRA),
    "mansi_sosva": lambda t: convert_upa_generic(t),
    "erzya": lambda t: convert_upa_generic(t),
    "mari_meadow": lambda t: convert_upa_generic(t),
}


def main():
    data_path = os.path.join(URALEX, "raw", "Data.tsv")
    with open(data_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    filled = 0
    per_lang = {}

    for row in rows:
        lang = row["uralex_lang"]
        if lang not in CONVERTERS:
            continue

        item = row.get("item", "").strip()
        ipa = row.get("item_ipa", "").strip()
        status = row.get("status", "").strip()

        if status or not item or ipa:
            continue

        converter = CONVERTERS[lang]
        new_ipa = converter(item)
        new_segs = " ".join(segment_ipa(new_ipa))

        row["item_ipa"] = new_ipa
        row["segments"] = new_segs
        filled += 1
        per_lang[lang] = per_lang.get(lang, 0) + 1

        # Also fill UPA for Hungarian (reverse from our IPA)
        if lang == "hungarian" and not row.get("item_upa", "").strip():
            # Import the reverse converter
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "reverse_upa"))
            from apply_all import convert_hungarian as rev_hun
            row["item_upa"] = rev_hun(new_ipa)

    print(f"Filled: {filled}")
    for lang in sorted(per_lang):
        print(f"  {lang}: {per_lang[lang]}")

    # Show samples
    print("\n=== Samples ===")
    for row in rows:
        lang = row["uralex_lang"]
        item = row.get("item", "").strip()
        ipa = row.get("item_ipa", "").strip()
        if lang in per_lang and ipa:
            # Show ones we just filled
            mng = row["uralex_mng"]
            key = (lang, mng, item)
            # Print first few per language
            if per_lang.get(f"_shown_{lang}", 0) < 5:
                print(f"  {lang:<22} {mng:<18} {item:<22} -> {ipa}")
                per_lang[f"_shown_{lang}"] = per_lang.get(f"_shown_{lang}", 0) + 1

    # Write back
    with open(data_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote to {data_path}")


if __name__ == "__main__":
    main()
