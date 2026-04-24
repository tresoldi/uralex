"""Moksha (mdf) UPA-influenced notation to IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    # Apostrophe marks palatalization -- convert to modifier prime
    text = text.replace("'", "ʹ")
    # Modifier letter prime (if present) also marks palatalization
    # Handle combining acute on consonants -> palatalization
    nfd = unicodedata.normalize("NFD", text)
    result = []
    i = 0
    while i < len(nfd):
        ch = nfd[i]
        if i + 1 < len(nfd) and nfd[i + 1] == "\u0301" and ch not in "aeiouyäöü":
            # Consonant + combining acute = palatalized (already have precomposed forms)
            result.append(ch)
            result.append("ʹ")
            i += 2
        else:
            result.append(ch)
            i += 1
    text = unicodedata.normalize("NFC", "".join(result))
    return text


RULES = [
    # Palatalized consonant pairs (apostrophe/prime after consonant)
    ("d'ž", "d͡ʒʲ"),   # palatalized voiced affricate cluster
    ("d'd'", "dʲː"),   # geminate palatalized d
    ("l'l'", "lʲː"),   # geminate palatalized l
    ("t't'", "tʲː"),   # geminate palatalized t

    # Precomposed palatalized consonants
    ("ś", "sʲ"),
    ("ŕ", "rʲ"),
    ("ń", "nʲ"),
    ("ć", "t͡sʲ"),     # palatalized affricate
    ("ź", "zʲ"),
    ("ĺ", "lʲ"),

    # Palatalization via prime/apostrophe
    ("cʹ", "t͡sʲ"),   # palatalized affricate (from decomposed ć)
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
    ("čč", "t͡ʃː"),
    ("č", "t͡ʃ"),
    ("cc", "t͡sː"),
    ("c", "t͡s"),

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("χ", "x"),        # Greek chi -> voiceless velar fricative

    # Velar nasal
    ("ng", "ŋɡ"),
    ("nk", "ŋk"),
    ("ŋ", "ŋ"),

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
    ("ə", "ə"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants
    ("g", "ɡ"),
]


def convert(text):
    text = preprocess(text)
    ipa = apply_rules(text, RULES)
    # Remove any leftover prime marks (after geminates etc.)
    ipa = ipa.replace("ʹ", "")
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic
    ("mon", "mon", "stays"),
    ("kulu", "kulu", "stays"),

    # Palatalized consonants (precomposed)
    ("śembä", "sʲembæ", "ś→sʲ, ä→æ"),
    ("kopoŕ", "koporʲ", "ŕ→rʲ"),
    ("pańəms", "pɑnʲəms", "ń→nʲ, ə stays"),
    ("ćora", "t͡sʲorɑ", "ć→t͡sʲ"),

    # Palatalization via apostrophe
    ("kal'd'av", "kɑlʲdʲɑv", "apostrophe palatalization"),
    ("äšel'ams", "æʃelʲɑms", "ä→æ, š→ʃ, apostrophe"),

    # Sibilants
    ("rakša", "rɑkʃɑ", "š→ʃ... wait, kš should be kʃ"),
    ("panžam", "pɑnʒɑm", "ž→ʒ... wait, nž should stay nʒ"),

    # χ -> x
    ("χ", "x", "χ→x"),

    # ŋ
    ("ŋ", "ŋ", "stays"),

    # Complex
    ("vəndŕav", "vəndrʲɑv", "ŕ→rʲ"),
    ("ker", "ker", "stays"),
]


if __name__ == "__main__":
    print("=== Testing Moksha conversion ===\n")
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
    for item in ["śembä", "kal'd'av", "pańəms", "kopoŕ", "ćora"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
