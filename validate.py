#!/usr/bin/env python3
"""
Validate UraLex raw data files.

Runs structural, referential, and content checks on all TSV files and
Citations.bib. Works with both old-style (raw/) and new-style (raw_narrow/)
column names.

Usage:
    python3 validate.py [directory]

Default directory: raw/

Output: TSV report to stdout with columns:
    level  file  row  column  check  message

Exit code: 0 if no errors (warnings OK), 1 if any errors.
"""

import csv
import os
import re
import sys
import unicodedata


# Column name normalization (accepts both old-style and new-style names)
COLUMN_NORM = {
    "item_upa": "item_upa", "item_ipa": "item_ipa",
    "iso-639-3": "iso_639_3", "iso_639_3": "iso_639_3",
    "lj_rank": "lj_rank", "leipzig-jakarta": "leipzig_jakarta",
    "leipzig_jakarta": "leipzig_jakarta",
    "swadesh100": "swadesh100", "swadesh200": "swadesh200",
    "swadesh207": "swadesh207", "fullbasic": "fullbasic",
    "ura100": "ura100", "wold401-500": "wold401_500",
    "wold401_500": "wold401_500",
}


def norm_col(name):
    """Normalize a column name for comparison."""
    low = name.lower()
    return COLUMN_NORM.get(low, low)


# Required columns per file (using normalized names).
# Optional columns are not listed here but won't trigger errors.
REQUIRED_COLUMNS = {
    "Data.tsv": {"uralex_lang", "uralex_mng", "item"},
    "Languages.tsv": {"uralex_lang", "language"},
    "Meanings.tsv": {"uralex_mng", "definition"},
    "Meaning_lists.tsv": {"uralex_mng"},
    "Meaning_examples.tsv": {"uralex_mng", "example"},
    "Language_compilers.tsv": {"uralex_lang"},
    "Meaning_list_descriptions.tsv": {"list", "description"},
}

# Valid borr_qual values
VALID_BORR_QUAL = {"clear", "probable", "possible"}

# Valid status values (new format)
VALID_STATUS = {"no_equivalent", "form_not_found", "not_reconstructable"}

# Old-format status markers
OLD_STATUS_MARKERS = {"[No equivalent]", "[Form not found]", "[Not reconstructable]"}

# IPA allowed Unicode categories and ranges
# Letters, marks (combining), modifiers, symbols used in IPA
IPA_ALLOWED_CATEGORIES = {"L", "M", "S"}  # broad categories (first letter)
# Specific allowed punctuation/separator chars in IPA/UPA fields
IPA_ALLOWED_CHARS = set(" ,~-*()ʼʹʾ°.")


class Report:
    def __init__(self):
        self.issues = []
        self.error_count = 0
        self.warning_count = 0

    def add(self, level, filename, row, column, check, message):
        self.issues.append((level, filename, str(row), column, check, message))
        if level == "error":
            self.error_count += 1
        else:
            self.warning_count += 1

    def print_report(self):
        print("level\tfile\trow\tcolumn\tcheck\tmessage")
        for issue in self.issues:
            print("\t".join(issue))

    def print_summary(self):
        total = self.error_count + self.warning_count
        print(f"\n{total} issues: {self.error_count} errors, {self.warning_count} warnings",
              file=sys.stderr)


def read_tsv_with_info(path):
    """Read TSV, return (raw_headers, norm_headers, rows_as_dicts, row_count)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        # Check for BOM
        first_bytes = f.read(1)
        if first_bytes == "\ufeff":
            pass  # skip BOM
        else:
            f.seek(0)

        reader = csv.reader(f, delimiter="\t")
        raw_headers = next(reader)
        norm_headers = [norm_col(h) for h in raw_headers]

        for line_num, row in enumerate(reader, start=2):
            if row:
                d = {}
                for i, h in enumerate(norm_headers):
                    d[h] = row[i] if i < len(row) else ""
                d["__row__"] = line_num
                d["__raw_row__"] = row
                d["__raw_col_count__"] = len(row)
                rows.append(d)

    return raw_headers, norm_headers, rows


def parse_bib_keys(path):
    """Extract all BibTeX entry keys from a .bib file."""
    keys = []
    pattern = re.compile(r"^@\w+\{(.+?),", re.MULTILINE)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for match in pattern.finditer(content):
        keys.append(match.group(1).strip())
    return keys


def parse_ref_keys(value):
    """Parse reference field value into individual citation keys."""
    if not value:
        return []
    # References are separated by ", " or ";" or "; "
    parts = re.split(r"[;,]\s*", value)
    return [p.strip() for p in parts if p.strip()]


def check_structure(filename, raw_headers, norm_headers, rows, report):
    """Check TSV structural integrity."""
    expected_col_count = len(raw_headers)

    # Check BOM in header
    if raw_headers and raw_headers[0].startswith("\ufeff"):
        report.add("warning", filename, 1, "", "bom",
                    "File starts with BOM character")

    # Check required columns
    required = REQUIRED_COLUMNS.get(filename, set())
    norm_set = set(norm_headers)
    for req_col in required:
        if req_col not in norm_set:
            report.add("error", filename, 1, req_col, "missing_column",
                        f"Required column '{req_col}' not found")

    # Check column count consistency and trailing whitespace
    for row in rows:
        row_num = row["__row__"]
        raw_col_count = row["__raw_col_count__"]
        raw_row = row["__raw_row__"]

        if raw_col_count != expected_col_count:
            report.add("error", filename, row_num, "", "column_count",
                        f"Expected {expected_col_count} columns, got {raw_col_count}")

        # Check for trailing whitespace in cells
        for i, cell in enumerate(raw_row):
            col_name = norm_headers[i] if i < len(norm_headers) else f"col{i}"
            if cell != cell.strip():
                report.add("warning", filename, row_num, col_name, "trailing_whitespace",
                            f"Cell has leading/trailing whitespace: '{cell[:30]}...'")

    # Check for empty rows (all fields blank)
    for row in rows:
        raw_row = row["__raw_row__"]
        if all(cell.strip() == "" for cell in raw_row):
            report.add("warning", filename, row["__row__"], "", "empty_row",
                        "Completely empty row")


def check_data(rows, norm_headers, languages, meanings, bib_keys, report):
    """Run all Data.tsv validation checks."""
    filename = "Data.tsv"
    has_status = "status" in set(norm_headers)
    has_variant = "variant" in set(norm_headers)
    lang_set = set(languages)
    mng_set = set(meanings)
    bib_set = set(bib_keys) if bib_keys else None

    # Track variant sequences
    variant_tracker = {}  # (lang, mng) -> list of variant numbers

    for row in rows:
        rn = row["__row__"]
        lang = row.get("uralex_lang", "")
        mng = row.get("uralex_mng", "")
        item = row.get("item", "")
        status = row.get("status", "")

        # Foreign key: language
        if lang and lang not in lang_set:
            report.add("error", filename, rn, "uralex_lang", "fk_language",
                        f"'{lang}' not found in Languages.tsv")

        # Foreign key: meaning
        if mng and mng not in mng_set:
            report.add("error", filename, rn, "uralex_mng", "fk_meaning",
                        f"'{mng}' not found in Meanings.tsv")

        # Status validation
        if has_status and status:
            if status not in VALID_STATUS:
                report.add("error", filename, rn, "status", "valid_status",
                            f"Invalid status '{status}', expected: {', '.join(sorted(VALID_STATUS))}")
            # If status set, form fields should be empty
            for fcol in ("item", "item_alt", "item_upa", "item_upa_alt",
                         "item_ipa", "item_ipa_alt", "segments"):
                if row.get(fcol, ""):
                    report.add("warning", filename, rn, fcol, "status_with_form",
                                f"Form field '{fcol}' filled but status is '{status}'")

        # Old-format status markers
        if not has_status and item in OLD_STATUS_MARKERS:
            pass  # valid in old format

        # Variant validation
        if has_variant:
            variant = row.get("variant", "")
            if variant:
                if not variant.isdigit() or int(variant) < 1:
                    report.add("error", filename, rn, "variant", "valid_variant",
                                f"Invalid variant '{variant}', expected positive integer")
                else:
                    key = (lang, mng)
                    variant_tracker.setdefault(key, []).append(int(variant))

        # form_set validation
        form_set = row.get("form_set", "")
        if form_set:
            if not re.match(r"^(\d+|[a-z]{1,2}|\?)$", form_set, re.IGNORECASE):
                report.add("error", filename, rn, "form_set", "valid_form_set",
                            f"Invalid form_set '{form_set}'")

        # cogn_set validation
        cogn_set = row.get("cogn_set", "")
        if cogn_set:
            if not re.match(r"^([a-z]{1,2}|\?)$", cogn_set, re.IGNORECASE):
                report.add("error", filename, rn, "cogn_set", "valid_cogn_set",
                            f"Invalid cogn_set '{cogn_set}'")

        # borr_qual validation
        borr_qual = row.get("borr_qual", "")
        borr_source = row.get("borr_source", "")
        if borr_qual and borr_qual not in VALID_BORR_QUAL:
            report.add("error", filename, rn, "borr_qual", "valid_borr_qual",
                        f"Invalid borr_qual '{borr_qual}', expected: {', '.join(sorted(VALID_BORR_QUAL))}")

        # borr consistency
        if borr_source and not borr_qual:
            report.add("warning", filename, rn, "borr_source", "borr_consistency",
                        "borr_source filled but borr_qual empty")
        if borr_qual and not borr_source:
            report.add("warning", filename, rn, "borr_qual", "borr_consistency",
                        "borr_qual filled but borr_source empty")

        # Citation key validation
        if bib_set is not None:
            for ref_col in ("ref_cogn", "ref_borr", "ref_item"):
                ref_val = row.get(ref_col, "")
                if ref_val:
                    for key in parse_ref_keys(ref_val):
                        if key not in bib_set:
                            report.add("warning", filename, rn, ref_col, "fk_citation",
                                        f"Citation key '{key}' not found in Citations.bib")

        # IPA/UPA character checks
        for ipa_col in ("item_ipa", "item_ipa_alt", "item_upa", "item_upa_alt"):
            ipa_val = row.get(ipa_col, "")
            if ipa_val:
                check_ipa_chars(ipa_val, filename, rn, ipa_col, report)

    # Check variant sequences
    if has_variant:
        for (lang, mng), variants in variant_tracker.items():
            expected = list(range(1, len(variants) + 1))
            if sorted(variants) != expected:
                report.add("warning", filename, 0, "variant", "variant_sequence",
                            f"Non-sequential variants for {lang}/{mng}: {variants}")


def check_ipa_chars(value, filename, row_num, column, report):
    """Check IPA/UPA value for unexpected characters."""
    for ch in value:
        if ch in IPA_ALLOWED_CHARS:
            continue
        cat = unicodedata.category(ch)
        broad_cat = cat[0]
        if broad_cat in ("L", "M"):
            # Letters and combining marks are fine
            continue
        if broad_cat == "S" and cat == "Sk":
            # Modifier symbols (like ʰ, ʷ) are fine
            continue
        if cat == "No":
            # Numeric "other" (like superscripts) - OK
            continue
        if cat == "Pc":
            # Connector punctuation - OK
            continue
        # Flag unexpected character
        code = f"U+{ord(ch):04X}"
        name = unicodedata.name(ch, "UNKNOWN")
        report.add("warning", filename, row_num, column, "ipa_char",
                    f"Unexpected character '{ch}' ({code} {name}) in IPA/UPA value")


def check_languages(rows, data_langs, report):
    """Validate Languages.tsv."""
    filename = "Languages.tsv"

    for row in rows:
        rn = row["__row__"]
        lang = row.get("uralex_lang", "")
        iso = row.get("iso_639_3", "")
        glotto = row.get("glottocode", "")
        subgroup = row.get("subgroup", "")

        # At least one identifier
        if not iso and not glotto:
            report.add("warning", filename, rn, "iso_639_3", "identifier_required",
                        f"Language '{lang}' has neither ISO code nor glottocode")

        # ISO format
        if iso and not re.match(r"^[a-z]{3}$", iso):
            report.add("error", filename, rn, "iso_639_3", "iso_format",
                        f"Invalid ISO 639-3 code '{iso}'")

        # Glottocode format
        if glotto and not re.match(r"^[a-z]{4}\d{4}$", glotto):
            report.add("error", filename, rn, "glottocode", "glottocode_format",
                        f"Invalid glottocode '{glotto}'")

        # Subgroup
        if not subgroup:
            report.add("warning", filename, rn, "subgroup", "subgroup_empty",
                        f"Language '{lang}' has no subgroup")

    # Check for unused languages
    lang_set = {row.get("uralex_lang", "") for row in rows}
    unused = lang_set - data_langs
    for lang in sorted(unused):
        if lang:
            report.add("warning", filename, 0, "uralex_lang", "unused_language",
                        f"Language '{lang}' in Languages.tsv but not in Data.tsv")


def check_meanings(rows, data_mngs, report):
    """Validate Meanings.tsv."""
    filename = "Meanings.tsv"
    mng_set = {row.get("uralex_mng", "") for row in rows}

    unused = mng_set - data_mngs
    for mng in sorted(unused):
        if mng:
            report.add("warning", filename, 0, "uralex_mng", "unused_meaning",
                        f"Meaning '{mng}' in Meanings.tsv but not in Data.tsv")


BOOL_COLS = {"leipzig_jakarta", "fullbasic", "swadesh100", "swadesh200",
             "swadesh207", "ura100", "wold401_500"}


def check_meaning_lists(rows, meanings_set, report):
    """Validate Meaning_lists.tsv."""
    filename = "Meaning_lists.tsv"

    for row in rows:
        rn = row["__row__"]
        mng = row.get("uralex_mng", "")

        # FK to meanings
        if mng and mng not in meanings_set:
            report.add("error", filename, rn, "uralex_mng", "fk_meaning",
                        f"'{mng}' not found in Meanings.tsv")

        # LJ rank
        lj = row.get("lj_rank", "")
        if lj and lj != "-" and not lj.isdigit():
            report.add("error", filename, rn, "lj_rank", "valid_lj_rank",
                        f"Invalid lj_rank '{lj}', expected '-' or positive integer")

        # Boolean columns
        for bc in BOOL_COLS:
            val = row.get(bc, "")
            if val and val not in ("0", "1"):
                report.add("error", filename, rn, bc, "valid_boolean",
                            f"Invalid boolean value '{val}' in {bc}")

        # Logical: swadesh100=1 implies swadesh207=1
        if row.get("swadesh100") == "1" and row.get("swadesh207") != "1":
            report.add("warning", filename, rn, "swadesh207", "list_logic",
                        "swadesh100=1 but swadesh207≠1")

        # Logical: fullbasic consistency
        is_basic = (row.get("swadesh100") == "1" or
                    row.get("swadesh200") == "1" or
                    row.get("leipzig_jakarta") == "1")
        fb = row.get("fullbasic", "")
        if is_basic and fb != "1":
            report.add("warning", filename, rn, "fullbasic", "list_logic",
                        "Member of basic list but fullbasic≠1")
        if not is_basic and fb == "1":
            report.add("warning", filename, rn, "fullbasic", "list_logic",
                        "fullbasic=1 but not in any basic list")


def check_meaning_examples(rows, meanings_set, report):
    """Validate Meaning_examples.tsv."""
    filename = "Meaning_examples.tsv"
    for row in rows:
        rn = row["__row__"]
        mng = row.get("uralex_mng", "")
        if mng and mng not in meanings_set:
            report.add("error", filename, rn, "uralex_mng", "fk_meaning",
                        f"'{mng}' not found in Meanings.tsv")


def check_language_compilers(rows, languages_set, report):
    """Validate Language_compilers.tsv."""
    filename = "Language_compilers.tsv"
    for row in rows:
        rn = row["__row__"]
        lang = row.get("uralex_lang", "")
        if lang and lang not in languages_set:
            report.add("error", filename, rn, "uralex_lang", "fk_language",
                        f"'{lang}' not found in Languages.tsv")


def check_citations(bib_keys, report):
    """Check for duplicate BibTeX keys."""
    seen = {}
    for key in bib_keys:
        if key in seen:
            report.add("error", "Citations.bib", 0, "", "duplicate_bib_key",
                        f"Duplicate BibTeX key '{key}'")
        seen[key] = True


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "raw"

    if not os.path.isdir(data_dir):
        print(f"Error: directory '{data_dir}' not found", file=sys.stderr)
        sys.exit(2)

    report = Report()

    # Read all files
    files = {}
    for fname in ["Data.tsv", "Languages.tsv", "Meanings.tsv",
                   "Meaning_lists.tsv", "Meaning_examples.tsv",
                   "Language_compilers.tsv", "Meaning_list_descriptions.tsv"]:
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            raw_h, norm_h, rows = read_tsv_with_info(path)
            files[fname] = (raw_h, norm_h, rows)
            check_structure(fname, raw_h, norm_h, rows, report)
        else:
            report.add("error", fname, 0, "", "file_missing",
                        f"Expected file '{fname}' not found in {data_dir}")

    # Parse bib
    bib_path = os.path.join(data_dir, "Citations.bib")
    bib_keys = []
    if os.path.exists(bib_path):
        bib_keys = parse_bib_keys(bib_path)
        check_citations(bib_keys, report)
    else:
        report.add("warning", "Citations.bib", 0, "", "file_missing",
                    "Citations.bib not found")

    # Build lookup sets
    languages_set = set()
    if "Languages.tsv" in files:
        languages_set = {r.get("uralex_lang", "") for r in files["Languages.tsv"][2]}

    meanings_set = set()
    if "Meanings.tsv" in files:
        meanings_set = {r.get("uralex_mng", "") for r in files["Meanings.tsv"][2]}

    data_langs = set()
    data_mngs = set()
    if "Data.tsv" in files:
        data_langs = {r.get("uralex_lang", "") for r in files["Data.tsv"][2]}
        data_mngs = {r.get("uralex_mng", "") for r in files["Data.tsv"][2]}

    # Run checks
    if "Data.tsv" in files:
        check_data(files["Data.tsv"][2], files["Data.tsv"][1],
                    languages_set, meanings_set, bib_keys, report)

    if "Languages.tsv" in files:
        check_languages(files["Languages.tsv"][2], data_langs, report)

    if "Meanings.tsv" in files:
        check_meanings(files["Meanings.tsv"][2], data_mngs, report)

    if "Meaning_lists.tsv" in files:
        check_meaning_lists(files["Meaning_lists.tsv"][2], meanings_set, report)

    if "Meaning_examples.tsv" in files:
        check_meaning_examples(files["Meaning_examples.tsv"][2], meanings_set, report)

    if "Language_compilers.tsv" in files:
        check_language_compilers(files["Language_compilers.tsv"][2], languages_set, report)

    # Output
    report.print_report()
    report.print_summary()
    sys.exit(1 if report.error_count > 0 else 0)


if __name__ == "__main__":
    main()
