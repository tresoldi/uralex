"""Inari Saami (smn) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    """Normalize Inari Saami orthography."""
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    return text


RULES = [
    # Diphthongs (must come before single vowel rules)
    ("uá", "uæ"),    # falling diphthong (čuávji -> tʃuævji)
    ("uâ", "uə"),    # variant
    ("iä", "iæ"),     # rising diphthong
    ("iâ", "iə"),     # variant
    ("ea", "eɑ"),     # diphthong (if present)

    # Long vowels (double letters, must come before single vowel rules)
    ("áá", "æː"),
    ("ää", "æː"),
    ("aa", "ɑː"),
    ("ââ", "əː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),
    ("yy", "yː"),

    # Digraphs
    ("nj", "ɲ"),      # palatal nasal
    ("lj", "ʎ"),      # palatal lateral

    # Affricates (with tie bar)
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("zz", "d͡zː"),
    ("z", "d͡z"),
    ("cc", "t͡sː"),   # geminate dental affricate
    ("c", "t͡s"),      # dental affricate

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("đđ", "ðː"),
    ("đ", "ð"),

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
    ("ŋŋ", "ŋː"),

    # Single vowels
    ("á", "æ"),       # same as ä in modern pronunciation
    ("ä", "æ"),
    ("â", "ə"),       # central reduced vowel
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),
    ("y", "y"),

    # Single consonants
    ("đ", "ð"),
    ("ŋ", "ŋ"),
    ("g", "ɡ"),       # Latin g -> IPA g (voiced in Inari Saami)
    # b, d, f, h, j, k, l, m, n, p, r, s, t, v stay as-is
]


def convert(text):
    """Convert Inari Saami orthography to IPA."""
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic
    ("mun", "mun", "stays as-is"),
    ("puoh", "puoh", "stays"),
    ("já", "jæ", "á→æ"),

    # â = schwa
    ("kutkâ", "kutkə", "â→ə"),
    ("vorrâ", "vorːə", "rr→rː, â→ə"),
    ("čappâd", "t͡ʃɑpːəd", "č→t͡ʃ, pp→pː, â→ə"),
    ("koolmâs", "koːlməs", "oo→oː, â→ə"),

    # á and ä both -> æ
    ("tähti", "tæhti", "ä→æ"),
    ("käskiđ", "kæskið", "ä→æ, đ→ð"),
    ("lávguđ", "lævɡuð", "á→æ, đ→ð"),

    # đ = dental fricative
    ("šoddâđ", "ʃodːəð", "š→ʃ, dd→dː, â→ə, đ→ð"),
    ("vuoiŋâđ", "vuoiŋəð", "ŋ→ŋ, â→ə, đ→ð"),

    # č = affricate
    ("čuávji", "t͡ʃuævji", "č→t͡ʃ, uá→uæ diphthong"),

    # Long vowels
    ("ellee", "elːeː", "ll→lː, ee→eː"),
    ("possoođ", "posːoːð", "ss→sː, oo→oː, đ→ð"),
    ("maajeeld", "mɑːjeːld", "aa→ɑː, ee→eː"),

    # áá = long æ
    ("páárnáš", "pæːrnæʃ", "áá→æː, á→æ, š→ʃ"),

    # ŋ
    ("käŋŋir", "kæŋːir", "ä→æ, ŋŋ→ŋː"),

    # b, d, g stay voiced
    ("lodde", "lodːe", "dd→dː, b/d/g voiced"),
    ("selgi", "selɡi", "g→ɡ (voiced)"),

    # y = front rounded
    ("pyelliđ", "pyelːið", "y→y, ll→lː, đ→ð"),
    ("kyeddiđ", "kyedːið", "y→y, dd→dː, đ→ð"),
    ("styeres", "styeres", "y→y"),
    ("myerji", "myerji", "y→y"),

    # Complex
    ("liäibuđ", "liæibuð", "iä→iæ diphthong, đ→ð"),
]


if __name__ == "__main__":
    print("=== Testing Inari Saami conversion ===\n")
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
    for item in ["čuávji", "páárnáš", "vuoiŋâđ", "possoođ", "kyeddiđ"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
