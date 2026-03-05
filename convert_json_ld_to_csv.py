#!/usr/bin/env python3
"""
Generate developer-friendly CSV and Excel files for IPTC Genre NewsCodes.

Why this exists:
We wanted to review IPTC’s Genre vocabulary quickly in a spreadsheet, but IPTC publishes it primarily as JSON-LD.
This repo provides CSV/XLSX exports (and a small converter script) so you can inspect, filter, and integrate the vocabulary without writing your own parser.

Input source:
- Human-facing scheme page: https://cv.iptc.org/newscodes/genre/
- Machine-readable source used by this script:
  https://cv.iptc.org/newscodes/genre/?format=jsonld
The script accepts a page URL via `--source` and resolves it to JSON-LD by
adding `format=jsonld` when needed.

Output files (defaults):
- data/iptc_genre.csv
- data/iptc_genre.xlsx (worksheet: "Genre")

Output columns:
- Genre-URI
- Genre-QCode (flat)
- Name (en-US)
- Definition (en-US)
- created
- modified
- Type
- Genre-QCode (full)
- Name (en-GB)
- Definition (en-GB)
- Note (en-US)
- Note (en-GB)
- Change-Note (en-US)
- Change-Note (en-GB)
- retired
- Scheme-URI

Field mapping rules:
- `Genre-QCode (flat)` is derived from `qcode` by removing the prefix before
  the first colon (e.g., "genre:Actuality" -> "Actuality").
- `Name (en-US)` and `Definition (en-US)` prefer `en-US`; if unavailable, they
  fall back to `en-GB`, then any available language value.
- `Name (en-GB)` and `Definition (en-GB)` preserve the source's en-GB text.
- Notes and change notes use the same language fallback logic for en-US columns.
- `Type` flattens single or multi-valued type fields into a deterministic
  pipe-separated string.

How to run:
python convert_json_ld_to_csv.py \
  --out_csv data/iptc_genre.csv \
  --out_xlsx data/iptc_genre.xlsx

Determinism:
- Rows are sorted by `Genre-QCode (flat)` and then `Genre-URI`.
- Column order is fixed in code.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import urlopen

DEFAULT_SOURCE = "https://cv.iptc.org/newscodes/genre/"
DEFAULT_OUT_CSV = Path("data/iptc_genre.csv")
DEFAULT_OUT_XLSX = Path("data/iptc_genre.xlsx")
DEFAULT_TIMEOUT = 30

COLUMNS = [
    "Genre-URI",
    "Genre-QCode (flat)",
    "Name (en-US)",
    "Definition (en-US)",
    "created",
    "modified",
    "Type",
    "Genre-QCode (full)",
    "Name (en-GB)",
    "Definition (en-GB)",
    "Note (en-US)",
    "Note (en-GB)",
    "Change-Note (en-US)",
    "Change-Note (en-GB)",
    "retired",
    "Scheme-URI",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert IPTC Genre JSON-LD into CSV and XLSX outputs."
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="IPTC Genre source page URL or a local JSON/JSON-LD file path.",
    )
    parser.add_argument(
        "--out_csv",
        type=Path,
        default=DEFAULT_OUT_CSV,
        help=f"Output CSV path (default: {DEFAULT_OUT_CSV}).",
    )
    parser.add_argument(
        "--out_xlsx",
        type=Path,
        default=DEFAULT_OUT_XLSX,
        help=f"Output XLSX path (default: {DEFAULT_OUT_XLSX}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    return parser.parse_args()


def source_to_jsonld_url(source: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"}:
        return source

    query = parse_qs(parsed.query, keep_blank_values=True)
    if "format" not in query:
        query["format"] = ["jsonld"]

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def load_jsonld(source: str, timeout: int) -> dict[str, Any]:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        url = source_to_jsonld_url(source)
        with urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("JSON-LD payload is not a JSON object.")
        return data

    path = Path(source)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Local JSON-LD file is not a JSON object.")
    return data


def get_lang_value(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        raw = value.get(lang)
        return str(raw) if raw is not None else ""
    return ""


def preferred_lang_value(value: Any, preferred_langs: list[str]) -> str:
    if not isinstance(value, dict):
        return ""

    for lang in preferred_langs:
        raw = value.get(lang)
        if raw:
            return str(raw)

    # Final fallback keeps useful text even if language tags change upstream.
    for raw in value.values():
        if raw:
            return str(raw)
    return ""


def normalize_type(value: Any) -> str:
    if isinstance(value, list):
        items = sorted({str(item) for item in value if item is not None})
        return " | ".join(items)
    if value is None:
        return ""
    return str(value)


def to_flat_qcode(qcode: str, uri: str) -> str:
    # IPTC qcodes are typically namespaced (e.g., "genre:Actuality").
    if qcode and ":" in qcode:
        return qcode.split(":", 1)[1]
    if qcode:
        return qcode
    if uri:
        return uri.rstrip("/").rsplit("/", 1)[-1]
    return ""


def concept_to_row(concept: dict[str, Any], scheme_uri: str) -> dict[str, str]:
    uri = str(concept.get("uri", ""))
    qcode_full = str(concept.get("qcode", ""))

    # Language selection: en-US first, then en-GB fallback.
    label = concept.get("prefLabel", {})
    definition = concept.get("definition", {})
    note = concept.get("note", {})
    change_note = concept.get("changeNote", {})

    in_scheme = concept.get("inScheme")
    if isinstance(in_scheme, list) and in_scheme:
        concept_scheme_uri = str(in_scheme[0])
    elif isinstance(in_scheme, str):
        concept_scheme_uri = in_scheme
    else:
        concept_scheme_uri = scheme_uri

    return {
        "Genre-URI": uri,
        "Genre-QCode (flat)": to_flat_qcode(qcode_full, uri),
        "Name (en-US)": preferred_lang_value(label, ["en-US", "en-GB"]),
        "Definition (en-US)": preferred_lang_value(definition, ["en-US", "en-GB"]),
        "created": str(concept.get("created", "")),
        "modified": str(concept.get("modified", "")),
        "Type": normalize_type(concept.get("type")),
        "Genre-QCode (full)": qcode_full,
        "Name (en-GB)": get_lang_value(label, "en-GB"),
        "Definition (en-GB)": get_lang_value(definition, "en-GB"),
        "Note (en-US)": preferred_lang_value(note, ["en-US", "en-GB"]),
        "Note (en-GB)": get_lang_value(note, "en-GB"),
        "Change-Note (en-US)": preferred_lang_value(change_note, ["en-US", "en-GB"]),
        "Change-Note (en-GB)": get_lang_value(change_note, "en-GB"),
        "retired": str(concept.get("retired", "")),
        "Scheme-URI": concept_scheme_uri,
    }


def extract_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    concept_set = data.get("conceptSet")
    if not isinstance(concept_set, list):
        raise ValueError("JSON-LD does not include a list-valued 'conceptSet'.")

    scheme_uri = str(data.get("uri", ""))
    rows = [concept_to_row(concept, scheme_uri) for concept in concept_set]
    rows.sort(key=lambda row: (row["Genre-QCode (flat)"], row["Genre-URI"]))
    return rows


def write_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(rows: list[dict[str, str]], out_xlsx: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is required to write XLSX. Install it with 'pip install openpyxl'."
        ) from exc

    out_xlsx.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Genre"
    ws.freeze_panes = "A2"

    ws.append(COLUMNS)
    for row in rows:
        ws.append([row.get(column, "") for column in COLUMNS])

    wb.save(out_xlsx)


def main() -> None:
    args = parse_args()
    data = load_jsonld(args.source, args.timeout)
    rows = extract_rows(data)
    write_csv(rows, args.out_csv)
    write_xlsx(rows, args.out_xlsx)
    print(f"Wrote {len(rows)} rows to {args.out_csv} and {args.out_xlsx}")


if __name__ == "__main__":
    main()
