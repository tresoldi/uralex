"""Build cross-reference between UraLex and NorthEuraLex."""

import csv
import os
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URALEX = os.path.dirname(BASE)
NEL = os.path.join(BASE, "northeuralex", "cldf")


def load_nel_languages():
    """Map Glottocode -> NEL language ID."""
    with open(os.path.join(NEL, "languages.csv")) as f:
        return {r["Glottocode"]: r["ID"] for r in csv.DictReader(f)}


# Manual overrides for Glottocode mismatches between UraLex and NEL
MANUAL_LANG_MAP = {
    "livonian_courland": "liv",   # NEL uses livv1244, UraLex uses west1760
    "mari_hill": "mrj",           # NEL uses west2392, UraLex uses kozy1238
    "mari_meadow": "mhr",         # NEL uses east2328, UraLex uses gras1239
    # No NEL entry for: estonian_south, proto_uralic, saami_pite, saami_ume, votic_western, ingrian
}


def load_uralex_languages():
    """Map uralex_lang -> Glottocode."""
    path = os.path.join(URALEX, "raw", "Languages.tsv")
    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames
        glotto_col = "glottocode" if "glottocode" in cols else "Glottocode"
        lang_col = "uralex_lang" if "uralex_lang" in cols else "uralex_lang"
        return {r[lang_col].lower(): r[glotto_col] for r in reader}


def build_concept_mapping():
    """Match UraLex meanings to NEL parameters by name similarity."""
    # Load NEL parameters
    with open(os.path.join(NEL, "parameters.csv")) as f:
        nel_params = list(csv.DictReader(f))

    # Build lookup: lowercase name -> parameter ID
    nel_by_name = {}
    for p in nel_params:
        name = p["Name"].lower().strip()
        nel_by_name[name] = p["ID"]
        # Also try the gloss part (before ::)
        gloss = p.get("NorthEuralex_Gloss", "")
        if "::" in gloss:
            gloss_word = gloss.split("::")[0].strip().lower()
            nel_by_name[gloss_word] = p["ID"]
        # Also extract from ID: "1_eye" -> "eye"
        if "_" in p["ID"]:
            id_word = p["ID"].split("_", 1)[1].lower()
            nel_by_name[id_word] = p["ID"]
        # Concepticon gloss
        cg = p.get("Concepticon_Gloss", "").lower().replace("_", " ")
        if cg:
            nel_by_name[cg] = p["ID"]

    # Load UraLex meanings
    with open(os.path.join(URALEX, "raw", "Meanings.tsv")) as f:
        uralex_meanings = list(csv.DictReader(f, delimiter="\t"))

    mappings = []
    unmatched = []
    for m in uralex_meanings:
        mng = m["uralex_mng"].strip()
        mng_lower = mng.lower()

        # Try progressively looser matches
        matched = False
        for attempt in [mng_lower, mng_lower.replace("_", " "),
                        mng_lower.replace("_n", ""), mng_lower.split("_")[0]]:
            if attempt in nel_by_name:
                match_type = "exact" if attempt == mng_lower else "fuzzy"
                mappings.append((mng, nel_by_name[attempt], match_type))
                matched = True
                break
        if not matched:
            unmatched.append(mng)

    return mappings, unmatched


def load_nel_forms():
    """Load all NEL forms into a dict: (language_id, parameter_id) -> list of (form, ipa, segments)."""
    forms = {}
    with open(os.path.join(NEL, "forms.csv")) as f:
        for r in csv.DictReader(f):
            key = (r["Language_ID"], r["Parameter_ID"])
            entry = (r["Value"], r["Form"], r["Segments"])
            forms.setdefault(key, []).append(entry)
    return forms


def main():
    print("Loading languages...")
    uralex_langs = load_uralex_languages()
    nel_glotto = load_nel_languages()

    # Build language mapping
    lang_map = {}
    lang_unmapped = []
    for ulang, glotto in uralex_langs.items():
        if ulang in MANUAL_LANG_MAP:
            lang_map[ulang] = MANUAL_LANG_MAP[ulang]
        elif glotto in nel_glotto:
            lang_map[ulang] = nel_glotto[glotto]
        else:
            lang_unmapped.append((ulang, glotto))

    print(f"Language mapping: {len(lang_map)} matched, {len(lang_unmapped)} unmatched")
    if lang_unmapped:
        print(f"  Unmatched: {lang_unmapped}")

    # Save language mapping
    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, "language_mapping.tsv"), "w") as f:
        f.write("uralex_lang\tnel_language_id\tglottocode\n")
        for ulang, nel_id in sorted(lang_map.items()):
            f.write(f"{ulang}\t{nel_id}\t{uralex_langs[ulang]}\n")

    print("\nBuilding concept mapping...")
    mappings, unmatched = build_concept_mapping()
    print(f"Concept mapping: {len(mappings)} matched, {len(unmatched)} unmatched")
    if unmatched:
        print(f"  Unmatched meanings: {unmatched[:20]}{'...' if len(unmatched) > 20 else ''}")

    # Save concept mapping
    with open(os.path.join(out_dir, "concept_mapping.tsv"), "w") as f:
        f.write("uralex_mng\tnel_parameter_id\tmatch_type\n")
        for mng, nel_id, match_type in sorted(mappings):
            f.write(f"{mng}\t{nel_id}\t{match_type}\n")

    # Save unmatched for manual review
    with open(os.path.join(out_dir, "unmatched_concepts.txt"), "w") as f:
        for mng in sorted(unmatched):
            f.write(f"{mng}\n")

    print("\nLoading NEL forms...")
    nel_forms = load_nel_forms()

    # Build per-language cross-reference
    concept_map = {mng: nel_id for mng, nel_id, _ in mappings}

    # Load UraLex data
    with open(os.path.join(URALEX, "raw", "Data.tsv")) as f:
        reader = csv.DictReader(f, delimiter="\t")
        uralex_data = list(reader)

    # Target languages
    targets = set(lang_map.keys())

    print(f"\nBuilding cross-reference for {len(targets)} languages...")
    for ulang in sorted(targets):
        nel_lang = lang_map[ulang]
        rows = [r for r in uralex_data if r["uralex_lang"].lower() == ulang]

        crossref_rows = []
        for r in rows:
            mng = r["uralex_mng"]
            if mng not in concept_map:
                continue
            nel_param = concept_map[mng]
            nel_key = (nel_lang, nel_param)
            nel_entries = nel_forms.get(nel_key, [])

            item = r.get("item", "").strip()
            item_ipa = r.get("item_ipa", r.get("item_IPA", "")).strip()
            status = r.get("status", "").strip()

            if not item and not status:
                continue

            # Get best NEL match
            nel_value = nel_entries[0][0] if nel_entries else ""
            nel_form = nel_entries[0][1] if nel_entries else ""
            nel_segments = nel_entries[0][2] if nel_entries else ""

            crossref_rows.append({
                "uralex_mng": mng,
                "uralex_item": item,
                "uralex_ipa": item_ipa,
                "uralex_status": status,
                "nel_value": nel_value,
                "nel_form": nel_form,
                "nel_segments": nel_segments,
            })

        if crossref_rows:
            # Determine language folder
            family_map = {
                "karelian_proper": "finnic", "veps": "finnic",
                "estonian_south": "finnic", "livonian_courland": "finnic",
                "estonian_standard": "reverse_upa", "finnish_standard": "reverse_upa",
                "saami_north": "saami", "saami_inari": "saami",
                "saami_skolt": "saami", "saami_south": "saami",
                "saami_pite": "saami", "saami_ume": "saami",
                "saami_kildin": "reverse_upa",
                "mari_hill": "volgaic", "moksha": "volgaic",
                "nenets_tundra": "samoyedic",
                "proto_uralic": "reconstruction",
                "hungarian": "reverse_upa",
            }
            family = family_map.get(ulang)
            if family:
                lang_dir = os.path.join(BASE, family, ulang)
            else:
                lang_dir = os.path.join(BASE, ulang)

            os.makedirs(lang_dir, exist_ok=True)
            outpath = os.path.join(lang_dir, "nel_crossref.tsv")
            with open(outpath, "w") as f:
                cols = ["uralex_mng", "uralex_item", "uralex_ipa", "uralex_status",
                        "nel_value", "nel_form", "nel_segments"]
                f.write("\t".join(cols) + "\n")
                for cr in crossref_rows:
                    f.write("\t".join(cr[c] for c in cols) + "\n")

            matched = sum(1 for cr in crossref_rows if cr["nel_form"])
            print(f"  {ulang}: {len(crossref_rows)} rows, {matched} with NEL match")


if __name__ == "__main__":
    main()
