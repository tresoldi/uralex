"""Estonian Standard -- reverse IPA to UPA."""

import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from conversion_utils import apply_rules


def ipa_to_upa(ipa):
    """Convert Estonian Standard IPA to UPA notation."""
    text = ipa

    # Length mark -> double the preceding character
    # Handle Cː -> CC and Vː -> VV
    result = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "ː" and result:
            # Double the preceding character
            result.append(result[-1])
        else:
            result.append(ch)
        i += 1
    text = "".join(result)

    # IPA -> UPA character mappings
    RULES = [
        # Vowels
        ("ɑ", "a"),
        ("æ", "ä"),
        ("ɤ", "ə̑"),     # close-mid back unrounded -> schwa + inverted breve
        ("ø", "ö"),
        ("y", "ü"),       # close front rounded

        # Consonants
        ("ɣ", "ɣ"),      # keep (already UPA-compatible)
        ("ŋ", "ŋ"),      # keep
        ("ʔ", "ˀ"),      # glottal stop in UPA
    ]

    text = apply_rules(text, RULES)
    return text


TEST_CASES = [
    ("minɑ", "mina", "ɑ→a"),
    ("kɤik", "kə̑ik", "ɤ→ə̑"),
    ("jɑ", "ja", "ɑ→a"),
    ("loːm", "loom", "ː→double"),
    ("sipːelkɑs", "sippelkas", "ː→double"),
    ("sɑːputɑ", "saaputa", "ː→double"),
    ("tuhk", "tuhk", "no change"),
    ("juːres", "juures", "ː→double"),
    ("selk", "selk", "no change"),
    ("kɑenlɑʔɑlune", "kaenlaˀalune", "ɑ→a, ʔ→ˀ"),
    ("minæ", "minä", "æ→ä"),  # wait, this is Finnish not Estonian
    ("kypːsetːɑtɑ", "küppsettata", "y→ü, ː→double"),
]


if __name__ == "__main__":
    print("=== Testing Estonian Standard IPA→UPA ===\n")
    passed = 0
    failed = 0
    for ipa, expected, source in TEST_CASES:
        result = ipa_to_upa(ipa)
        status = "OK" if result == expected else "FAIL"
        if status == "FAIL":
            print(f"  FAIL: {ipa:<22} expected={expected:<22} got={result:<22} ({source})")
            failed += 1
        else:
            passed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(TEST_CASES)}")
