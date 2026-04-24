# Uralic basic vocabulary with cognate and loanword information

## How to cite

If you use these data please cite
this dataset using the DOI of the [particular released version](../../releases/) you were using.

When you are using UraLex 3.0, you should also cite the following paper which introduces the dataset:

> Vesakoski, Outi; Tresoldi, Tiago; Soosaar, Sven-Erik; de Heer, Mervi; Maurits, Luke; Syrjänen, Kaj; Honkola, Terhi and Dunn, Michael. "Unravelling the disintegration patterns and chronology of the Uralic language family."


## Description

The dataset is described in [uralex_documentation.md](uralex_documentation.md).

This dataset is licensed under a CC-BY-4.0 license.

## Statistics

- **Languages:** 29 (including Proto-Uralic)
- **Meanings:** 313
- **Rows:** 10,498 (10,106 lexical forms, 392 status entries)
- **Synonymy:** 1.16
- **With UPA transcription:** 5,278 (17 languages)
- **With IPA transcription:** 10,106 (29 languages)
- **With segments:** 9,804
- **Borrowings:** 2,184

Statistics can be regenerated with `python3 scripts/stats.py raw/`.

## Repository structure

The data lives in `raw/` as tab-separated value (TSV) files:

- `Data.tsv` -- the main lexical data
- `Languages.tsv` -- language metadata
- `Meanings.tsv` -- meaning definitions
- `Meaning_lists.tsv` -- membership in standardized word lists
- `Meaning_examples.tsv` -- example sentences for meanings
- `Language_compilers.tsv` -- data collectors and checkers
- `Meaning_list_descriptions.tsv` -- descriptions of the word lists
- `Citations.bib` -- BibTeX bibliography

A CLDF conversion of an earlier version of the data is archived in `archive/`.

## Validation

The data can be validated with a zero-dependency Python script:

```bash
python3 scripts/validate.py raw/
```

## Contributors

Name               | GitHub user     | Description | Role
---                | ---             | ---         | ---
Mervi de Heer | @MervideHeer | | author, DataCurator, DataCollector
Mikko Heikkilä | | | author
Kaj Syrjänen | @kasyrj | data collection | Author, DataCurator
Jyri Lehtinen | | | author, DataCollector
Outi Vesakoski | | | author
Toni, Suutari | | | author
Michael Dunn | @evoling | | author
Urho Määttä | | | author
Unni-Päivä Leino | | | author
Luke Maurits | @lmaurits | helped with sources | Other
Tiago Tresoldi | @tresoldi | IPA conversion, data normalization | DataCurator
Robert Forkel | @xrotwang | patron, code | DataCurator
