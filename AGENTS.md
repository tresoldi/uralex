# AGENTS.md — onboarding notes (local, not committed)

Lives on disk in the fork but **not tracked in git**. Don't `git add` it
— upstream is `bedlan/uralex` and this is a contributor fork
(`tresoldi/uralex`).

See `~/meta/research/AGENTS.md` for the wider domain context.
`README.md` and `uralex_documentation.md` are the public dataset docs;
`IPA_NOTES.md` is the technical record of the IPA work.

## What this project is

The **UraLex** dataset: Uralic basic vocabulary with cognate and
loanword information, 29 languages (incl. Proto-Uralic), 313 meanings,
~10.5k rows, ~10.1k lexical forms, 2.2k borrowings. Backs Vesakoski
et al. (forthcoming), *"Unravelling the disintegration patterns and
chronology of the Uralic language family."*

Data lives in `raw/` as flat TSVs (Data, Languages, Meanings,
Meaning_lists, etc.) — the project deliberately keeps a flat-TSV
working format alongside the CLDF archived in `archive/`.

## Current state (May 2026)

**Complete on my side.** The IPA work — converting existing UPA
transcriptions to IPA, adding IPA for languages without phonetic
transcription, reverse-engineering UPA for the four IPA-only
languages, filling the `Segments` column — is done (commit `f89c9cd`).
Methodology recorded in `IPA_NOTES.md`; conversion uses **merkmal**
(Tresoldi & Gopal forthcoming).

**Waiting on bedlan team feedback** to proceed with the next release
(UraLex 3.x) and a follow-up phylogenetic analysis.

## Authority

- Upstream: `bedlan/uralex` (BEDLAN consortium).
- I am a **contributor** (listed as "DataCurator: IPA conversion,
  data normalization"), and **will be listed as co-author on the next
  release**.
- Contributions land via PR from `tresoldi/uralex` (fork) → `bedlan`.
  **Don't push directly to upstream.**

## Layout

```
raw/
  Data.tsv                     Main lexical data
  Languages.tsv                Language metadata
  Meanings.tsv                 Meaning definitions
  Meaning_lists.tsv            Word-list membership
  Meaning_examples.tsv         Example sentences
  Language_compilers.tsv       Data collectors / checkers
  Meaning_list_descriptions.tsv
  Citations.bib                Bibliography (BibTeX)
etc/
  ipa_conversion/              UPA→IPA conversion scripts (by family)
scripts/
  validate.py                  Zero-dependency TSV validation
  stats.py                     Regenerate README statistics
  build_narrow.py              Narrow-transcription build
archive/                      CLDF conversion of an earlier version;
                              older scripts and discrepancy reports
IPA_NOTES.md                  Methodology for the IPA work
uralex_documentation.md       Dataset documentation
README.md                     Public-facing entry
```

## Stack

- Python 3, stdlib only for validation
- merkmal (for IPA conversion; lives in `~/chl/merkmal/`)
- venv: `~/.venvs/ling`

## Running things

```bash
python3 scripts/validate.py raw/         # Validate TSVs
python3 scripts/stats.py raw/            # Regenerate statistics
python3 scripts/build_narrow.py raw/     # Build narrow transcription
```

## Conventions (deferred to upstream)

The dataset follows BEDLAN's conventions, not mine. Don't import CHL
style. The flat-TSV-in-`raw/` model is deliberate (not CLDF in the
working tree).

For IPA: broad phonemic transcription throughout, no allophonic
detail unless source notation forces it. See `IPA_NOTES.md` for the
guiding principles and per-family decisions.

## Don't

- Don't push directly to `bedlan/uralex` — PRs from fork only.
- Don't propose to convert `raw/` to CLDF in the working tree — that's
  what `archive/` is for.
- Don't commit this AGENTS.md.
