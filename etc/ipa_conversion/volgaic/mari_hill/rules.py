"""Hill Mari (mrj) semi-phonetic notation to IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    text = text.replace("'", "")  # apostrophe (3x, unclear function)
    # Handle ə̑ (schwa + combining inverted breve U+0311) -> plain ə
    # Following existing UraLex convention from IPA_NOTES.md
    text = unicodedata.normalize("NFD", text)
    text = text.replace("\u0311", "")  # remove combining inverted breve
    text = unicodedata.normalize("NFC", text)
    return text


RULES = [
    # Affricates
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("cc", "t͡sː"),
    ("c", "t͡s"),

    # Fricatives -- Greek letters to IPA
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("δ", "ð"),       # Greek delta -> dental fricative
    ("β", "β"),        # bilabial fricative (valid IPA, keep as-is)
    ("ɣ", "ɣ"),        # velar fricative (already IPA)
    ("χ", "x"),        # Greek chi -> voiceless velar fricative

    # Palatalized consonants
    ("ń", "nʲ"),

    # Velar nasal
    ("ng", "ŋɡ"),
    ("nk", "ŋk"),

    # Double consonants -> geminates
    ("bb", "bː"),
    ("dd", "dː"),
    ("ff", "fː"),
    ("gg", "ɡː"),
    ("hh", "hː"),
    ("jj", "jː"),
    ("kk", "kː"),
    ("ll", "lː"),
    ("mm", "mː"),
    ("nn", "nː"),
    ("pp", "pː"),
    ("rr", "rː"),
    ("ss", "sː"),
    ("tt", "tː"),
    ("vv", "vː"),

    # Single vowels
    ("ä", "æ"),
    ("ü", "y"),
    ("ö", "ø"),
    ("ə", "ə"),       # schwa stays
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants
    ("g", "ɡ"),        # Latin g -> IPA g
]


def convert(text):
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic
    ("lu", "lu", "stays"),
    ("kek", "kek", "stays"),

    # Greek letters -> IPA
    ("huδa", "huðɑ", "δ→ð"),
    ("βər", "βər", "β stays"),
    ("koɣo", "koɣo", "ɣ stays"),
    ("δä", "ðæ", "δ→ð, ä→æ"),

    # Schwa with inverted breve -> plain schwa
    ("kə̑tkə̑", "kətkə", "inverted breve stripped"),
    ("šaiə̑lnə̑", "ʃɑiəlnə", "inverted breve stripped"),

    # Affricates
    ("cilä", "t͡silæ", "c→t͡s, ä→æ"),
    ("čö", "t͡ʃø", "č→t͡ʃ, ö→ø"),

    # Sibilants
    ("šoaš", "ʃoɑʃ", "š→ʃ"),
    ("šužaš", "ʃuʒɑʃ", "š→ʃ, ž→ʒ"),

    # Vowels
    ("küktäš", "kyktæʃ", "ü→y, ä→æ, š→ʃ"),
    ("nüštəläš", "nyʃtəlæʃ", "ü→y, š→ʃ, ä→æ"),
    ("šüläš", "ʃylæʃ", "ü→y, ä→æ"),

    # Palatalized n
    ("məń", "mənʲ", "ń→nʲ"),

    # χ -> x
    ("oχ", "ox", "χ→x"),

    # Complex
    ("təngäläš", "təŋɡælæʃ", "ng→ŋɡ, ä→æ"),
]


if __name__ == "__main__":
    print("=== Testing Hill Mari conversion ===\n")
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
    for item in ["βər", "huδa", "cilä", "kə̑tkə̑", "küktäš"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
