# IPA transcription notes

This document covers all the IPA work done for UraLex: the conversion
of existing UPA transcriptions to IPA, the addition of IPA for languages
that had no phonetic transcription at all, and the reverse-engineering
of UPA for four languages that only had IPA. It also describes how the
Segments column was filled.

The UPA-to-IPA conversion used merkmal (Tresoldi and Gopal,
forthcoming). The conversion scripts are in `etc/ipa_conversion/`,
organized by language family. The earlier pipeline and its discrepancy
report are archived in `archive/scripts/`.


## Guiding principles

We targeted a **broad phonemic transcription** throughout, with no
predictable allophones and no narrow phonetic detail unless the
source notation forced it. Finnish [x] before stops, North Saami
pre-aspiration, Estonian palatalization before front vowels: none
of these appear in the IPA, because the source notation does not
encode them and including them would overcommit to particular surface
forms.

Where our choices disagree with NorthEuraLex, we stuck with whatever
keeps UraLex internally consistent. NEL uses /ɛ/ and /ɔ/ for
Karelian mid vowels; we use /e/ and /o/, the phonemic values from
the Oxford chapter on Karelian, because a broad transcription should
reflect the phoneme system rather than surface quality. The same
reasoning applies to /ɑ/ for the open back vowel, a convention
already established in the 11 languages that had UPA from the start.

We also tried to respect whatever system the original compiler of
each language used. The `item` field was populated by different
scholars at different times: some languages arrived in standard
literary spelling, some in UPA or something close to it, and some
in one-off semi-phonetic notation. Each converter was built for the
system actually in front of us.


## Phase 1: UPA-to-IPA conversion (11 languages)

The first phase ran the UPA-to-IPA adapter over all 4,162 UPA
rows with language-specific post-processing, then compared the output
against the existing IPA. Every disagreement was investigated and
decided case by case.

- 1,168 IPA values changed
- 2,994 IPA values confirmed (conversion matched the original)
- 5,594 Segments values filled (was zero)
- 4,637 rows untouched (no transcription source)


### Specific discrepancy decisions

**UPA `a` in IPA: `a` or `ɑ`?** The default UPA-to-IPA mapping gives
`a` (identity). The existing UraLex IPA consistently used `ɑ` (open
back unrounded) in all 11 languages. We override to `ɑ`, matching
the database convention.

**UPA `lʹ` in IPA: `lʲ` or `ʎ`?** The default mapping treats the modifier prime as
secondary palatalization (`ʲ`), giving `lʲ`. In the Uralic
tradition, though, prime on `l` means a true palatal lateral, not a
palatalized alveolar. The existing IPA across all 11 languages used
`ʎ`, so that is what we keep.

**UPA `ʒ́` (ezh + acute): `ʒʲ` or `dʑ`?** The default mapping treats acute on
ʒ as palatalization, giving `ʒʲ`. In UPA this is actually the voiced
alveolo-palatal affricate. The existing IPA had the ligature `ʥ`; we
produce the two-character `dʑ` instead (see affricates below).

**Affricate notation.** The existing IPA used ligature characters:
`ʧ` (U+02A7), `ʨ` (U+02A8), `ʥ` (U+02A5). These are deprecated
in current IPA, so we decompose them to digraphs: `tʃ`, `tɕ`, `dʑ`.
About 360 changed cells come from this alone.

**UPA `ə̑` (schwa + inverted breve above).** The default mapping
treats the inverted breve as backing, producing `ɤ` (close-mid back unrounded).
The existing UraLex IPA used `ə̠` (retracted schwa). Neither is
ideal. The vowel in Komi, Udmurt, and Mari is mid central in
standard descriptions. A reviewer on the Freelance Reconstruction
blog recommended plain /ə/; the copius_api tool uses /ɘ/ (close-mid
central), which is reasonable but less conventional. We went with `ə`.

**Mansi `χ` --> `x`.** UPA uses Greek chi for the velar fricative.
The existing Mansi IPA kept `χ`, but in IPA that means uvular. The
Mansi sound is velar, so we use `x`.

**Mansi low-ring modifier (U+02F3).** In the Mansi data, the modifier
letter low ring appears after velar stops: `rak˳`, `sēŋk˳`, `ēk˳a`.
The Form column renders it as something that looks like `w`, which
was initially confusing. The existing IPA treated it as labialization
(`kʷ`), and we follow that interpretation. This is Mansi-specific;
in other languages the same character would mean devoicing.

**Geminates.** UPA writes geminates as doubled consonants (`ll`,
`tt`). The existing IPA sometimes used length marks (`lː`, `tː`),
sometimes kept the doubled letters. We apply geminate merging for
the languages where the existing IPA showed this pattern: Ingrian,
Western Votic, Selkup, Komi-Zyrian, Komi-Permyak, Udmurt, Erzya,
and Sosva Mansi.

**`g` vs `ɡ`.** Latin small g (U+0067) and IPA script g (U+0261)
are visually identical in most fonts. We normalize to IPA `ɡ`
(U+0261).

**Short vowel breve.** UPA combining breve (U+0306) marks short
vowels. The default conversion produces inverted breve below (U+032F,
non-syllabic marker). The existing IPA in UraLex, especially for
Vakh-Vasyugan Khanty, kept the breve as-is, so we preserve it.


### Multi-form handling

UraLex has two kinds of multi-form entries:

**Comma-separated in Value** (389 concept-language pairs): the CLDF
FormSpec already split these into separate rows. Each row has its
own Form (`jažams` or `jažavtoms`), but `item_UPA` still has the
full comma string from Value. The script matches each Form to the
correct UPA variant.

**Tilde-separated in Form** (282 rows): these were not split into
rows. A single row has `Form = di ~ da`, `item_UPA = di, da`. We
produce all variants in `item_IPA` (`di, dɑ`), matching the
original convention. For Segments we use only the first variant
(`d i`); concatenating both would look like a single four-segment
word.

These 282 tilde rows should eventually be split into separate CLDF
rows with their own Form, item_IPA, and Segments.


### Phase 1 examples

IPA modified (we changed what was there):

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


### Where the overrides live

All language-specific overrides for this phase are in
`archive/scripts/apply_ipa_fixes.py`. The UPA adapter is
language-agnostic. Character-level UPA-to-IPA mapping belongs in
the adapter; language-specific phonological decisions (is this vowel
back or central? is this a true palatal or a palatalized alveolar?)
belong with the dataset.

To reproduce:

```bash
cd uralex/
python3 archive/scripts/apply_ipa_fixes.py
```

`archive/scripts/ipa_discrepancy_report.py` compares item_IPA
against raw adapter output (without the overrides) and produces a
report grouped by language and type.


## Phase 2: orthography-to-IPA expansion (14 languages)

The second phase added IPA transcriptions for the 14 languages that
had none, bringing coverage from 5,257 rows (16 languages) to 10,106
rows (all 29). The workflow was roughly the same for each language:
look at the character inventory of the `item` field, compare
overlapping entries with NorthEuraLex to find the systematic
correspondences, chase down anything ambiguous in the literature,
write ordered replacement rules, and validate against the NEL
cross-reference. Languages were done one at a time, grouped by family.

The conversion scripts are in `etc/ipa_conversion/`, organized by
family (finnic/, saami/, volgaic/, samoyedic/, reconstruction/).
Each language has a `rules.py` with the ordered replacement rules and
an `apply.py` that runs them against the data and validates.


### Karelian Proper (403 items)

Karelian uses a standard Latin orthography that reads a lot like
Finnish, phonemically transparent, with ä, š, and ö as the only
non-ASCII characters of note. Matching 135 Karelian words against
NorthEuraLex gave a 99.3% agreement rate once you account for the
vowel-quality choices discussed below.

Vowels: a --> /ɑ/, e --> /e/, i --> /i/, o --> /o/, u --> /u/, y --> /y/,
ä --> /æ/, ö --> /ø/. We went with /e/ and /o/ rather than the /ɛ/
and /ɔ/ that NEL prefers, and /u/ rather than /ʊ/, since /u/ is
the standard phonemic value even if the phonetic realisation sits
a bit lower. Double vowels and consonants are length and geminates
in the usual way. The digraph tš is /t͡ʃ/ and ng before velars
is /ŋ/.

One spot where we deliberately part ways with NEL: /h/ before stops.
NEL renders `lehti` as [lɛxti], capturing a real Karelian allophonic
pattern, but we keep /h/ in all positions, matching the broad
approach and the way Finnish /h/ is handled elsewhere in the
database. Six items have parenthesised optional segments like
`sentäh(en)`; we include the parenthesised material in the IPA.


### Veps (338 items)

Unlike Karelian, the Veps data is not in standard orthography. It
uses a semi-phonetic notation with palatalization marks (the modifier
prime ʹ appears 38 times) and precomposed characters ś, ź, ń, ŕ.
Macron vowels mark length. The system sits closer to UPA than to
anything a Veps speaker would write.

Palatalization is systematic: ʹ after a consonant gives /Cʲ/, and
the precomposed letters work the same way. The vowel ü is /y/, not
/ʏ/, which is the standard phonemic inventory confirmed in published
descriptions. One difference from Karelian worth flagging: `ng`
in Veps is a geminate nasal /ŋː/, not /ŋɡ/. NEL confirms this
(`langeta` --> /lɑŋːetɑ/). Veps also maps /h/ to /x/ before stops,
unlike our treatment of Karelian; this is standard for Veps and
NEL agrees.

The bare letter `c` (two occurrences) is /ts/. One item has a
combining breve below on e (`okse̮ta`); we treated it as plain /e/
since the diacritic seems to be a notation artefact. After
normalizing all the known systematic differences, the NEL comparison
showed zero genuine mismatches.


### Estonian South / Võro (367 items)

The two features that set Võro orthography apart from Standard
Estonian are the letter `q` for the glottal stop /ʔ/ (16 occurrences,
always word-final, encoding a morphological feature) and the
apostrophe for palatalization (58 occurrences). These serve genuinely
different functions: `q` is the glottal stop, the apostrophe
palatalizes the consonant before it. We were careful not to
conflate them, so `maq` --> /mɑʔ/ but `suur'` --> /suːrʲ/.

The vowels follow the Standard Estonian conventions already in
UraLex: õ --> /ɤ/, ä --> /æ/, ö --> /ø/, ü --> /y/. The digraph `ts`
is a real affricate in Võro (not just a cluster), and the right
single quotation mark (two occurrences) is normalized to the
regular apostrophe. No NorthEuraLex cross-reference exists for Võro
specifically, since NEL only includes Standard Estonian, but the
conversions track the Standard Estonian IPA already in the database.


### Livonian Courland (353 items)

Livonian brought the richest orthographic inventory in the Finnic
group: macron vowels, cedilla consonants (ļ, ŗ, ņ, ḑ, ț), and a
handful of rare diacritics (ȯ, ȭ, ȱ, ǭ). Validation against 144
NEL matches gave 85.4% agreement after accounting for known
differences.

The most consequential finding here concerns the vowel **õ**.
Estonian-influenced descriptions and NorthEuraLex treat it as a
schwa /ə/, but Livonian-specific phonological work consistently
describes it as a high back unrounded vowel /ɯ/. We follow the
Livonian analysis, which also determines the long counterpart:
ȭ --> /ɯː/. Similarly, **ȯ** (o with dot above) is not /ʊ/ as NEL
has it but a mid back unrounded vowel /ɤ/, with ȱ --> /ɤː/. The
rare ǭ (one occurrence) maps to /ɒː/. The grave ì (six
occurrences) carries no phonemic weight and is just /i/.

The cedilla consonants follow the Latvian-influenced tradition:
ļ --> /ʎ/, ŗ --> /rʲ/, ņ --> /ɲ/, ḑ --> /ɟ/, ț --> /c/. The digraph
tš is /t͡ʃ/. Livonian has a broken tone (stod) that contrasts with
plain tone, but since the orthography does not mark it, neither
does the IPA.


### Saami languages

The six Saami varieties in UraLex range from the well-standardised
North Saami to the sparsely documented Pite and Ume Saami. They
share diphthong systems, consonant gradation, and quantity contrasts
of varying complexity, but differ in their orthographic encoding and,
critically, in whether the underlying stops should be analysed
as voiced or voiceless.

**North Saami (361 items).** The big question here is what to do
with b, d, g. Phonetically these are voiceless unaspirated stops,
and we map them to /p, t, k/ following Sammallahti (1998) and
Aikio & Ylikoski. So `buot` --> /puot/, `dákti` --> /tɑːkti/, and so
on. The orthography itself is otherwise fairly transparent, with á,
č, đ, ŋ, š, ž and the familiar diphthongs ea, uo, oa. The vowel á
is simply long /ɑː/; the diphthong ea maps to /eæ/, following both
NEL and standard descriptions. The modifier letter ˈ between
identical consonants marks a gemination boundary and is removed,
since the double-letter rules already produce the geminate. The
combining dot below (eight occurrences, always on e) is a
corpus-specific annotation and gets stripped. Double bb, dd, gg are
**pre-stopped** consonants (/pp, tt, kk/), not simple geminates,
which is an important distinction from the Finnic pattern. Sonorant
and fricative doubles (ll, nn, rr, ss, etc.) are regular geminates.
NEL match rates came out lower for North Saami (42.8%) than for
Finnic, mainly because NEL uses different citation forms (infinitives
ending in -h), a different pre-stopping notation (/dt/ where we
write /tt/), and considerably more phonetic detail.

**Inari Saami (351 items).** Three vowel letters need care here:
â, á, and ä. In modern pronunciation á and ä have merged, both
realized as /æ/, so the spelling distinction is orthographic rather
than phonemic. The circumflex â is a reduced central vowel: we use
/ə/ rather than the /ɐ/ that NEL prefers, following descriptions
that treat it as the mid member of the vowel system. After
normalizing this one difference, the NEL match rate hit 99.2%.
Inari Saami keeps its b, d, g voiced, unlike North Saami. Double
consonants are ordinary geminates, not pre-stopped. The digraph lj
is the palatal lateral /ʎ/, and bare c is the affricate /t͡s/.

**Skolt Saami (352 items).** Skolt has the most involved orthography
of any language in the database, centred on the modifier prime ʹ
(159 occurrences) and four consonant letters found nowhere else:
ǩ, ǧ, ǥ, ǯ. The prime palatalizes whatever consonant or cluster
follows the stressed-syllable vowel. When it precedes doubled
consonants, the result is a palatalized geminate: ʹ + CC --> /Cʲː/.
The special consonants map to ǩ --> /c/, ǧ --> /ɟ/, ǥ --> /ɣ/,
ǯ --> /d͡ʒ/. Vowels: â --> /ɐ/, õ --> /ə/, å --> /ɔ/, ä --> /æ/. Like
Inari Saami, Skolt has voiced stops. NEL match rates are lowest for
Skolt (25.8%), which is expected: the language's morphophonology
produces surface forms quite remote from the citation orthography.

**South Saami (386 items).** The interesting problem here is the
digraph ae. Some descriptions call it a long monophthong /aː/,
others a diphthong. Since we cannot reliably distinguish the two
from spelling alone (ae before j in `vaejsjie` is plainly
diphthongal; ae in `aelkedh` is traditionally described as long),
we went with /ɑe/ everywhere and flagged the caveat. The orthography
is otherwise comparatively simple: å (/ɔ/), ï (/ɨ/), ö (/ø/),
æ (/æ/), and the consonant digraphs sj --> /ɕ/ and tj --> /t͡ɕ/. The
voicing of b, d, g is genuinely debated. Published sources describe
them as "voiced or near-voiced unaspirated stops" while NEL devoices
them across the board. We kept them voiced, partly because South
Saami lacks consonant gradation entirely (unlike the western
varieties), which weakens the case for treating the "lenis" series
as underlyingly voiceless.

**Pite Saami (356 items).** Pite is among the least documented
Saami languages, and the converter leans on the assumption that it
patterns with other Western Saami varieties (supported by
Wilbur 2014). The orthography is North Saami-like: á (/ɑː/),
å (/ɔ/), ä (/æ/), ŋ. One item uses the Greek delta δ, treated as a
legacy variant of đ --> /ð/. Stops and pre-stopping follow North
Saami conventions. This is the least independently verified converter.

**Ume Saami (371 items).** What stands out in the Ume Saami
notation is the use of grave accents (à, è, ì, ò, ù) to mark short
vowels (47 + 28 + 10 + 7 + 6 occurrences) and the stress mark ˈ
(88 occurrences). The graves signal shortness as opposed to the
unmarked long variants; since short and long have the same quality
in a broad transcription, we simply strip the graves. The stress
mark is kept in the IPA, appearing between syllables (e.g.
`lüdˈnee` --> /lytˈneː/). This makes Ume Saami the only language in
the dataset with stress marking in the IPA; all other languages leave
stress unmarked. The placement follows the source notation, with the
stress mark after the coda of the first syllable rather than before
the onset of the second, which is non-standard IPA but faithfully
mirrors the original transcription. Like North and Pite Saami, b/d/g are
voiceless and bb/dd/gg are pre-stopped. The vowel ü is /y/, and ï
(four occurrences) is /i/, a morphophonemic spelling variant rather
than a separate phoneme.


### Hill Mari (333 items)

Hill Mari was one of the easier conversions because the `item` field
already uses semi-phonetic notation with IPA and UPA characters mixed
in: ə (238×), β (30×), δ (27×), ɣ (17×), χ (3×). This is not the
standard Hill Mari Cyrillic script but a Latinized phonological
transcription from the original UraLex compilation.

Most of the work is just normalizing Greek-letter conventions to
proper IPA: δ --> /ð/, χ --> /x/ (consistent with the Mansi `χ` --> `x`
decision above). The bilabial fricative β stays as /β/ since it is
valid IPA. The combining inverted breve above on ə (92×) is stripped,
following the convention already established for Meadow Mari, Komi,
and Udmurt. Fifteen items had UPA from the original data, which
served as a sanity check.


### Moksha (325 items)

Moksha notation mirrors what was used for Erzya (already handled by
the UPA pipeline): apostrophe for palatalization (77×),
precomposed ś, ŕ, ń, ć, ź, ĺ. The Greek chi χ (12×) maps to /x/
and the schwa ə stays put.

The one wrinkle was ć (c with acute), which under NFD decomposition
becomes c + combining acute. The preprocessor catches this and
converts it to c + ʹ, which then matches the palatalization rule
cʹ --> /t͡sʲ/. Moksha patterns so closely with Erzya that no
language-specific research was needed beyond confirming the notation
is the same.


### Tundra Nenets (308 items)

The degree sign ° (183 occurrences) shows up at the end of most
Nenets words, and it initially looked mysterious. Cross-referencing
with NorthEuraLex cleared things up: ° is a morphological stem-final
marker with no phonetic content. It flags the bare citation stem and
corresponds to an underlying glottal stop at the morpheme boundary,
but in the IPA it just gets dropped. Published Nenets grammars
(Salminen 1997, Nikolaeva 2014) confirm this analysis. The notation
itself is a Latinized phonological system, neither standard Cyrillic
nor UPA.

The letter y is the most complex part of the converter. After a
consonant it signals palatalization (ty --> /tʲ/, sy --> /sʲ/, my -->
/mʲ/, ny --> /ɲ/, cy --> /t͡sʲ/), but before a vowel or word-initially
it is simply /j/. The converter handles this in two passes: first
resolving Cy --> /Cʲ/, then mapping leftover y to /j/. NorthEuraLex
correspondences confirmed both directions.

A few other mappings: h is not /h/ but /ʔ/ (a glottal stop, same
as q); acute accents on í and ú mark stress, not vowel quality, and
get stripped; w is /w/.


### Proto-Uralic (138 items)

Proto-Uralic uses the standard Uralicist reconstruction notation:
asterisk for reconstructed forms, hyphen for morpheme boundaries,
question mark for uncertainty. All three are stripped.

The important vowel is i̮ (i + combining breve below, 34×), the
close central/back unrounded vowel, mapped to /ɨ/ in the usual way.
Palatalized consonants follow standard conventions: ś --> /sʲ/,
ć --> /t͡sʲ/, ń --> /ɲ/. The affricate č is /t͡ʃ/, the dental
fricative δ is /ð/, and the velar fricative ɣ is already valid IPA.
Items containing uppercase V (conventional placeholder for an
unknown vowel in the reconstruction) keep it as lowercase v, which
is not ideal but these forms are inherently uncertain anyway.


## Reverse UPA for four languages

Estonian Standard (349 items), Finnish Standard (338), Hungarian
(360), and Kildin Saami (321) all had IPA in the database but no
UPA. We generated UPA for them by reversing the IPA values, not by
running a separate transcription pipeline.

This is a lossy process in principle (the forward UPA-->IPA conversion
is not always one-to-one), but in practice the results are clean and
consistent. Length marks /ː/ expand to doubled letters, IPA vowels
map to their UPA counterparts (/ɑ/ --> a, /æ/ --> ä, /ɤ/ --> ə̑, /ø/ --> ö,
/y/ --> ü), and the rest is bookkeeping.

Finnish IPA had narrow phonetic diacritics (the lowered and dental
marks) that have no UPA equivalent; we strip those first. The
Finnish allophones /ɦ/ and /ç/ both map back to plain h; /ʋ/ maps
to v. For Hungarian, the main reversals are /ɒ/ --> a, /ɛ/ --> e,
/ʃ/ --> š, /ɲ/ --> ń, /ɟ/ --> ǵ, and recomposed affricates (/t͡ʃ/ --> č).
For Kildin Saami, /ʲ/ (148×) goes back to the modifier prime ʹ
and /ɨ/ to ə̑.

This UPA is **derived from IPA**, not transcribed independently by
the original compilers. It has not been validated against published
UPA sources for these languages and should be treated accordingly.

The reverse-conversion scripts are in `etc/ipa_conversion/reverse_upa/`.


## Segments

The Segments column was empty before this work. It is now filled for
all rows where the IPA is a simple single-word form without
alternatives. The approach differs between the two phases:

Phase 1 rows (4,162 from UPA conversion) get segments directly from
the UPA-to-IPA adapter, which returns a segment list as part of the conversion.
Another 1,432 rows (Finnish, Estonian, Hungarian, Kildin Saami) are
segmented by grouping base characters with their combining marks and
modifier letters.

Phase 2 rows get segments from the same grouping algorithm, applied
to the newly generated IPA. Rows with slashes, parenthetical
alternatives, or multi-word expressions are left without segments
rather than risk incorrect tokenization.

Format: space-separated IPA segments, e.g. `t ɯ l` or `s ɑː ŋ xʷ i`.


## Caveats

These conversions operate at the segmental level only. They do not
capture stress (except in Ume Saami, where the orthography marks it),
tone, the Livonian stod, quantity distinctions finer than short/long,
morphophonological alternations like Saami consonant gradation, or
predictable allophony. Each converter targets a single variety
(usually the standard or most widely described one); South Saami
vowels, in particular, get described inconsistently across sources,
and our choices reflect one reasonable analysis rather than the only
possible one.

None of the 14 newly transcribed languages were independently checked
by native speakers or by the scholars who originally compiled each
language's data. The transcriptions are best-effort broad phonemic
approximations meant for computational work and cross-linguistic
comparison, not authoritative phonetic records. Expert corrections
are welcome.

The conversion code is preserved in `etc/ipa_conversion/`, organized
by language family. Conversions were cross-checked against
NorthEuraLex (Dellert et al. 2020) wherever concept overlap existed.
