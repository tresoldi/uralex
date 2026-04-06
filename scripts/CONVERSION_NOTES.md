# IPA conversion notes

Notes on the `tiago-ipa-from-upa` branch: what changed, why, and
what reviewers should look at.


## Background

UraLex v3 has 10,231 lexical entries across 28 Uralic languages.
Before this branch:

- `item_UPA` was filled for 4,162 rows (11 languages)
- `item_IPA` was filled for 5,594 rows (16 languages)
- `Segments` was empty everywhere
- Every row that had UPA also had IPA; no row had UPA without IPA

The IPA column had problems. Some values used deprecated ligature
characters, others had encoding inconsistencies, and multi-form
cells carried the full variant list even when Form had already been
split into separate rows.


## What changed

I ran merkmal's UPA-to-IPA adapter over all 4,162 UPA rows with
language-specific post-processing, then compared the output against
the existing IPA. I investigated every disagreement and decided
what to do case by case.

- 1,168 IPA values changed
- 2,994 IPA values confirmed (conversion matched the original)
- 5,594 Segments values filled (was zero)
- 4,637 rows untouched (no transcription source)


## Decisions on specific discrepancies

### UPA `a` in IPA: `a` or `ɑ`?

merkmal maps UPA `a` to IPA `a` (identity). The existing UraLex IPA
consistently used `ɑ` (open back unrounded) in all 11 languages.
I override merkmal to `ɑ`, matching the database. The override is
in the conversion script, not in merkmal itself.

### UPA `lʹ` in IPA: `lʲ` or `ʎ`?

merkmal maps the modifier prime to secondary palatalization (`ʲ`),
giving `lʲ`. In the Uralic tradition, though, prime on `l` means a
true palatal lateral, not a palatalized alveolar. The existing IPA
across all 11 languages used `ʎ`, so that is what I use.

### UPA `ʒ́` (ezh + acute): `ʒʲ` or `dʑ`?

merkmal treats acute on ʒ as palatalization, giving `ʒʲ`. In UPA
this is actually the voiced alveolo-palatal affricate. The existing
IPA had the ligature `ʥ`; I produce the two-character `dʑ` instead
(see affricates below).

### Affricate notation

The existing IPA used ligature characters: `ʧ` (U+02A7), `ʨ`
(U+02A8), `ʥ` (U+02A5). These are deprecated in current IPA, so I
decompose them to digraphs: `tʃ`, `tɕ`, `dʑ`. About 360 changed
cells come from this alone.

### UPA `ə̑` (schwa + inverted breve above)

merkmal maps the inverted breve above as backing, producing `ɤ`
(close-mid back unrounded). The existing UraLex IPA used `ə̠`
(retracted schwa). Neither is ideal.

The vowel in Komi, Udmurt, and Mari is mid central in standard
descriptions of all three languages. A reviewer of UraLex on the
Freelance Reconstruction blog recommended plain /ə/ as sufficient.
The copius_api tool uses /ɘ/ (close-mid central), which is
reasonable but less conventional. I went with `ə`, overriding
merkmal's `ɤ` in the conversion script.

### Mansi `χ` → `x`

UPA uses Greek chi for the velar fricative. The existing Mansi IPA
kept `χ`, but in IPA that means uvular. The Mansi sound is velar,
so I use `x`.

### Mansi low-ring modifier (U+02F3)

In the Mansi data, the modifier letter low ring appears after velar
stops: `rak˳`, `sēŋk˳`, `ēk˳a`. The Form column renders it as
something that looks like `w`, which confused me at first. The
existing IPA treated it as labialization (`kʷ`), and I follow that
interpretation.

This is Mansi-specific. In other languages the same character would
mean devoicing.

### Geminates

UPA writes geminates as doubled consonants (`ll`, `tt`). The
existing IPA sometimes used length marks (`lː`, `tː`), sometimes
kept the doubled letters. I apply geminate merging for the languages
where the existing IPA showed this pattern: Ingrian, Western Votic,
Selkup, Komi-Zyrian, Komi-Permyak, Udmurt, Erzya, and Sosva Mansi.

### `g` vs `ɡ`

Latin small g (U+0067) and IPA script g (U+0261) are visually
identical in most fonts. I normalize to IPA `ɡ` (U+0261).

### Short vowel breve

UPA combining breve (U+0306) marks short vowels. merkmal converts
it to inverted breve below (U+032F, non-syllabic marker). The
existing IPA in UraLex, especially for Vakh-Vasyugan Khanty, kept
the breve as-is, so I preserve it.


## Multi-form handling

UraLex has two kinds of multi-form entries:

**Comma-separated in Value** (389 concept-language pairs): the CLDF
FormSpec already split these into separate rows. Each row has its
own Form (`jažams` or `jažavtoms`), but `item_UPA` still has the
full comma string from Value. The script matches each Form to the
correct UPA variant.

**Tilde-separated in Form** (282 rows): these were not split into
rows. A single row has `Form = di ~ da`, `item_UPA = di, da`. I
produce all variants in `item_IPA` (`di, dɑ`), matching the
original convention. For Segments I use only the first variant
(`d i`) -- concatenating both would look like a single four-segment
word, which would be wrong.

These 282 tilde rows should eventually be split into separate CLDF
rows with their own Form, item_IPA, and Segments.


## Where the overrides live

All language-specific overrides are in `scripts/apply_ipa_fixes.py`.
merkmal's UPA adapter stays language-agnostic. Character-level
UPA-to-IPA mapping belongs in the adapter; language-specific
phonological decisions (is this vowel back or central? is this a
true palatal or a palatalized alveolar?) belong with the dataset.


## Segments

The Segments column was empty before this branch. I fill it for
all 5,594 rows that have IPA:

- 4,162 from UPA conversion (merkmal returns a segment list directly)
- 1,432 from segmenting existing IPA (Finnish, Estonian, Hungarian,
  Kildin Saami) by grouping base characters with their combining
  marks and modifier letters

Format: space-separated IPA segments, e.g. `t ɯ l` or `s ɑː ŋ xʷ i`.


## Examples

IPA modified (I changed what was there):

| Language | Form | Old IPA | New IPA | Why |
|----------|------|---------|---------|-----|
| Erzya | vačoči | vɑʧoʧi | vɑtʃotʃi | Ligature to digraph |
| Komi-Permyak | aʒ́ʒ́i̮ni̮ | ɑʥːɯnɯ | ɑdʑːɯnɯ | Ligature to digraph |
| Komi-Zyrian | iće̮t | iʨɤt | itɕɤt | Ligature to digraph |
| Udmurt | śubeg | ɕubeg | ɕubeɡ | g to ɡ |
| Mansi | χuji ~ χoji | χuji, χoji | xuji, xoji | χ to x (velar) |
| Meadow Mari | uδə̑rem | uðə̠rem | uðərem | ə̠ to ə |
| Nganasan | dʹindiśi | dʲinsiɕi | dʲindiɕi | Genuine error (d was s) |
| Udmurt | tšoš | ʧoʃ, ʧoʃen | tʃoʃ | Multi-form matched + ligature |
| W. Votic | takan̄ | tɑkɑn | tɑkɑnː | Length mark was missing |

IPA unchanged, Segments added (conversion matched):

| Language | Form | IPA | Segments |
|----------|------|-----|----------|
| Udmurt | vi̮n | vɯn | v ɯ n |
| Sosva Mansi | wolʹk | woʎk | w o ʎ k |
| Selkup | qē̮ | qɤː | q ɤː |
| Komi-Zyrian | pe̮jim | pɤjim | p ɤ j i m |

IPA-only languages (no UPA available, only Segments added):

| Language | Form | IPA | Segments |
|----------|------|-----|----------|
| Finnish | juuri | juːri | j uː r i |
| Estonian | lill | lilː | l i lː |
| Hungarian | felszed | fɛlsɛd | f ɛ l s ɛ d |
| Kildin Saami | nēmm | neːmː | n eː mː |


## How to reproduce

```bash
cd uralex/
PYTHONPATH=/path/to/distfeat/src python3 scripts/apply_ipa_fixes.py
```

The script reads `archive/cldf/forms.csv`, applies all conversions, and
writes the result back. Statistics go to stdout.

`scripts/ipa_discrepancy_report.py` compares item_IPA against raw
merkmal output (without the overrides) and produces a report grouped
by language and type. I used it during development to find the
patterns described above.
