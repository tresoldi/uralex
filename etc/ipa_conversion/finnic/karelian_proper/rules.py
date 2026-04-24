"""Karelian Proper (krl) orthography-to-IPA conversion rules."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars

# Ordered replacement rules: longest match first (handled by apply_rules)
RULES = [
    # Digraphs / multigraphs (must come before single chars)
    ("tš", "tʃ"),    # voiceless postalveolar affricate
    ("dž", "dʒ"),    # voiced postalveolar affricate
    ("nk", "ŋk"),    # velar nasal before k
    ("ng", "ŋ"),     # velar nasal before g or word-finally (simplified)

    # Double vowels -> long (must come before single vowel rules)
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("yy", "yː"),
    ("ää", "æː"),
    ("öö", "øː"),

    # Double consonants -> geminates (must come before single consonant rules)
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
    ("y", "y"),
    ("ä", "æ"),
    ("ö", "ø"),

    # Single consonants (only those that change)
    ("š", "ʃ"),
    ("ž", "ʒ"),
    ("g", "ɡ"),  # Latin g -> IPA g

    # These stay the same: b, d, f, h, j, k, l, m, n, p, r, s, t, v
]


def convert(text):
    """Convert Karelian orthography to IPA."""
    # Remove parentheses (optional segments are included)
    text = text.replace("(", "").replace(")", "")
    return apply_rules(text.lower(), RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


# Test cases from NorthEuraLex cross-reference
TEST_CASES = [
    # (item, expected_ipa, source)
    ("mie", "mie", "NEL: miɛ -- we use /e/ not /ɛ/"),
    ("kaikki", "kɑikːi", "NEL: kɑikːi"),
    ("lintu", "lintu", "NEL: lintʊ -- we use /u/ not /ʊ/"),
    ("veri", "veri", "NEL: vɛri -- we use /e/ not /ɛ/"),
    ("luu", "luː", "NEL: luː"),
    ("musta", "mustɑ", "NEL: mʊstɑ"),
    ("hammas", "hɑmːɑs", "NEL: hɑmːɑs"),
    ("suuri", "suːri", "NEL: suːri"),
    ("kolme", "kolme", "NEL: kɔlmɛ -- we use /o e/"),
    ("lehti", "lehti", "NEL: lɛxti -- we keep h as h"),
    ("hyvä", "hyvæ", "NEL: hyvæ"),
    ("häntä", "hæntæ", "NEL: hæntæ"),
    ("jalka", "jɑlkɑ", "NEL: jɑlkɑ"),
    ("tulla", "tulːɑ", "NEL: tʊlːɑ"),
    ("marja", "mɑrjɑ", "NEL: mɑrjɑ"),
    ("kylpie", "kylpie", "NEL: kylpiɛ"),
    ("šiivatta", "ʃiːvɑtːɑ", "NEL: --"),
    ("vattša", "vɑtːʃɑ", "NEL: --"),
    ("pyyhkie", "pyːhkie", "NEL: pyyxkiɛ"),
    ("henkitteä", "heŋkitːeæ", "NEL: hɛŋkitːyæ -- different vowels"),
    ("purra", "purːɑ", "NEL: pʊrːɑ"),
    ("selkä", "selkæ", "NEL: --"),
    ("huono", "huono", "NEL: hʊɔnɔ -- we use /u o/"),
    ("takana", "tɑkɑnɑ", "NEL: tɑkɑnɑ"),
    ("olla nälkähine", "olːɑ nælkæhine", "multi-word"),
]


if __name__ == "__main__":
    print("=== Testing Karelian Proper conversion ===\n")
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

    # Also test segmentation
    print("\n=== Sample segmentation ===")
    for item in ["kaikki", "vattša", "henkitteä", "olla nälkähine"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<20} IPA={ipa:<20} segments={segs}")
