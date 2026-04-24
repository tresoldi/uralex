"""Pite Saami (sje) orthography-to-IPA conversion rules."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    # δ is a legacy variant of đ
    text = text.replace("δ", "đ")
    return text


RULES = [
    # Diphthongs
    ("ea", "eɑ"),
    ("ie", "ie"),
    ("uo", "uo"),
    ("oa", "oɑ"),

    # Long vowels
    ("áá", "ɑːː"),  # unlikely but handle
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("åå", "ɔː"),
    ("ää", "æː"),

    # Digraphs
    ("nj", "ɲ"),
    ("tj", "c"),       # palatal stop
    ("dj", "ɟ"),       # voiced palatal

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

    # Pre-stopped geminates (like North Saami)
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
    ("á", "ɑː"),     # long a (like North Saami)
    ("å", "ɔ"),
    ("ä", "æ"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants: b/d/g -> voiceless (like North Saami)
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
    ("ja", "jɑ", "plain"),
    ("gajk", "kɑjk", "g→k"),
    ("bahá", "pɑhɑː", "b→p, á→ɑː"),
    ("gåttkå", "kɔtːkɔ", "g→k, å→ɔ, tt→tː"),
    ("bähkkut", "pæhkːut", "b→p, ä→æ, kk→kː"),
    ("skälla", "skælːɑ", "ä→æ, ll→lː"),
    ("lávgudit", "lɑːvkutit", "á→ɑː, g→k"),
    ("gudna", "kutnɑ", "g→k, d→t"),
    ("nielgen", "nielken", "g→k, ie diphthong"),
    ("gárŋgel", "kɑːrŋkel", "á→ɑː, ŋ→ŋ, g→k"),
]


if __name__ == "__main__":
    print("=== Testing Pite Saami conversion ===\n")
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
