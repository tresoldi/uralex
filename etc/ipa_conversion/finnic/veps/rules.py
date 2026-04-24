"""Veps (vep) semi-phonetic notation to IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    """Normalize Veps notation before applying rules."""
    text = text.lower()
    # Normalize apostrophe to modifier letter prime
    text = text.replace("'", "ʹ")
    # Remove parentheses (optional segments included)
    text = text.replace("(", "").replace(")", "")
    # Decompose combining acute on consonants to consonant + ʹ
    # e.g. t + U+0301 -> tʹ, but ń is precomposed
    nfd = unicodedata.normalize("NFD", text)
    result = []
    i = 0
    while i < len(nfd):
        ch = nfd[i]
        if i + 1 < len(nfd) and nfd[i + 1] == "\u0301" and ch not in "aeiouyäöü":
            # Consonant + combining acute -> consonant + prime (palatalization)
            result.append(ch)
            result.append("ʹ")
            i += 2
        elif ch == "\u032E":
            # Combining breve below -- skip (vowel stays as-is)
            i += 1
        else:
            result.append(ch)
            i += 1
    text = unicodedata.normalize("NFC", "".join(result))
    return text


# Context-dependent h->x rule needs special handling
def apply_h_before_stop(text):
    """Convert h to x before stops (t, k, p)."""
    result = list(text)
    for i in range(len(result) - 1):
        if result[i] == "h" and result[i + 1] in "tkp":
            result[i] = "x"
    return "".join(result)


RULES = [
    # Palatalized consonant clusters (must come before single consonant rules)
    ("ńʹ", "nʲ"),   # redundant marking
    ("śʹ", "sʲ"),
    ("źʹ", "zʲ"),
    ("ŕʹ", "rʲ"),

    # Palatalized consonants (precomposed)
    ("ń", "nʲ"),
    ("ś", "sʲ"),
    ("ź", "zʲ"),
    ("ŕ", "rʲ"),

    # Palatalization via prime after consonant
    ("lʹlʹ", "lʲː"),   # geminate palatalized l (nelʹlʹ)
    ("bʹ", "bʲ"),
    ("dʹ", "dʲ"),
    ("fʹ", "fʲ"),
    ("gʹ", "ɡʲ"),
    ("hʹ", "hʲ"),
    ("jʹ", "jʲ"),
    ("kʹ", "kʲ"),
    ("lʹ", "lʲ"),
    ("mʹ", "mʲ"),
    ("nʹ", "nʲ"),
    ("pʹ", "pʲ"),
    ("rʹ", "rʲ"),
    ("sʹ", "sʲ"),
    ("tʹ", "tʲ"),
    ("vʹ", "vʲ"),
    ("zʹ", "zʲ"),

    # Affricates
    ("č", "tʃ"),
    ("c", "ts"),

    # Fricatives
    ("š", "ʃ"),
    ("ž", "ʒ"),

    # Long vowels (macron)
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
    ("yy", "yː"),
    ("ää", "æː"),
    ("öö", "øː"),
    ("üü", "yː"),

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

    # Single vowels
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
    ("y", "y"),
    ("ä", "æ"),
    ("ö", "ø"),
    ("ü", "y"),

    # Single consonants that change
    ("g", "ɡ"),  # Latin g -> IPA g

    # ng/nk: in Veps, ng = geminate nasal /ŋː/, nk = /ŋk/
    ("ng", "ŋː"),
    ("nk", "ŋk"),
]


def convert(text):
    """Convert Veps semi-phonetic notation to IPA."""
    text = preprocess(text)
    ipa = apply_rules(text, RULES)
    ipa = apply_h_before_stop(ipa)
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    ("mińa", "minʲɑ", "NEL: minæ"),
    ("kaik", "kɑik", "NEL: kɑik"),
    ("živat", "ʒivɑt", "NEL: ʒivɑt"),
    ("pašta", "pɑʃtɑ", "NEL: pɑʃtːɑ"),
    ("külʹptas", "kylʲptɑs", "NEL: kʏlʲptæs"),
    ("lapś", "lɑpsʲ", "NEL: lɑpsʲ"),
    ("silʹm", "silʲm", "NEL: silʲm"),
    ("pilʹv", "pilʲv", "NEL: pilʲv"),
    ("kelʹ", "kelʲ", "NEL: kɛlʲ"),
    ("suŕ", "surʲ", "NEL: sʊrʲ"),
    ("meź", "mezʲ", "NEL: mɛzʲ"),
    ("voź", "vozʲ", "NEL: vɔzʲ"),
    ("uź", "uzʲ", "NEL: ʊzʲ"),
    ("pölü", "pøly", "NEL: pœlʏ -- we use y not ʏ"),
    ("hüvä", "hyvæ", "NEL: hʏvæ -- we use y not ʏ"),
    ("ükś", "yksʲ", "NEL: ʏksʲ -- we use y not ʏ"),
    ("lind", "lind", "NEL: lind"),
    ("must", "must", "NEL: mʊst"),
    ("taga", "tɑɡɑ", "NEL: tɑɡɑ"),
    ("vac", "vɑts", "NEL: vɑts"),
    ("viž", "viʒ", "NEL: viʒ"),
    ("nelʹlʹ", "nelʲː", "NEL: nɛlʲː"),
    ("tʹehta", "tʲextɑ", "h before t → x"),
    ("ńähta", "nʲæxtɑ", "h before t → x"),
    ("pühktʹa", "pyxktʲɑ", "h before k → x"),
    ("lʹämoi", "lʲæmoi", "NEL: læmɔi"),
    ("sūg", "suːɡ", "NEL: suːɡ"),
    ("mā", "mɑː", "long a via macron"),
    ("olla nälkähine", "olːɑ nælkæhine", "multi-word"),
    ("langeta", "lɑŋːetɑ", "ng = geminate nasal"),
]


if __name__ == "__main__":
    print("=== Testing Veps conversion ===\n")
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
    for item in ["lapś", "silʹm", "tʹehta", "nelʹlʹ", "pölü"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<20} IPA={ipa:<20} segments={segs}")
