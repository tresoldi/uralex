"""Shared utilities for orthography-to-IPA conversion."""

import unicodedata


def apply_rules(text, rules):
    """Apply ordered replacement rules with greedy longest-match-first."""
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


IPA_MODIFIERS = set("\u02D0\u02D1\u02B0\u02B2\u02B7\u02E0\u02E4\u02BC\u02C8\u207F")

def segment_ipa(ipa_text):
    """Segment IPA string into a list of segments."""
    text = unicodedata.normalize("NFD", ipa_text)
    segments = []
    current = ""

    in_tie = False
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in ("\u0361", "\u035C"):  # tie bars -- check BEFORE combining marks
            current += ch
            in_tie = True
        elif cat.startswith("M"):
            current += ch
        elif ch in IPA_MODIFIERS:
            current += ch
        elif ch in " \t-.,;:()[]/_":
            if current:
                segments.append(unicodedata.normalize("NFC", current))
                current = ""
            in_tie = False
        else:
            if in_tie:
                # Next char after tie bar is part of the same segment
                current += ch
                in_tie = False
            else:
                if current:
                    segments.append(unicodedata.normalize("NFC", current))
                current = ch

    if current:
        segments.append(unicodedata.normalize("NFC", current))

    return segments


def validate_ipa_chars(ipa):
    """Check if all characters in the IPA string are valid IPA."""
    bad = []
    for ch in ipa:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            continue  # combining marks OK
        if ch in " \t":
            continue
        # IPA ranges: Latin (basic + extended), IPA extensions, spacing modifiers
        if any([
            0x0041 <= cp <= 0x007A,  # basic Latin
            0x00C0 <= cp <= 0x024F,  # Latin extended
            0x0250 <= cp <= 0x02AF,  # IPA extensions
            0x02B0 <= cp <= 0x02FF,  # spacing modifier letters
            0x0300 <= cp <= 0x036F,  # combining diacriticals
            0x1D00 <= cp <= 0x1D7F,  # phonetic extensions
            0x1DC0 <= cp <= 0x1DFF,  # combining diacriticals supplement
            0x2070 <= cp <= 0x209F,  # superscripts
            0x2190 <= cp <= 0x21FF,  # arrows (for tone)
            ch in "ːˈˌ.ˑ‿",         # common IPA punctuation
        ]):
            continue
        bad.append((ch, f"U+{cp:04X}", unicodedata.name(ch, "UNKNOWN")))
    return bad
