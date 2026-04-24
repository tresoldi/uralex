"""Livonian / Courland (liv) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    # Normalize right single quotation mark (1 occurrence, likely glottal or nothing)
    text = text.replace("\u2019", "")
    # ì (grave i) -> plain i (not phonemic)
    text = text.replace("ì", "i")
    return text


RULES = [
    # Affricate digraph (must come before š)
    ("tš", "t͡ʃ"),

    # Cedilla/palatalized consonants (before regular consonant rules)
    ("ļļ", "ʎː"),
    ("ļ", "ʎ"),
    ("ŗŗ", "rʲː"),
    ("ŗ", "rʲ"),
    ("ņņ", "ɲː"),
    ("ņ", "ɲ"),
    ("ḑḑ", "ɟː"),
    ("ḑ", "ɟ"),
    ("țț", "cː"),
    ("ț", "c"),

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),

    # Long vowels with special diacritics (must come before simple macrons)
    ("ǟ", "æː"),     # ä + macron = long front open
    ("ȭ", "ɯː"),     # õ + macron = long high back unrounded
    ("ȱ", "ɤː"),     # ȯ + macron = long mid back unrounded
    ("ǭ", "ɒː"),     # o + ogonek + macron = long low back rounded (marginal)

    # Long vowels with macron
    ("ā", "ɑː"),
    ("ē", "eː"),
    ("ī", "iː"),
    ("ō", "oː"),
    ("ū", "uː"),

    # Double vowels -> long
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),

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
    ("zz", "zː"),

    # Velar nasal before velars
    ("ng", "ŋɡ"),
    ("nk", "ŋk"),

    # Special vowels (single)
    ("õ", "ɯ"),       # high back unrounded (NOT schwa!)
    ("ȯ", "ɤ"),       # mid back unrounded (NOT ʊ!)
    ("ä", "æ"),       # front open
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants: b/d/g stay voiced in Livonian
    ("g", "ɡ"),       # Latin g -> IPA g
]


def convert(text):
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic vowels
    ("ma", "mɑ", "a→ɑ"),
    ("un", "un", "stays"),
    ("ver", "ver", "e→e"),
    ("lind", "lind", "stays"),

    # õ = high back unrounded
    ("joudõ", "joudɯ", "õ→ɯ"),
    ("kandõ", "kɑndɯ", "õ→ɯ"),
    ("gilgõ", "ɡilɡɯ", "õ→ɯ, g→ɡ"),

    # Macron = long
    ("sūr", "suːr", "ū→uː"),
    ("lū", "luː", "ū→uː"),
    ("mustā", "mustɑː", "ā→ɑː"),
    ("līdõ", "liːdɯ", "ī→iː, õ→ɯ"),
    ("tagān", "tɑɡɑːn", "g→ɡ, ā→ɑː"),
    ("mōŗa", "moːrʲɑ", "ō→oː, ŗ→rʲ"),
    ("pīla", "piːlɑ", "ī→iː"),

    # ǟ = long front open
    ("sǟlga", "sæːlɡɑ", "ǟ→æː, g→ɡ"),
    ("nǟlgas", "næːlɡɑs", "ǟ→æː"),

    # ä = front open
    ("läpš", "læpʃ", "ä→æ, š→ʃ"),

    # ȯ = mid back unrounded
    ("vȯzā", "vɤzɑː", "ȯ→ɤ"),
    ("vȯigõ", "vɤiɡɯ", "ȯ→ɤ, g→ɡ, õ→ɯ"),

    # Cedilla consonants
    ("kūoŗ", "kuːorʲ", "ū→uː, ŗ→rʲ"),
    ("kīņtš", "kiːɲt͡ʃ", "ī→iː, ņ→ɲ, tš→t͡ʃ"),
    ("kibḑi", "kibɟi", "ḑ→ɟ"),
    ("slikțõ", "slikcɯ", "ț→c, õ→ɯ"),

    # ȭ = long ɯ
    ("ȭŗõ", "ɯːrʲɯ", "ȭ→ɯː, ŗ→rʲ, õ→ɯ"),
    ("tȭlza", "tɯːlzɑ", "ȭ→ɯː"),

    # ȱ = long ɤ
    ("vȱlda", "vɤːldɑ", "ȱ→ɤː"),

    # Geminate
    ("pallõ", "pɑlːɯ", "ll→lː, õ→ɯ"),
    ("amā", "ɑmɑː", "ā→ɑː"),

    # tš affricate
    ("pluņtšõ", "pluɲt͡ʃɯ", "ņ→ɲ, tš→t͡ʃ, õ→ɯ"),

    # ng
    ("jengõ", "jeŋɡɯ", "ng→ŋɡ, õ→ɯ"),
]


if __name__ == "__main__":
    print("=== Testing Livonian conversion ===\n")
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
    for item in ["joudõ", "sǟlga", "kīņtš", "vȯigõ", "ȭŗõ", "mustā"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
