"""Proto-Uralic reconstruction notation to IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    # Preserve uppercase V (unknown vowel placeholder) before lowercasing
    text = text.replace("V", "\x00V\x00")
    text = text.lower()
    text = text.replace("\x00v\x00", "V")
    # Strip asterisk (reconstruction marker)
    text = text.replace("*", "")
    # Strip ? (uncertainty)
    text = text.replace("?", "")
    # Strip parentheses (optional/uncertain segments -- include content)
    text = text.replace("(", "").replace(")", "")
    # Handle i̮ (i + combining breve below U+032E) -> ɨ
    text = unicodedata.normalize("NFD", text)
    # Replace i + breve below -> ɨ, and any other vowel + breve below
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i + 1] == "\u032E":
            # Vowel with breve below -> back/central counterpart
            base = text[i]
            if base == "i":
                result.append("ɨ")
            elif base == "u":
                result.append("ʉ")
            else:
                result.append(base)  # keep as-is if unexpected
            i += 2
        else:
            result.append(text[i])
            i += 1
    text = unicodedata.normalize("NFC", "".join(result))
    # Handle ȣ̈ (ou ligature + diaeresis) -- rare, only 1 occurrence
    text = text.replace("ȣ̈", "ø")  # approximate
    text = text.replace("ȣ", "o")   # fallback
    return text


RULES = [
    # Palatalized consonants (from UPA/Uralistics notation)
    ("ś", "sʲ"),       # palatalized sibilant
    ("ć", "t͡sʲ"),     # palatalized affricate
    ("ń", "ɲ"),        # palatal nasal (not just nʲ)

    # Affricates
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),

    # Fricatives / special consonants
    ("δ", "ð"),        # dental fricative
    ("ɣ", "ɣ"),        # velar fricative (already IPA)
    ("ð", "ð"),        # eth (if present)

    # Modifier letter prime (1 occurrence: *śüδʹi)
    ("ʹ", "ʲ"),        # palatalization

    # Vowels
    ("ä", "æ"),
    ("ü", "y"),
    ("ɨ", "ɨ"),        # from preprocessing (i̮)
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # ŋ stays
    ("ŋ", "ŋ"),

    # Unknown vowel V -- keep as uppercase V (not convertible)
    # This will be handled by leaving it as-is

    # Consonants
    ("g", "ɡ"),
]


def convert(text):
    text = preprocess(text)
    ipa = apply_rules(text, RULES)
    # Remove morpheme boundary hyphens
    ipa = ipa.replace("-", "")
    ipa = ipa.strip()
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    ("*min-", "min", "strip * and -"),
    ("*mun-", "mun", "strip * and -"),
    ("*kala", "kɑlɑ", "a→ɑ"),
    ("*weri", "weri", "w stays"),
    ("*muna", "munɑ", "a→ɑ"),
    ("*nimi", "nimi", "stays"),
    ("*śilmä", "sʲilmæ", "ś→sʲ, ä→æ"),
    ("*käti", "kæti", "ä→æ"),
    ("*ńeljä", "ɲeljæ", "ń→ɲ, ä→æ"),
    ("*čečä", "t͡ʃet͡ʃæ", "č→t͡ʃ"),
    ("*künči", "kynt͡ʃi", "ü→y, č→t͡ʃ"),
    ("*lumi̮", "lumɨ", "i̮→ɨ"),
    ("*kolmi̮", "kolmɨ", "i̮→ɨ"),
    ("*tulɨ-", "tulɨ", "strip -"),  # wait, ɨ is already processed
    ("*maɣi̮", "mɑɣɨ", "ɣ stays, i̮→ɨ"),
    ("*śüδä-m-", "sʲyðæm", "ś→sʲ, ü→y, δ→ð, ä→æ"),
    ("*śüδʹi", "sʲyðʲi", "ʹ→ʲ"),
    ("*ićä", "it͡sʲæ", "ć→t͡sʲ"),
    ("*enä", "enæ", "ä→æ"),
    ("*jalka", "jɑlkɑ", "a→ɑ"),
    ("?*konV", "konV", "? stripped, V stays as uppercase V"),
]


if __name__ == "__main__":
    print("=== Testing Proto-Uralic conversion ===\n")
    passed = 0
    failed = 0
    for item, expected, source in TEST_CASES:
        result = convert(item)
        status = "OK" if result == expected else "FAIL"
        if status == "FAIL":
            print(f"  FAIL: {item:<22} expected={expected:<22} got={result:<22} ({source})")
            failed += 1
        else:
            passed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(TEST_CASES)}")

    print("\n=== Sample segmentation ===")
    for item in ["*śilmä", "*kolmi̮", "*čečä", "*śüδä-m-", "*jalka"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
