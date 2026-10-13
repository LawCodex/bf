# Burkina Faso (BF) — législation en Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Constitution, codes and laws of Burkina Faso, in **French** (official language), from two official sources:

1. the **Assemblée législative de Transition / Assemblée nationale** website (https://www.assembleenationale.bf,
   "Lois promulguées"): 269 promulgated laws (2018–2024), each with its PDF;
2. the former official legal portal **LegiBurkina** (www.legiburkina.bf, Secrétariat général du Gouvernement et
   du Conseil des ministres), no longer online, via **Internet Archive captures**: the Constitution (text as amended
   up to 2012), codes, and laws published there (mostly 1994–2016).

Texts are as enacted / as published at the time (not consolidated).

Retrieved 2026-10-13.

<!-- COUNTS -->
| Directory | Files |
|---|---|
| `codes/` | 10 |
| `codes/legiburkina-htm/` | 7 |
| `constitution/` | 3 |
| `lois-constitutionnelles/` | 2 |
| `lois-organiques/` | 6 |
| `lois/` | 351 |
| **Total** | **379** |
<!-- /COUNTS -->

## Structure

```
constitution/constitution-1991-version-2012.md   Constitution of 2 June 1991 as amended up to 2012 (LegiBurkina PDF)
constitution/constitution*-htm.md                older HTML versions of the Constitution (LegiBurkina)
lois-constitutionnelles/<year>/...                constitutional laws (Assemblée)
lois-organiques/<year>/loi-<nnn>-<year>-<alt|an>.md
lois/<year>/loi-<nnn>-<year>-<alt|an|cnt>.md       laws (Assemblée: 2018–2024; LegiBurkina: 1994–2016)
codes/<name>.md                                   codes (LegiBurkina PDFs: civil, pénal, travail, foncier, minier, impôts…)
codes/legiburkina-htm/<name>.md                   codes / compilations published as HTML pages by LegiBurkina
```

Front matter: `identifier` = law number (e.g. `Loi n° 042-2024/ALT`), `date` = date of the law, `source` = PDF or
page URL, `record` = Assemblée page of the law, `archived_source` = Internet Archive capture (LegiBurkina texts),
`status: unknown`. When a law exists in both sources, the Assemblée version is kept.

Headings: LIVRE / TITRE / CHAPITRE / SECTION → `##`…; articles → headings. Most Assemblée PDFs are scans; their text
was produced by OCR (tesseract, French; `note: … OCR`) and contains recognition errors.

## Constitutional situation (factual)

The Constitution of 2 June 1991 has been amended many times (1997, 2000, 2002, 2009, 2012, 2015). After the military
takeovers of January and September 2022, a *Charte de la Transition* (14 October 2022, revised on 25 May 2024)
governs the transitional institutions alongside the Constitution. The Assemblée législative de Transition adopted
constitutional revisions in December 2023 (loi n° 045-2023/ALT) and October 2024 (loi constitutionnelle
n° 033-2024/ALT); these are included as published by the Assemblée. The Charte de la Transition itself, and an
official consolidated text of the Constitution after 2012, were not found on an accessible official site and are
**not included**.

## Sources

| Source | URL |
|---|---|
| Assemblée nationale / ALT — Lois promulguées | https://www.assembleenationale.bf/loip (pages `/loip/<id>`, PDFs `/storage/Loi/…`) |
| LegiBurkina (archived) | http://www.legiburkina.bf/ → https://web.archive.org/web/*/legiburkina.bf/* |

The Government's coordinated websites (`*.gov.bf`, e.g. the Conseil constitutionnel site) carry general terms of use
forbidding reproduction of their content without authorisation of the Service d'information du Gouvernement; no text
was taken from those sites. The Assemblée website states no such terms.

## Not covered / known gaps

* Laws before 2013 that were not captured from LegiBurkina; laws whose Assemblée page has no PDF (reported as
  `NOPDF` by the script, e.g. several ratification laws).
* Codes from LegiBurkina reflect the versions online at capture time and may be outdated (e.g. the Code pénal was
  replaced in 2018 by loi n° 025-2018/AN).
* Decrees, ordinances and the Journal officiel are not included (the JO site and the SGG site are not reachable;
  LegiBurkina's JO pages were mostly decrees and notices).

## Copyright

Official texts of Burkina Faso. The Markdown conversion is provided as is; the authoritative text is the one
published in the Journal officiel du Burkina Faso.

## Regenerating

```sh
python3 scripts/bf_fetch.py --download-only        # Assemblée laws -> ../_raw/bf/
python3 scripts/bf_fetch.py --no-download --jobs 3 # OCR in parallel, then Markdown
python3 scripts/bf_legi.py                         # LegiBurkina texts via the Internet Archive (run after bf_fetch)
python3 scripts/bf_readme.py                       # counts table
```
