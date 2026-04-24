"""Shared IPA→UPA reverse conversion logic."""

import unicodedata


def expand_length(text):
    """Convert ː after a character to doubling of that character."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == "ː" and result:
            result.append(result[-1])
        else:
            result.append(text[i])
        i += 1
    return "".join(result)


def strip_narrow_diacritics(text):
    """Remove narrow phonetic diacritics (lowered, dental, etc.) keeping broad."""
    nfd = unicodedata.normalize("NFD", text)
    result = []
    for ch in nfd:
        cp = ord(ch)
        # Skip: combining below (dental ̪ U+032A, lowered ̞ U+031E,
        # non-syllabic ̯ U+032F, devoiced ̥ U+0325, ring below ̊ U+030A)
        if cp in (0x032A, 0x031E, 0x032F, 0x0325, 0x030A):
            continue
        result.append(ch)
    return unicodedata.normalize("NFC", "".join(result))


def apply_reverse_rules(text, rules):
    """Apply ordered replacement rules (longest match first)."""
    sorted_rules = sorted(rules, key=lambda r: len(r[0]), reverse=True)
    result = []
    i = 0
    while i < len(text):
        matched = False
        for pattern, replacement in sorted_rules:
            if text[i:i + len(pattern)] == pattern:
                result.append(replacement)
                i += len(pattern)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)
