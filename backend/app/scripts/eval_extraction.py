"""Accuracy test: run real policy documents through the same reading pipeline as the app and compare every
field with the correct answers a person wrote down.

    python -m app.scripts.eval_extraction <folder>              # run, print the report, save results-*.csv
    python -m app.scripts.eval_extraction <folder> --template   # write answers.csv with one row per file
    python -m app.scripts.eval_extraction <folder> --only motor --min-accuracy 0.95

The folder holds the policy files (PDF, JPG, PNG) and answers.csv. Keep it OUTSIDE the repo: these are real
people's policies. Each run calls the configured AI provider (AI_PROVIDER in .env), so it costs tokens.

answers.csv columns: file, then any of the fields below. A blank cell is not checked; "-" means the field must
come out empty (for example NCB on a policy with none). Extra columns are compared with the AI's detail fields
(registration_number, ncb_percentage, room_rent, ...).
"""

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.core.config import get_settings
from app.processing.extraction import is_not_a_policy, validate_extraction
from app.processing.text_extraction import ExtractionError, extract_text

CORE = ["policy_type", "insurer", "plan_name", "policy_number", "start_date", "end_date", "premium", "sum_insured",
        "payment_frequency"]  # fmt: skip
AMOUNT_FIELDS = {"premium", "sum_insured", "idv", "own_damage_premium", "third_party_premium", "compulsory_deductible"}
DATE_FIELDS = {"start_date", "end_date"}
LOOSE_FIELDS = {"insurer", "plan_name"}  # "TATA AIG" matches "Tata AIG General Insurance Company"
TYPES = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
EMPTY = "-"


@dataclass
class Check:
    file: str
    field: str
    expected: str
    got: str
    ok: bool
    confidence: float | None = None


@dataclass
class FileResult:
    file: str
    error: str | None = None
    checks: list[Check] = field(default_factory=list)


def _words(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _amount(value: Any) -> Decimal | None:
    text = str(value).lower().replace(",", "").replace("rs.", "").replace("rs", "").replace("₹", "").strip()
    unit = 100_000 if "lakh" in text or "lac" in text else 10_000_000 if "cr" in text else 1
    number = re.search(r"\d+(\.\d+)?", text)
    if not number:
        return None
    try:
        return Decimal(number.group()) * unit
    except InvalidOperation:
        return None


def _date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def matches(field_name: str, expected: str, got: Any) -> bool:
    """Whether the pipeline's value counts as correct for what a person wrote in answers.csv."""
    got_empty = got is None or str(got).strip() == ""
    if expected == EMPTY:
        return got_empty
    if got_empty:
        return False
    if field_name in AMOUNT_FIELDS or field_name.endswith("_premium"):
        a, b = _amount(expected), _amount(got)
        return a is not None and b is not None and abs(a - b) <= 1
    if field_name in DATE_FIELDS:
        a, b = _date(expected), _date(got)
        return a is not None and a == b
    if field_name == "policy_number":
        return re.sub(r"[^A-Za-z0-9]", "", expected).upper() == re.sub(r"[^A-Za-z0-9]", "", str(got)).upper()
    e, g = _words(expected), _words(str(got))
    if field_name in LOOSE_FIELDS or field_name not in CORE:
        return bool(e) and (e in g or g in e)
    return e == g


def read_answers(folder: Path) -> list[dict[str, str]]:
    path = folder / "answers.csv"
    if not path.exists():
        sys.exit(f"No answers.csv in {folder}. Create one with --template.")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def write_template(folder: Path) -> Path:
    files = sorted(p.name for p in folder.iterdir() if p.suffix.lower() in TYPES)
    path = folder / "answers.csv"
    if path.exists():
        sys.exit(f"{path} already exists; not overwriting it.")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", *CORE, "registration_number", "ncb_percentage"])
        for name in files:
            writer.writerow([name] + [""] * (len(CORE) + 2))
    return path


def run_file(path: Path, answers: dict[str, str]) -> FileResult:
    result = FileResult(path.name)
    try:
        extracted = extract_text(path.read_bytes(), TYPES[path.suffix.lower()])
        raw = get_ai_gateway().extract_policy(extracted.full_text)
        if is_not_a_policy(raw, extracted.full_text):
            raise ExtractionError("not_a_policy")
        validated = validate_extraction(raw, extracted.full_text)
    except (ExtractionError, AIProviderError) as exc:
        result.error = getattr(exc, "code", None) or str(exc)
        return result
    found = {"policy_type": validated.policy_type, **validated.values, **validated.details}
    for name, expected in answers.items():
        if name == "file" or not expected:
            continue
        got = found.get(name)
        result.checks.append(
            Check(
                path.name,
                name,
                expected,
                "" if got is None else str(got),
                matches(name, expected, got),
                validated.confidence.get(name),
            )  # fmt: skip
        )
    return result


def report(results: list[FileResult]) -> tuple[str, float]:
    checks = [c for r in results for c in r.checks]
    lines = []
    for r in results:
        if r.error:
            lines.append(f"✗ {r.file}: FAILED TO READ ({r.error})")
            continue
        right = sum(c.ok for c in r.checks)
        lines.append(f"{'✓' if right == len(r.checks) else '•'} {r.file}: {right}/{len(r.checks)} fields right")
        for c in r.checks:
            if not c.ok:
                conf = "" if c.confidence is None else f"  (AI confidence {c.confidence:.2f})"
                lines.append(f"    {c.field}: expected {c.expected!r}, got {c.got or '(empty)'!r}{conf}")
    by_field: dict[str, list[Check]] = {}
    for c in checks:
        by_field.setdefault(c.field, []).append(c)
    lines.append("")
    lines.append("By field:")
    for name, cs in sorted(by_field.items(), key=lambda kv: sum(c.ok for c in kv[1]) / len(kv[1])):
        lines.append(f"  {name:<22} {sum(c.ok for c in cs)}/{len(cs)}")
    failed = sum(1 for r in results if r.error)
    accuracy = sum(c.ok for c in checks) / len(checks) if checks else 0.0
    lines.append("")
    lines.append(
        f"Overall: {sum(c.ok for c in checks)}/{len(checks)} fields right ({accuracy:.0%}) across "
        f"{len(results)} documents; {failed} could not be read."
    )
    return "\n".join(lines), accuracy


def save_csv(folder: Path, results: list[FileResult]) -> Path:
    path = folder / f"results-{datetime.now():%Y%m%d-%H%M}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "field", "expected", "got", "correct", "ai_confidence", "error"])
        for r in results:
            if r.error:
                writer.writerow([r.file, "", "", "", "", "", r.error])
            for c in r.checks:
                writer.writerow([c.file, c.field, c.expected, c.got, "yes" if c.ok else "NO", c.confidence or "", ""])
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--template", action="store_true", help="write answers.csv for the files in the folder")
    parser.add_argument("--only", help="only rows whose policy_type is this (health, motor, life, other)")
    parser.add_argument("--min-accuracy", type=float, default=0.0, help="exit with an error below this (0-1)")
    args = parser.parse_args(argv)
    folder: Path = args.folder.expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f"{folder} is not a folder")
    if args.template:
        print(f"Wrote {write_template(folder)}. Fill in the correct values from each document, then run again.")
        return 0

    rows = read_answers(folder)
    if args.only:
        rows = [r for r in rows if r.get("policy_type", "").lower() == args.only.lower()]
    print(f"Reading {len(rows)} documents with AI_PROVIDER={get_settings().ai_provider} …", flush=True)
    results = []
    for row in rows:
        path = folder / row.get("file", "")
        if not path.is_file() or path.suffix.lower() not in TYPES:
            results.append(FileResult(row.get("file", "?"), error="file not found or not PDF/JPG/PNG"))
            continue
        print(f"  {path.name}", flush=True)
        results.append(run_file(path, row))
    text, accuracy = report(results)
    print()
    print(text)
    print(f"\nDetails saved to {save_csv(folder, results)}")
    return 1 if accuracy < args.min_accuracy else 0


if __name__ == "__main__":
    raise SystemExit(main())
