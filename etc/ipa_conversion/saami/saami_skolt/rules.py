"""Skolt Saami (sms) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    """Normalize Skolt Saami orthography."""
    text = text.lower()
    # Normalize right single quotation mark to modifier letter prime
    text = text.replace("\u2019", "ʹ")
    # Remove parentheses
    text = text.replace("(", "").replace(")", "")
    # Remove combining dot below (corpus annotation)
    text = unicodedata.normalize("NFD", text)
    text = text.replace("\u0323", "")
    text = unicodedata.normalize("NFC", text)
    # Remove stress mark ˈ (we don't model stress)
    text = text.replace("ˈ", "")
    return text


RULES = [
    # Palatalized geminates: ʹ + double consonant -> palatalized geminate
    # These must come first (longest match)
    ("ʹbb", "bʲː"),
    ("ʹcc", "t͡sʲː"),
    ("ʹdd", "dʲː"),
    ("ʹff", "fʲː"),
    ("ʹgg", "ɡʲː"),
    ("ʹhh", "hʲː"),
    ("ʹjj", "jʲː"),
    ("ʹkk", "kʲː"),
    ("ʹll", "lʲː"),
    ("ʹmm", "mʲː"),
    ("ʹnn", "nʲː"),
    ("ʹpp", "pʲː"),
    ("ʹrr", "rʲː"),
    ("ʹss", "sʲː"),
    ("ʹtt", "tʲː"),
    ("ʹvv", "vʲː"),

    # Palatalized special geminates
    ("ʹǩǩ", "cː"),    # already palatal, geminate
    ("ʹǧǧ", "ɟː"),
    ("ʹčč", "t͡ʃʲː"),
    ("ʹšš", "ʃʲː"),
    ("ʹžž", "ʒʲː"),
    ("ʹŋŋ", "ŋʲː"),
    ("ʹđđ", "ðʲː"),

    # Palatalized single consonants: ʹ + consonant
    ("ʹb", "bʲ"),
    ("ʹc", "t͡sʲ"),
    ("ʹd", "dʲ"),
    ("ʹf", "fʲ"),
    ("ʹg", "ɡʲ"),
    ("ʹh", "hʲ"),
    ("ʹj", "jʲ"),
    ("ʹk", "kʲ"),
    ("ʹl", "lʲ"),
    ("ʹm", "mʲ"),
    ("ʹn", "nʲ"),
    ("ʹp", "pʲ"),
    ("ʹr", "rʲ"),
    ("ʹs", "sʲ"),
    ("ʹt", "tʲ"),
    ("ʹv", "vʲ"),
    ("ʹǩ", "cʲ"),
    ("ʹǧ", "ɟʲ"),
    ("ʹč", "t͡ʃʲ"),
    ("ʹš", "ʃʲ"),
    ("ʹž", "ʒʲ"),
    ("ʹŋ", "ŋʲ"),
    ("ʹđ", "ðʲ"),
    ("ʹǥ", "ɣʲ"),
    ("ʹǯ", "d͡ʒʲ"),

    # Diphthongs (before single vowel rules)
    ("eä", "eæ"),
    ("ie", "ie"),
    ("ue", "ue"),
    ("uõ", "uə"),
    ("iõ", "iə"),
    ("åu", "ɔu"),
    ("uâ", "uɐ"),
    ("iâ", "iɐ"),
    ("eâ", "eɐ"),

    # Long vowels (double letters)
    ("ää", "æː"),
    ("ââ", "ɐː"),
    ("åå", "ɔː"),
    ("õõ", "əː"),
    ("aa", "ɑː"),
    ("ee", "eː"),
    ("ii", "iː"),
    ("oo", "oː"),
    ("uu", "uː"),

    # Palatal/special consonant digraphs
    ("nj", "ɲ"),
    ("lj", "ʎ"),

    # Special consonants with caron / stroke
    ("ǩǩ", "cː"),     # palatal stop geminate
    ("ǩ", "c"),         # palatal stop
    ("ǧǧ", "ɟː"),     # voiced palatal stop geminate
    ("ǧ", "ɟ"),         # voiced palatal stop
    ("ǥ", "ɣ"),         # voiced velar fricative
    ("ǯǯ", "d͡ʒː"),   # voiced affricate geminate
    ("ǯ", "d͡ʒ"),       # voiced postalveolar affricate

    # Standard affricates
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("cc", "t͡sː"),
    ("c", "t͡s"),

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("đđ", "ðː"),
    ("đ", "ð"),

    # Regular geminates
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
    ("â", "ɐ"),
    ("õ", "ə"),
    ("å", "ɔ"),
    ("ä", "æ"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Single consonants that change
    ("ŋ", "ŋ"),
    ("đ", "ð"),
    ("ʒ", "ʒ"),
    ("g", "ɡ"),      # Latin g -> IPA g (voiced in Skolt)
]


def convert(text):
    """Convert Skolt Saami orthography to IPA."""
    text = preprocess(text)
    ipa = apply_rules(text, RULES)
    # Remove any remaining ʹ that didn't match a consonant after it
    ipa = ipa.replace("ʹ", "")
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic
    ("mon", "mon", "plain"),
    ("puk", "puk", "plain"),
    ("ja", "jɑ", "a→ɑ"),

    # Special vowels
    ("šõddâd", "ʃədːɐd", "õ→ə, â→ɐ, dd→dː"),
    ("čappâd", "t͡ʃɑpːɐd", "â→ɐ, pp→pː"),
    ("võrr", "vərː", "õ→ə, rr→rː"),
    ("pååssad", "pɔːsːɑd", "åå→ɔː, ss→sː"),

    # Palatalization with ʹ
    ("låʹdd", "lɔdʲː", "å→ɔ, ʹdd→dʲː"),
    ("jieʹlli", "jielʲːi", "ie diphthong, ʹll→lʲː"),
    ("hueʹnn", "huenʲː", "ue diphthong, ʹnn→nʲː"),
    ("mueʹrjj", "muerʲjː", "ue diphthong, ʹr→rʲ, jj→jː"),
    ("päʹrnn", "pærʲnː", "ä→æ, ʹr→rʲ, nn→nː"),
    ("täʹhtt", "tæhʲtː", "ä→æ, ʹh→hʲ, tt→tː"),
    ("čåuʹjj", "t͡ʃɔujʲː", "č→t͡ʃ, åu→ɔu, ʹjj→jʲː"),

    # Special consonants
    ("neälǥlaž", "neælɣlɑʒ", "eä→eæ, ǥ→ɣ, ž→ʒ"),
    ("käʹcǩǩed", "kæt͡sʲcːed", "ä→æ, ʹc→t͡sʲ, ǩǩ→cː"),

    # b/d/g stay voiced
    ("lodde", "lodːe", "dd→dː, voiced"),

    # Long vowels
    ("lääuǥõõttäd", "læːuɣəːtːæd", "ää→æː, ǥ→ɣ, õõ→əː, tt→tː, ä→æ"),

    # Diphthongs
    ("čiõʹlj", "t͡ʃiəlʲj", "iõ→iə, ʹl→lʲ, j stays"),

    # ŋ
    ("vuõiŋŋâd", "vuəiŋːɐd", "uõ→uə, ŋŋ→ŋː, â→ɐ"),

    # šurr
    ("šurr", "ʃurː", "š→ʃ, rr→rː"),
]


if __name__ == "__main__":
    print("=== Testing Skolt Saami conversion ===\n")
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
    for item in ["låʹdd", "jieʹlli", "čappâd", "neälǥlaž", "vuõiŋŋâd"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
