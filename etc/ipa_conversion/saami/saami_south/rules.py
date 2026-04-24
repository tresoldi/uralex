"""South Saami (sma) orthography-to-IPA conversion rules."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    return text


RULES = [
    # Digraph consonants (longest match first)
    ("dtj", "t͡ɕː"),   # geminate palatal affricate (pre-stopped)
    ("dts", "t͡sː"),    # geminate dental affricate (pre-stopped)
    ("sj", "ɕ"),        # voiceless alveolo-palatal fricative
    ("tj", "t͡ɕ"),      # voiceless palatal affricate
    ("ts", "t͡s"),       # voiceless dental affricate
    ("nj", "ɲ"),        # palatal nasal
    ("dj", "ɟ"),        # voiced palatal stop

    # Diphthongs / long vowel digraphs (before single vowels)
    ("ae", "ɑe"),        # diphthong (sometimes long aː but hard to distinguish)
    ("oe", "ue"),        # diphthong /uə/-like
    ("ie", "ie"),        # diphthong
    ("ue", "ue"),        # diphthong
    ("ea", "eɑ"),        # diphthong (if present)

    # Long vowels (double letters)
    ("åå", "oː"),
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("öö", "øː"),
    ("ïï", "ɨː"),

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
    ("å", "ɔ"),
    ("ï", "ɨ"),
    ("ö", "ø"),
    ("æ", "æ"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants: b/d/g stay voiced
    ("g", "ɡ"),      # Latin g -> IPA g
    # b, d, f, h, j, k, l, m, n, p, r, s, t, v stay as-is
]


def convert(text):
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    ("manne", "mɑnːe", "nn→nː"),
    ("gaajhke", "ɡɑːjhke", "g→ɡ, aa→ɑː"),
    ("jïh", "jɨh", "ï→ɨ"),
    ("garhke", "ɡɑrhke", "g→ɡ"),
    ("nåekies", "nɔekies", "å→ɔ"),
    ("sjïdtedh", "ɕɨdtedh", "sj→ɕ, ï→ɨ"),
    ("aelkedh", "ɑelkedh", "ae→ɑe diphthong"),
    ("duekesne", "duekesne", "ue diphthong"),
    ("bååhkesjidh", "boːhkeɕidh", "åå→oː, sj→ɕ"),
    ("baarhkoe", "bɑːrhkue", "aa→ɑː, oe→ue"),
    ("gïrre", "ɡɨrːe", "ï→ɨ, rr→rː"),
    ("rudtje", "rut͡ɕːe", "dtj→t͡ɕː pre-stopped palatal"),
    ("tjåejjie", "t͡ɕɔejːie", "tj→t͡ɕ, å→ɔ, jj→jː"),
    ("govne", "ɡovne", "g→ɡ"),
    ("vaejsjie", "vɑejɕie", "ae→ɑe, sj→ɕ"),
]


if __name__ == "__main__":
    print("=== Testing South Saami conversion ===\n")
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
    for item in ["gaajhke", "sjïdtedh", "tjåejjie", "baarhkoe", "aelkedh"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
