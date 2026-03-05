# IPTC Genre CSV + XLSX (Derived Convenience Export)

**Date Parsed**: 2026-03-06

## Overview
CSV and Excel of the IPTC NewsCodes Genre vocabulary, generated from IPTC's Controlled Vocabulary (CV) server located at http://cv.iptc.org/newscodes/JSON-LD.

## Why this exists
We wanted to review IPTC’s Genre vocabulary quickly in a spreadsheet, but IPTC publishes it as RDF/XML, RDF/Turtle, or JSON-LD.
This repo provides CSV/XLSX exports (and a small converter script) so you can inspect, filter, and integrate the vocabulary without writing your own parser.

## Source of truth
- Authoritative vocabulary: https://cv.iptc.org/newscodes/genre/
- Machine-readable endpoint used by the script: `https://cv.iptc.org/newscodes/genre/?format=jsonld`
- This repository's CSV/XLSX files are derived convenience formats. The authoritative source remains IPTC's CV server.

## License / Attribution
- IPTC NewsCodes are licensed under Creative Commons Attribution 4.0 (CC BY 4.0).
- License text: https://creativecommons.org/licenses/by/4.0/
- Credit: IPTC NewsCodes / IPTC.

This repository republishes derived tabular exports for convenience. It is not an official IPTC distribution.

## Data schema
The generated CSV and XLSX share identical columns and order:

1. `Genre-URI`: Concept URI from `conceptSet[].uri`
2. `Genre-QCode (flat)`: Flat code derived from `conceptSet[].qcode` (text after `:`)
3. `Name (en-US)`: Preferred label with language fallback `en-US -> en-GB -> first available`
4. `Definition (en-US)`: Definition with language fallback `en-US -> en-GB -> first available`
5. `created`: `conceptSet[].created`
6. `modified`: `conceptSet[].modified`
7. `Type`: Flattened concept type(s)
8. `Genre-QCode (full)`: Original `conceptSet[].qcode` value
9. `Name (en-GB)`: Raw `en-GB` preferred label when present
10. `Definition (en-GB)`: Raw `en-GB` definition when present
11. `Note (en-US)`: `note` with language fallback
12. `Note (en-GB)`: Raw `note.en-GB` when present
13. `Change-Note (en-US)`: `changeNote` with language fallback
14. `Change-Note (en-GB)`: Raw `changeNote.en-GB` when present
15. `retired`: Retirement timestamp when present
16. `Scheme-URI`: Scheme URI from `inScheme` (fallback to top-level scheme URI)

## How to regenerate
Run from repository root:

```bash
python convert_json_ld_to_csv.py --out_csv data/iptc_genre.csv --out_xlsx data/iptc_genre.xlsx
```

Expected outputs:
- `data/iptc_genre.csv`
- `data/iptc_genre.xlsx`

## Dependency notes
- Python standard library for fetching/parsing/writing CSV.
- `openpyxl` for XLSX output.

Install dependency if needed:

```bash
pip install openpyxl
```

## Change management
If IPTC updates the Genre vocabulary, rerun the script and commit the refreshed `data/` artifacts.
