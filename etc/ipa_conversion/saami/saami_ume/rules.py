"""Ume Saami (sju) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    # Remove curly apostrophe and straight apostrophe (rare)
    text = text.replace("\u2019", "")
    text = text.replace("\u02BD", "")  # modifier letter reversed comma
    text = text.replace("'", "")
    # Handle combining grave on vowels that already have their own rules (å̀, ä̀, etc.)
    # Decompose, strip combining grave U+0300, recompose
    text = unicodedata.normalize("NFD", text)
    text = text.replace("\u0300", "")  # remove combining grave accent
    text = unicodedata.normalize("NFC", text)
    return text


RULES = [
    # Stress mark -> IPA stress (keep as-is, it's already U+02C8)
    # It will be handled in segmentation

    # Diphthongs
    ("ea", "eɑ"),
    ("ie", "ie"),
    ("uo", "uo"),
    ("oa", "oɑ"),
    ("ua", "uɑ"),
    ("iä", "iæ"),

    # Long vowels (double letters)
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("åå", "ɔː"),
    ("ää", "æː"),
    ("üü", "yː"),
    ("öö", "øː"),
    ("ïï", "iː"),

    # Digraph consonants
    ("nj", "ɲ"),
    ("tj", "c"),       # palatal stop
    ("dj", "ɟ"),       # voiced palatal
    ("sj", "ɕ"),       # alveolopalatal fricative

    # Affricates
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("ts", "t͡s"),

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("đđ", "ðː"),
    ("đ", "ð"),

    # Pre-stopped geminates (voiceless, like North Saami)
    ("bb", "pp"),
    ("dd", "tt"),
    ("gg", "kk"),

    # Regular geminates
    ("ff", "fː"),
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
    ("ŋŋ", "ŋː"),

    # Single vowels
    # Grave accents (à, è, ì, ò, ù) are stripped in preprocessing -> plain vowels
    ("á", "ɑː"),      # long a (acute, like North Saami)
    ("å", "ɔ"),        # open-mid back rounded
    ("ä", "æ"),        # front open
    ("ü", "y"),        # front rounded
    ("ö", "ø"),        # front rounded mid
    ("ï", "i"),        # morphophonemic variant of i
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants: b/d/g -> voiceless
    ("b", "p"),
    ("d", "t"),
    ("g", "k"),
    ("ŋ", "ŋ"),
]


def convert(text):
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    ("månna", "mɔnːɑ", "å→ɔ, nn→nː"),
    ("gáihka", "kɑːihkɑ", "g→k, á→ɑː"),
    ("ja", "jɑ", "plain"),
    ("tjuura", "cuːrɑ", "tj→c, uu→uː"),
    ("gùdna", "kutnɑ", "g→k, ù→u, d→t"),
    ("lüdˈnee", "lytˈneː", "ü→y, d→t, ˈ between syllables, ee→eː"),
    ("bàrˈkoo", "pɑrˈkoː", "b→p, à→ɑ, oo→oː"),
    ("tjüvvielge", "cyvːielke", "tj→c, ü→y, vv→vː, ie diph, g→k"),
    ("bå̀hkat", "pɔhkɑt", "b→p, å̀→ɔ (grave stripped), k stays"),
]


if __name__ == "__main__":
    print("=== Testing Ume Saami conversion ===\n")
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
