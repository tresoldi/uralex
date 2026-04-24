"""Tundra Nenets (yrk) Latinized notation to IPA conversion rules."""

import sys, os, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules, segment_ipa, validate_ipa_chars


VOWELS = set("ɑeiouyæə")
CONSONANTS = set("bcdfghjklmnpqrstvwxŋ")


def preprocess(text):
    text = text.lower()
    text = text.replace("(", "").replace(")", "")
    # Strip acute accents (stress markers, not quality)
    text = text.replace("í", "i").replace("ú", "u")
    # Remove ° (morphological stem marker, no phonetic value)
    text = text.replace("°", "")
    return text


# Note: y is context-dependent and handled specially in convert(),
# so it does NOT appear in RULES as a standalone mapping.
RULES = [
    # Palatalized consonant + y (before non-vowel or word-end)
    # These are handled by convert() function below

    # Affricates
    ("cy", "t͡sʲ"),    # palatalized dental affricate (cy before consonant/end)

    # Standalone affricate (c without following y -- cy handled in convert())
    ("c", "t͡s"),

    # Glottal stop
    ("q", "ʔ"),
    ("h", "ʔ"),        # h = glottal stop in Nenets notation

    # Nasal
    ("ŋ", "ŋ"),

    # Velar fricative
    ("x", "x"),

    # Double consonants -> geminates
    ("bb", "bː"),
    ("dd", "dː"),
    ("ff", "fː"),
    ("gg", "ɡː"),
    ("kk", "kː"),
    ("ll", "lː"),
    ("mm", "mː"),
    ("nn", "nː"),
    ("pp", "pː"),
    ("rr", "rː"),
    ("ss", "sː"),
    ("tt", "tː"),
    ("ww", "wː"),

    # Single vowels
    ("æ", "æ"),
    ("ə", "ə"),
    ("a", "ɑ"),
    ("e", "e"),
    ("i", "i"),
    ("o", "o"),
    ("u", "u"),

    # w stays
    ("w", "w"),

    # Consonants that stay
    ("g", "ɡ"),
]


def convert(text):
    """Convert Nenets Latinized notation to IPA.

    The key complexity is 'y': palatalization after consonants, /j/ before vowels.
    We handle this with a two-pass approach:
    1. First, replace Cy sequences with palatalized consonants
    2. Then, replace remaining y (before vowels) with j
    3. Finally, apply the standard rules
    """
    text = preprocess(text)

    # Pass 1: Handle Cy -> Cʲ (consonant + y = palatalization)
    # ny is special -> ɲ
    # cy -> t͡sʲ (affricate)
    # Other Cy -> Cʲ
    result = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "y" and i > 0:
            prev = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < len(text) else ""

            if prev in CONSONANTS or (result and result[-1][-1:] in "ʲ"):
                # y after consonant = palatalization
                if result and result[-1] == "n":
                    result[-1] = "ɲ"  # ny -> ɲ
                elif result and result[-1] == "c":
                    result[-1] = "t͡sʲ"  # cy -> t͡sʲ
                elif result and result[-1] == "l":
                    result[-1] = "lʲ"
                elif result and result[-1] == "t":
                    result[-1] = "tʲ"
                elif result and result[-1] == "s":
                    result[-1] = "sʲ"
                elif result and result[-1] == "d":
                    result[-1] = "dʲ"
                elif result and result[-1] == "m":
                    result[-1] = "mʲ"
                elif result and result[-1] == "p":
                    result[-1] = "pʲ"
                elif result and result[-1] == "r":
                    result[-1] = "rʲ"
                elif result and result[-1] == "b":
                    result[-1] = "bʲ"
                elif result and result[-1] == "k":
                    result[-1] = "kʲ"
                elif result and result[-1] == "v":
                    result[-1] = "vʲ"
                elif result:
                    result[-1] = result[-1] + "ʲ"
                i += 1
                continue
            else:
                # y before vowel or at word start = j
                result.append("j")
                i += 1
                continue
        elif ch == "y" and i == 0:
            # Word-initial y = j
            result.append("j")
            i += 1
            continue
        else:
            result.append(ch)
            i += 1

    text = "".join(result)

    # Pass 2: Apply standard rules for remaining characters
    ipa = apply_rules(text, RULES)
    return ipa


def convert_and_segment(text):
    ipa = convert(text)
    segs = segment_ipa(ipa)
    return ipa, " ".join(segs)


TEST_CASES = [
    # ° dropped
    ("məny°", "məɲ", "° dropped, ny→ɲ"),
    ("sarmyik°", "sɑrmʲik", "° dropped, my→mʲ"),
    ("xæsy°", "xæsʲ", "° dropped, sy→sʲ"),

    # Palatalization
    ("tyíw°", "tʲiw", "ty→tʲ, í→i, ° dropped"),
    ("pyasy°", "pʲɑsʲ", "py→pʲ, sy→sʲ"),
    ("syabt°", "sʲɑbt", "sy→sʲ"),

    # y before vowel = j
    ("yabcə°", "jɑbt͡sə", "y→j, c→t͡s (no y after c here)"),
    ("yilye°", "jilʲe", "y→j, ly→lʲ"),

    # q and h = glottal stop
    ("mal°h", "mɑlʔ", "h→ʔ"),
    ("yínt°q", "jintʔ", "q→ʔ, í→i"),

    # ŋ
    ("ŋəcyeki°", "ŋət͡sʲeki", "ŋ stays, cy→t͡sʲ"),

    # æ
    ("sæw°", "sæw", "æ stays, w stays"),
    ("tæwə°", "tæwə", "æ stays"),

    # No °
    ("xudumka", "xudumkɑ", "no ° in this word"),
    ("ŋarka", "ŋɑrkɑ", "no °"),
    ("weya", "wejɑ", "y before a = j"),
    ("ŋodya", "ŋodʲɑ", "dy→dʲ"),

    # Complex
    ("pəryidye°", "pərʲidʲe", "ry→rʲ, dy→dʲ"),
    ("ŋamtyo°", "ŋɑmtʲo", "ty→tʲ"),
    ("tyírtya", "tʲirtʲɑ", "ty→tʲ twice"),

    # x stays
    ("xəl°ta°", "xəltɑ", "x stays, ° dropped"),

    # w
    ("sæw°", "sæw", "w stays"),
]


if __name__ == "__main__":
    print("=== Testing Tundra Nenets conversion ===\n")
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
    for item in ["məny°", "yabcə°", "tyírtya", "pəryidye°", "ŋamtyo°"]:
        ipa, segs = convert_and_segment(item)
        print(f"  {item:<22} IPA={ipa:<22} segments={segs}")
