"""Estonian South / Võro (vro) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    """Normalize Võro orthography before applying rules."""
    text = text.lower()
    # Normalize right single quotation mark to apostrophe
    text = text.replace("\u2019", "'")
    # Remove parentheses (optional segments included)
    text = text.replace("(", "").replace(")", "")
    return text


RULES = [
    # Palatalized affricate (ts + apostrophe)
    ("ts'", "tsʲ"),

    # Affricate (must come before single-char rules)
    ("ts", "ts"),

    # Palatalization via apostrophe (must come before geminate rules)
    ("b'", "bʲ"),
    ("d'", "dʲ"),
    ("f'", "fʲ"),
    ("g'", "ɡʲ"),
    ("h'", "hʲ"),
    ("j'", "jʲ"),
    ("k'", "kʲ"),
    ("l'", "lʲ"),
    ("m'", "mʲ"),
    ("n'", "nʲ"),
    ("p'", "pʲ"),
    ("r'", "rʲ"),
    ("s'", "sʲ"),
    ("t'", "tʲ"),
    ("v'", "vʲ"),
    ("z'", "zʲ"),

    # Velar nasal
    ("nk", "ŋk"),
    ("ng", "ŋɡ"),

    # Double vowels -> long
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("üü", "yː"),
    ("ää", "æː"),
    ("öö", "øː"),
    ("õõ", "ɤː"),

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
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
    ("ä", "æ"),
    ("ö", "ø"),
    ("ü", "y"),
    ("õ", "ɤ"),

    # Glottal stop
    ("q", "ʔ"),

    # Single consonants that change
    ("g", "ɡ"),  # Latin g -> IPA g
]


def convert(text):
    """Convert Võro orthography to IPA."""
    text = preprocess(text)
    ipa = apply_rules(text, RULES)
    # Handle leftover apostrophes after geminates: ː' -> ːʲ
    ipa = ipa.replace("ː'", "ːʲ")
    # Remove any remaining apostrophes (shouldn't happen, but safety)
    ipa = ipa.replace("'", "")
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Glottal stop
    ("maq", "mɑʔ", "q = glottal stop"),
    ("seemeq", "seːmeʔ", "q = glottal stop"),
    ("munaq", "munɑʔ", "q = glottal stop"),
    ("lühüq", "lyhyʔ", "q = glottal stop"),
    ("miiq", "miːʔ", "q = glottal stop"),

    # Palatalization
    ("kõik'", "kɤikʲ", "apostrophe = palatalization"),
    ("suur'", "suːrʲ", "apostrophe = palatalization"),
    ("pilv'", "pilvʲ", "final v palatalized"),
    ("lats'", "lɑtsʲ", "palatalized ts"),
    ("viis'", "viːsʲ", "palatalized s"),
    ("pall'o", "pɑlːʲo", "geminate l + palatalization"),

    # Basic vowels
    ("ja", "jɑ", "a→ɑ"),
    ("veri", "veri", "e→e, i→i"),
    ("must", "must", "u→u"),
    ("kõtt", "kɤtː", "õ→ɤ, tt→tː"),
    ("sälg", "sælɡ", "ä→æ"),
    ("küdsämä", "kydsæmæ", "ü→y, ä→æ"),

    # Length
    ("luu", "luː", "long vowel"),
    ("nahkhiir'", "nɑhkhiːrʲ", "long vowel + palatalization"),
    ("elläi", "elːæi", "geminate + diphthong"),

    # Affricate
    ("tsirk", "tsirk", "ts affricate"),

    # Multi-word
    ("peräle joudma", "peræle joudmɑ", "multi-word"),
]


if __name__ == "__main__":
    print("=== Testing Võro conversion ===\n")
    passed = 0
    failed = 0
    for item, expected, source in TEST_CASES:
        result = convert(item)
        status = "OK" if result == expected else "FAIL"
        if status == "FAIL":
            print(f"  FAIL: {item:<20} expected={expected:<20} got={result:<20} ({source})")
            failed += 1
        else:
            passed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(TEST_CASES)}")

    print("\n=== Sample segmentation ===")
    for item in ["maq", "kõik'", "suur'", "tsirk", "küdsämä", "lats'"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<20} IPA={ipa:<20} segments={segs}")
