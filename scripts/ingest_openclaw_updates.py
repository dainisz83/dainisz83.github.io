#!/usr/bin/env python3
"""Sanitize OpenClaw recipe payloads before writing Markdown drafts.

This script enforces the repository schema (data/schema.json) and applies
additional sanitization to reduce the risk of unwanted outbound content
(lethal-trifecta guard): only allow a strict set of metadata fields, strip
links/HTML, normalize whitespace, and refuse unsafe slugs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"
DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "data" / "openclaw_updates.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "recipes"

ALLOWED_META_FIELDS = {
    "title",
    "date",
    "tags",
    "prep_time",
    "cook_time",
    "serves",
    "image",
    "summary",
    "source",
}

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
HTML_RE = re.compile(r"<[^>]+>")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
WHITESPACE_RE = re.compile(r"\s+")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text.strip())


def sanitize_text(text: str) -> str:
    text = HTML_RE.sub("", text)
    text = MD_LINK_RE.sub(r"\\1", text)
    text = URL_RE.sub("", text)
    text = normalize_whitespace(text)
    return text


def sanitize_list(items: list[str]) -> list[str]:
    cleaned = []
    for item in items:
        item = sanitize_text(item)
        if item:
            cleaned.append(item)
    return cleaned


def validate_schema(payload: dict, schema: dict) -> list[str]:
    """Lightweight schema checks without external dependencies."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be an object"]
    if "recipes" not in payload or not isinstance(payload["recipes"], list) or not payload["recipes"]:
        errors.append("payload.recipes must be a non-empty list")
        return errors

    for idx, recipe in enumerate(payload["recipes"]):
        if not isinstance(recipe, dict):
            errors.append(f"recipes[{idx}] must be an object")
            continue
        required = schema["properties"]["recipes"]["items"]["required"]
        for key in required:
            if key not in recipe:
                errors.append(f"recipes[{idx}] missing required field: {key}")
        if "slug" in recipe and not SLUG_RE.match(recipe["slug"]):
            errors.append(f"recipes[{idx}] slug is invalid")
        if "date" in recipe and not DATE_RE.match(recipe["date"]):
            errors.append(f"recipes[{idx}] date must be YYYY-MM-DD")
    return errors


def sanitize_recipe(recipe: dict) -> dict:
    title = sanitize_text(recipe.get("title", ""))
    slug = recipe.get("slug", "")
    if not SLUG_RE.match(slug):
        slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
    if not slug:
        raise ValueError("Could not derive a valid slug")

    date = recipe.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
    if not DATE_RE.match(date):
        raise ValueError("Invalid date format")

    summary = sanitize_text(recipe.get("summary", ""))
    tags = sanitize_list(recipe.get("tags", []))
    tags = [t.lower() for t in tags]

    image = sanitize_text(recipe.get("image", ""))
    if image and not (image.startswith("assets/") or image.startswith("https://")):
        image = ""

    meta = {
        "title": title,
        "date": date,
        "summary": summary,
        "tags": tags,
        "prep_time": sanitize_text(recipe.get("prep_time", "")),
        "cook_time": sanitize_text(recipe.get("cook_time", "")),
        "serves": sanitize_text(recipe.get("serves", "")),
        "image": image,
        "source": sanitize_text(recipe.get("source", "")),
    }
    meta = {k: v for k, v in meta.items() if k in ALLOWED_META_FIELDS and v}

    ingredients = sanitize_list(recipe.get("ingredients", []))
    steps = sanitize_list(recipe.get("steps", []))
    notes = sanitize_list(recipe.get("notes", []))

    if not ingredients or not steps:
        raise ValueError("Ingredients and steps must be non-empty after sanitization")

    return {
        "slug": slug,
        "meta": meta,
        "ingredients": ingredients,
        "steps": steps,
        "notes": notes,
    }


def format_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("draft: true")
    lines.append("---")
    return "\n".join(lines)


def write_markdown(output_dir: Path, recipe: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{recipe['slug']}.md"

    frontmatter = format_frontmatter(recipe["meta"])
    lines = [frontmatter, "", "## Ingredients", ""]
    lines += [f"- {item}" for item in recipe["ingredients"]]
    lines += ["", "## Steps", ""]
    lines += [f"{idx + 1}. {step}" for idx, step in enumerate(recipe["steps"]) ]
    if recipe["notes"]:
        lines += ["", "## Notes", ""]
        lines += [f"- {note}" for note in recipe["notes"]]

    target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize OpenClaw recipe payloads")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    schema = load_schema()
    payload = load_payload(args.input)
    errors = validate_schema(payload, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    written = []
    for recipe in payload["recipes"]:
        try:
            sanitized = sanitize_recipe(recipe)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        if args.dry_run:
            print(f"DRY RUN: would write {sanitized['slug']}.md")
            continue

        target = write_markdown(args.output, sanitized)
        written.append(target)

    if written:
        print("Wrote drafts:")
        for path in written:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
