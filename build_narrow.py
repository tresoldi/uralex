#!/usr/bin/env python3
"""
Build narrow-format raw data from raw/ and archive/cldf/.

Reads raw/*.tsv + archive/cldf/forms.csv (for Segments and corrected IPA),
writes normalized files to raw_narrow/.
"""

import csv
import os
import re
import shutil
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "raw")
CLDF_DIR = os.path.join(SCRIPT_DIR, "archive", "cldf")
OUT_DIR = os.path.join(SCRIPT_DIR, "raw_narrow")

# Status markers in the raw item column
STATUS_MARKERS = {
    "[No equivalent]": "no_equivalent",
    "[Form not found]": "form_not_found",
    "[Not reconstructable]": "not_reconstructable",
}

# Column name normalization map
COLUMN_RENAMES = {
    "item_UPA": "item_upa",
    "item_IPA": "item_ipa",
    "iso-639-3": "iso_639_3",
    "LJ_rank": "lj_rank",
    "Leipzig-Jakarta": "leipzig_jakarta",
    "Swadesh100": "swadesh100",
    "Swadesh200": "swadesh200",
    "Swadesh207": "swadesh207",
    "Fullbasic": "fullbasic",
    "Ura100": "ura100",
    "WOLD401-500": "wold401_500",
}

# New Data.tsv column order
DATA_COLUMNS = [
    "uralex_lang", "uralex_mng", "variant", "status",
    "item", "item_alt", "item_upa", "item_upa_alt",
    "item_ipa", "item_ipa_alt", "segments",
    "form_set", "cogn_set",
    "borr_source", "borr_qual",
    "etym_notes", "glossing_notes", "general_notes",
    "ref_cogn", "ref_borr", "ref_item",
]


def read_tsv(path):
    """Read a quoted-TSV file and return (headers, rows). Strips whitespace from cells."""
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        headers = [h.strip() for h in next(reader)]
        for row in reader:
            if row:
                rows.append([cell.strip() for cell in row])
    return headers, rows


def write_tsv(path, headers, rows):
    """Write a TSV file (no quoting unless necessary)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def normalize_column(name):
    """Normalize a column name to lowercase with underscores."""
    if name in COLUMN_RENAMES:
        return COLUMN_RENAMES[name]
    return name.lower()


def clean_ipa(value):
    """Fix known encoding issues in IPA values."""
    if not value:
        return value
    value = value.replace(":", "ː")  # ASCII colon → IPA length mark
    value = value.replace("\u00a0", " ")  # non-breaking space → regular space
    return value


def clean_upa(value):
    """Fix known encoding issues in UPA values."""
    if not value:
        return value
    value = value.replace("'", "ʹ")  # ASCII apostrophe → modifier letter prime
    value = value.replace("\u00a0", " ")  # non-breaking space → regular space
    return value


def segments_match_ipa(segments, ipa):
    """
    Check if a segments string plausibly matches an IPA string.
    Segments are space-separated IPA segments, e.g. "t ɑ n".
    Joining them should reconstruct the IPA: "tɑn".
    Returns False if segments clearly belong to a different form.
    """
    if not segments or not ipa:
        return True  # can't check, assume OK

    # Reject segments that contain tilde (combined from multiple forms)
    if "~" in segments:
        return False

    reconstructed = segments.replace(" ", "")
    # Normalize for comparison: strip hyphens, parentheses
    ipa_clean = ipa.replace("-", "").replace("(", "").replace(")", "")
    reconstructed_clean = reconstructed.replace("-", "").replace("(", "").replace(")", "")

    if reconstructed_clean == ipa_clean:
        return True

    # Length check: if the reconstructed segments are much longer or shorter
    # than the IPA, they're probably from a different form. Allow some
    # tolerance for diacritics and combining characters.
    len_ratio = len(reconstructed_clean) / max(len(ipa_clean), 1)
    if len_ratio > 1.5 or len_ratio < 0.67:
        return False

    # If lengths are similar, check character overlap.
    # Count how many characters in the reconstructed segments appear
    # in the IPA at roughly the same position.
    matches = 0
    min_len = min(len(reconstructed_clean), len(ipa_clean))
    for i in range(min_len):
        if reconstructed_clean[i] == ipa_clean[i]:
            matches += 1
    overlap = matches / max(min_len, 1)
    return overlap >= 0.6


def split_comma_forms(value):
    """Split comma-separated forms. "maq, mina, minno" -> ["maq", "mina", "minno"]."""
    if not value:
        return [""]
    return [part.strip() for part in value.split(", ")]


def split_tilde(value):
    """
    Split tilde-separated variants. Returns (main, alt).
    "mina ~ ma" -> ("mina", "ma")
    "takan ~ takah ~ takahn" -> ("takan", "takah ~ takahn")
    "" -> ("", "")
    """
    if not value or " ~ " not in value:
        return value or "", ""
    parts = value.split(" ~ ")
    return parts[0].strip(), " ~ ".join(parts[1:]).strip()


def split_tilde_or_comma(trans_value, item_value):
    """
    Split a transcription value (UPA/IPA) into (main, alt), matching the
    structure of the item value.

    The raw data sometimes uses commas in UPA/IPA where item uses tildes.
    E.g., item="di ~ da" but UPA="di, da". We detect this by checking
    if item has tildes but the transcription doesn't, and the comma-split
    count matches the tilde-split count.
    """
    if not trans_value:
        return "", ""

    # If transcription itself has tildes, use normal tilde split
    if " ~ " in trans_value:
        return split_tilde(trans_value)

    # If item has no tildes either, no alt needed
    if " ~ " not in item_value:
        return trans_value, ""

    # Item has tildes, transcription has commas instead
    item_variant_count = item_value.count(" ~ ") + 1
    trans_parts = [p.strip() for p in trans_value.split(", ")]

    if len(trans_parts) == item_variant_count:
        return trans_parts[0], " ~ ".join(trans_parts[1:])

    # Counts don't match — return as-is
    return trans_value, ""


def build_cldf_lookup():
    """
    Build a lookup from CLDF forms.csv to get Segments and item_IPA.
    Returns dict keyed by (uralex_lang, uralex_mng, form) -> (segments, item_ipa).
    Only includes rows where Segments is filled (i.e., the conversion touched them).
    """
    # Build CLDF ID -> name mappings
    lang_map = {}
    with open(os.path.join(CLDF_DIR, "languages.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lang_map[row["ID"]] = row["Name"]

    param_map = {}
    with open(os.path.join(CLDF_DIR, "parameters.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            param_map[row["ID"]] = row["Name"]

    # Build name -> uralex_lang mapping from Languages.tsv
    name_to_uralex = {}
    lang_headers, lang_rows = read_tsv(os.path.join(RAW_DIR, "Languages.tsv"))
    lang_col = lang_headers.index("uralex_lang")
    name_col = lang_headers.index("language")
    for row in lang_rows:
        name_to_uralex[row[name_col]] = row[lang_col]

    # Read CLDF forms and build lookup
    cldf_lookup = {}  # (uralex_lang, uralex_mng, form) -> (segments, item_ipa)
    with open(os.path.join(CLDF_DIR, "forms.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lang_id = row["Language_ID"]
            param_id = row["Parameter_ID"]
            form = row.get("Form", "").strip()
            segments = row.get("Segments", "").strip()
            item_ipa = row.get("item_IPA", "").strip()

            if not segments or not form:
                continue

            cldf_lang_name = lang_map.get(lang_id, "")
            cldf_param_name = param_map.get(param_id, "")

            # Map CLDF language name to uralex_lang
            uralex_lang = name_to_uralex.get(cldf_lang_name, "")
            if not uralex_lang:
                for ul, ln in [(r[lang_col], r[name_col]) for r in lang_rows]:
                    if ln == cldf_lang_name:
                        uralex_lang = ul
                        break

            uralex_mng = cldf_param_name

            key = (uralex_lang.lower(), uralex_mng.lower(), form)
            cldf_lookup[key] = (segments, item_ipa)

    # Build secondary lookup by (lang, meaning) for single-form meanings.
    # This handles cases where raw item and CLDF Form differ in spelling.
    lang_mng_forms = {}  # (lang, mng) -> [(form, segments, ipa), ...]
    for (lang, mng, form), (seg, ipa) in cldf_lookup.items():
        lang_mng_forms.setdefault((lang, mng), []).append((form, seg, ipa))

    cldf_fallback = {}  # (lang, mng) -> (segments, ipa)
    for (lang, mng), forms in lang_mng_forms.items():
        if len(forms) == 1:
            _, seg, ipa = forms[0]
            cldf_fallback[(lang, mng)] = (seg, ipa)

    return cldf_lookup, cldf_fallback


def regroup_transcription(trans_parts, item_parts):
    """
    Regroup transcription parts (UPA/IPA) to align with item parts.

    Problem: item may have "tan ~ tani, tate̮n" (2 comma parts, first has tilde),
    but UPA has "tan, tani, tate̮n" (3 comma parts, no tildes).
    We need to regroup UPA as ["tan, tani", "tate̮n"] to match item structure.

    Strategy: count tilde groups in each item part. An item part with N tildes
    consumes N+1 transcription parts, joined with ", ".
    """
    if len(trans_parts) == len(item_parts):
        return trans_parts

    result = []
    ti = 0  # index into trans_parts
    for item_part in item_parts:
        n_variants = item_part.count(" ~ ") + 1
        chunk = trans_parts[ti:ti + n_variants]
        ti += n_variants
        result.append(", ".join(chunk))

    # If we have leftover transcription parts, append them to last group
    if ti < len(trans_parts):
        leftover = ", ".join(trans_parts[ti:])
        if result:
            result[-1] = result[-1] + ", " + leftover if result[-1] else leftover
        else:
            result.append(leftover)

    # Pad if needed
    while len(result) < len(item_parts):
        result.append("")

    return result[:len(item_parts)]


def align_comma_splits(item_parts, upa_value, ipa_value):
    """
    When item has comma-separated forms, align the UPA and IPA values
    to each form. Handles mixed comma+tilde cases where UPA/IPA may
    have more comma parts than item (because item groups tilde variants).
    Returns list of (upa, ipa) tuples aligned to item_parts.
    """
    upa_parts = split_comma_forms(upa_value) if upa_value else [""] * len(item_parts)
    ipa_parts = split_comma_forms(ipa_value) if ipa_value else [""] * len(item_parts)

    upa_parts = regroup_transcription(upa_parts, item_parts)
    ipa_parts = regroup_transcription(ipa_parts, item_parts)

    return list(zip(upa_parts, ipa_parts))


def transform_data(cldf_lookup, cldf_fallback):
    """Transform raw Data.tsv into narrow format rows."""
    headers, rows = read_tsv(os.path.join(RAW_DIR, "Data.tsv"))

    # Build column index map
    col = {h: i for i, h in enumerate(headers)}

    # First pass: build all rows without variant numbers
    out_rows = []
    for row in rows:
        # Pad row if needed
        while len(row) < len(headers):
            row.append("")

        uralex_lang = row[col["uralex_lang"]].lower()
        uralex_mng = row[col["uralex_mng"]]
        item_raw = row[col["item"]]
        upa_raw = row[col["item_UPA"]]
        ipa_raw = row[col["item_IPA"]]
        form_set = row[col["form_set"]]
        cogn_set = row[col["cogn_set"]]
        borr_source = row[col["borr_source"]].lower() if row[col["borr_source"]] else ""
        borr_qual = row[col["borr_qual"]]
        etym_notes = row[col["etym_notes"]]
        glossing_notes = row[col["glossing_notes"]]
        general_notes = row[col["general_notes"]]
        ref_cogn = row[col["ref_cogn"]]
        ref_borr = row[col["ref_borr"]]
        ref_item = row[col["ref_item"]]

        # Check for status markers
        status = ""
        for marker, status_val in STATUS_MARKERS.items():
            if item_raw == marker:
                status = status_val
                break

        # Normalize form_set and cogn_set
        if form_set in ("0", "?"):
            form_set = ""
        if cogn_set in ("0", "?"):
            cogn_set = ""

        if status:
            # Status row: no form data
            out_rows.append({
                "uralex_lang": uralex_lang,
                "uralex_mng": uralex_mng,
                "variant": "1",
                "status": status,
                "item": "", "item_alt": "",
                "item_upa": "", "item_upa_alt": "",
                "item_ipa": "", "item_ipa_alt": "",
                "segments": "",
                "form_set": form_set, "cogn_set": cogn_set,
                "borr_source": borr_source, "borr_qual": borr_qual,
                "etym_notes": etym_notes, "glossing_notes": glossing_notes,
                "general_notes": general_notes,
                "ref_cogn": ref_cogn, "ref_borr": ref_borr, "ref_item": ref_item,
            })
            continue

        # Split comma-separated forms
        item_parts = split_comma_forms(item_raw)
        transcriptions = align_comma_splits(item_parts, upa_raw, ipa_raw)

        for variant_idx, (item_form, (upa_form, ipa_form)) in enumerate(
            zip(item_parts, transcriptions), start=1
        ):
            # Split tilde variants
            item_main, item_alt = split_tilde(item_form)

            # UPA/IPA may use commas where item uses tildes.
            # If item has tilde but UPA/IPA doesn't, and UPA/IPA has commas
            # with the same variant count, treat commas as tilde equivalent.
            upa_main, upa_alt = split_tilde_or_comma(upa_form, item_form)
            upa_main, upa_alt = clean_upa(upa_main), clean_upa(upa_alt)
            ipa_main, ipa_alt = split_tilde_or_comma(ipa_form, item_form)
            ipa_main, ipa_alt = clean_ipa(ipa_main), clean_ipa(ipa_alt)

            # Look up segments and IPA from CLDF
            # Try full tilde form first (CLDF keeps tilde forms unsplit),
            # then fall back to main part only
            cldf_segments = ""
            cldf_ipa = ""
            if item_alt:
                cldf_entry = cldf_lookup.get(
                    (uralex_lang, uralex_mng.lower(), item_form))
                if cldf_entry:
                    cldf_segments, cldf_ipa = cldf_entry
            if not cldf_segments:
                cldf_entry = cldf_lookup.get(
                    (uralex_lang, uralex_mng.lower(), item_main))
                if cldf_entry:
                    cldf_segments, cldf_ipa = cldf_entry

            # Fallback: if form-based lookup failed and this meaning has
            # only one form in CLDF, use that (handles spelling differences
            # between raw item and CLDF Form, e.g. Western Votic).
            if not cldf_segments:
                fb = cldf_fallback.get((uralex_lang, uralex_mng.lower()))
                if fb:
                    cldf_segments, cldf_ipa = fb

            # Validate segments against the form's IPA. The CLDF sometimes
            # has segments from a different form in the same Value group.
            # Also handle tilde in segments (combined from multiple forms).
            segments = cldf_segments

            # Use CLDF IPA when available (has fixes from conversion),
            # fall back to raw IPA otherwise.
            # But: CLDF item_IPA sometimes has the full original string
            # (all comma-separated variants) even for tilde forms. Only
            # use it when the variant count matches the item form.
            if cldf_ipa:
                cldf_ipa_main, cldf_ipa_alt = split_tilde_or_comma(
                    cldf_ipa, item_form)
                # Check if the split worked — if cldf_ipa_main still has
                # commas it means the counts didn't match and we should
                # fall back to raw IPA (which was already properly split)
                if ", " not in cldf_ipa_main:
                    ipa_main = clean_ipa(cldf_ipa_main)
                    ipa_alt = clean_ipa(cldf_ipa_alt)

            # Validate segments against the final IPA. Clear if mismatched.
            if segments and not segments_match_ipa(segments, ipa_main):
                segments = ""

            out_rows.append({
                "uralex_lang": uralex_lang,
                "uralex_mng": uralex_mng,
                "variant": "",  # assigned in second pass
                "status": "",
                "item": item_main, "item_alt": item_alt,
                "item_upa": upa_main, "item_upa_alt": upa_alt,
                "item_ipa": ipa_main, "item_ipa_alt": ipa_alt,
                "segments": segments,
                "form_set": form_set, "cogn_set": cogn_set,
                "borr_source": borr_source, "borr_qual": borr_qual,
                "etym_notes": etym_notes, "glossing_notes": glossing_notes,
                "general_notes": general_notes,
                "ref_cogn": ref_cogn, "ref_borr": ref_borr, "ref_item": ref_item,
            })

    # Second pass: assign sequential variant numbers per (lang, meaning)
    variant_counters = {}
    for row in out_rows:
        key = (row["uralex_lang"], row["uralex_mng"])
        variant_counters[key] = variant_counters.get(key, 0) + 1
        row["variant"] = str(variant_counters[key])

    return out_rows


def transform_simple_tsv(filename, lowercase_lang_col=False):
    """Transform a simple TSV file: normalize column names, optionally lowercase lang keys."""
    headers, rows = read_tsv(os.path.join(RAW_DIR, filename))
    new_headers = [normalize_column(h) for h in headers]

    if lowercase_lang_col and "uralex_lang" in new_headers:
        lang_idx = new_headers.index("uralex_lang")
        for row in rows:
            if lang_idx < len(row):
                row[lang_idx] = row[lang_idx].lower()

    return new_headers, rows


def transform_meaning_list_descriptions():
    """Transform Meaning_list_descriptions.tsv: lowercase list names."""
    headers, rows = read_tsv(os.path.join(RAW_DIR, "Meaning_list_descriptions.tsv"))
    new_headers = [normalize_column(h) for h in headers]

    # The "list" column values need to be lowercased and normalized
    # to match the new column names in Meaning_lists.tsv
    list_name_map = {
        "Fullbasic": "fullbasic",
        "Leipzig-Jakarta": "leipzig_jakarta",
        "Swadesh100": "swadesh100",
        "Swadesh200": "swadesh200",
        "Swadesh207": "swadesh207",
        "Ura100": "ura100",
        "WOLD401-500": "wold401_500",
    }

    list_idx = new_headers.index("list")
    for row in rows:
        if list_idx < len(row) and row[list_idx] in list_name_map:
            row[list_idx] = list_name_map[row[list_idx]]

    return new_headers, rows


def main():
    # Create output directory
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Building CLDF segments lookup...")
    cldf_lookup, cldf_fallback = build_cldf_lookup()
    print(f"  Found {len(cldf_lookup)} forms with segments/IPA")
    print(f"  Found {len(cldf_fallback)} single-form meanings for fallback")

    # Transform Data.tsv
    print("Transforming Data.tsv...")
    data_rows = transform_data(cldf_lookup, cldf_fallback)
    write_tsv(
        os.path.join(OUT_DIR, "Data.tsv"),
        DATA_COLUMNS,
        [[r[c] for c in DATA_COLUMNS] for r in data_rows],
    )
    print(f"  Wrote {len(data_rows)} rows")

    # Count segments matches
    seg_count = sum(1 for r in data_rows if r["segments"])
    print(f"  {seg_count} rows with segments")

    # Transform Languages.tsv
    print("Transforming Languages.tsv...")
    h, r = transform_simple_tsv("Languages.tsv", lowercase_lang_col=True)
    write_tsv(os.path.join(OUT_DIR, "Languages.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Transform Meanings.tsv
    print("Transforming Meanings.tsv...")
    h, r = transform_simple_tsv("Meanings.tsv")
    write_tsv(os.path.join(OUT_DIR, "Meanings.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Transform Meaning_lists.tsv
    print("Transforming Meaning_lists.tsv...")
    h, r = transform_simple_tsv("Meaning_lists.tsv")
    write_tsv(os.path.join(OUT_DIR, "Meaning_lists.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Transform Meaning_examples.tsv
    print("Transforming Meaning_examples.tsv...")
    h, r = transform_simple_tsv("Meaning_examples.tsv")
    write_tsv(os.path.join(OUT_DIR, "Meaning_examples.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Transform Language_compilers.tsv
    print("Transforming Language_compilers.tsv...")
    h, r = transform_simple_tsv("Language_compilers.tsv", lowercase_lang_col=True)
    write_tsv(os.path.join(OUT_DIR, "Language_compilers.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Transform Meaning_list_descriptions.tsv
    print("Transforming Meaning_list_descriptions.tsv...")
    h, r = transform_meaning_list_descriptions()
    write_tsv(os.path.join(OUT_DIR, "Meaning_list_descriptions.tsv"), h, r)
    print(f"  Wrote {len(r)} rows")

    # Copy Citations.bib as-is
    print("Copying Citations.bib...")
    shutil.copy2(
        os.path.join(RAW_DIR, "Citations.bib"),
        os.path.join(OUT_DIR, "Citations.bib"),
    )

    print(f"\nDone. Output in {OUT_DIR}/")


if __name__ == "__main__":
    main()
