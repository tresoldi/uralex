"""North Saami (sme) orthography-to-IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


def preprocess(text):
    """Normalize North Saami orthography before applying rules."""
    text = text.lower()
    # Decompose to NFD so combining dot below becomes separate U+0323
    text = unicodedata.normalize("NFD", text)
    # Remove combining dot below U+0323 (corpus-specific annotation)
    text = text.replace("\u0323", "")
    # Recompose
    text = unicodedata.normalize("NFC", text)
    # Normalize grave accent: à -> a (non-standard annotation)
    text = text.replace("à", "a")
    # Remove stress mark ˈ between identical consonants -- the gemination
    # is already handled by double-consonant rules
    # But ˈ between different consonants should just be removed
    text = text.replace("ˈ", "")
    # Remove parentheses
    text = text.replace("(", "").replace(")", "")
    return text


RULES = [
    # Digraphs / multigraphs (longest match first)
    ("nj", "ɲ"),     # palatal nasal
    ("dj", "ɟ"),     # palatal stop (if present)

    # Diphthongs (must come before single vowel rules)
    ("ea", "eæ"),    # falling diphthong (NEL confirmed: eæ)
    ("ie", "ie"),    # stays as-is
    ("uo", "uo"),    # stays as-is
    ("oa", "oɑ"),    # falling diphthong

    # Long vowel: á
    ("á", "ɑː"),

    # Macron vowels (long)
    ("ē", "eː"),
    ("ō", "oː"),

    # Affricates (use tie bar U+0361 to keep as single segment)
    ("čč", "t͡ʃː"),  # geminate affricate
    ("č", "t͡ʃ"),     # postalveolar affricate
    ("zz", "d͡zː"),   # geminate z-affricate
    ("z", "d͡z"),      # affricate

    # Fricatives
    ("šš", "ʃː"),
    ("š", "ʃ"),
    ("žž", "ʒː"),
    ("ž", "ʒ"),
    ("đđ", "ðː"),
    ("đ", "ð"),

    # Pre-stopped consonants (Saami-specific: voiced letter doubled = pre-stopped)
    ("bb", "pp"),     # pre-stopped: orthographic bb = /pp/ (strong grade)
    ("dd", "tt"),     # pre-stopped: orthographic dd = /tt/ (strong grade)
    ("gg", "kk"),     # pre-stopped: orthographic gg = /kk/ (strong grade)

    # Regular geminates (sonorants, fricatives, voiceless stops)
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

    # Single vowels
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # Consonants: b/d/g -> voiceless p/t/k
    ("b", "p"),
    ("d", "t"),
    ("g", "k"),

    # Other consonants that stay the same but need IPA normalization
    ("ŋ", "ŋ"),
    # f, h, j, k, l, m, n, p, r, s, t, v stay as-is
]


def convert(text):
    """Convert North Saami orthography to IPA."""
    text = preprocess(text)
    return apply_rules(text, RULES)


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # Basic voiceless mapping
    ("mun", "mun", "u stays u"),
    ("buot", "puot", "b→p"),
    ("gotka", "kotkɑ", "g→k, a→ɑ"),
    ("ja", "jɑ", "a→ɑ"),
    ("loddi", "lotti", "o→o, dd→tt (pre-stopped)"),

    # á = long aː
    ("mánná", "mɑːnːɑː", "á→ɑː, nn→nː"),
    ("álgit", "ɑːlkit", "á→ɑː, g→k"),
    ("jápmit", "jɑːpmit", "á→ɑː"),
    ("dákti", "tɑːkti", "d→t, á→ɑː"),

    # Diphthongs
    ("čoavji", "t͡ʃoɑvji", "č→tʃ, oa→oɑ"),
    ("beaivi", "peæivi", "b→p, ea→eæ"),

    # Special consonants
    ("čáhppat", "t͡ʃɑːhpːɑt", "č→tʃ, á→ɑː, pp→pː"),
    ("šaddat", "ʃɑttɑt", "š→ʃ, dd→tt"),
    ("đivččat", "ðivt͡ʃːɑt", "đ→ð, čč→t͡ʃː"),

    # đ
    ("muođut", "muoðut", "đ→ð, uo stays"),
    ("iđit", "iðit", "đ→ð"),
    ("ođas", "oðɑs", "đ→ð"),

    # nj palatal nasal
    ("njálbmi", "ɲɑːlpmi", "nj→ɲ, á→ɑː, b→p (single b stays p)"),

    # z affricate
    ("vázzit", "vɑːd͡zːit", "á→ɑː, zz→d͡zː"),

    # ŋ
    ("vuoigŋat", "vuoikŋɑt", "g→k, ŋ→ŋ"),

    # ˈ stress mark (removed, gemination from double letters)
    ("ealˈli", "eælːi", "ˈ removed, ll→lː, ea→eæ"),
    ("asˈsái", "ɑsːɑːi", "ˈ removed, ss→sː, á→ɑː"),
    ("unˈni", "unːi", "ˈ removed, nn→nː"),

    # Dot below (stripped)
    ("bealjẹheapmẹ", "peæljeheæpme", "dot below stripped, ea→eæ"),

    # Macron vowels
    ("hēittot", "heːitːot", "ē→eː, tt→tː"),

    # Blood
    ("varra", "vɑrːɑ", "a→ɑ, rr→rː"),

    # Multi-word
    ("leat nealggis", "leæt neælkkis", "multi-word, ea→eæ, gg→kk"),
]


if __name__ == "__main__":
    print("=== Testing North Saami conversion ===\n")
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
    for item in ["mánná", "čáhppat", "njálbmi", "vuoigŋat", "ealˈli", "vázzit"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
