#!/usr/bin/env python3
import argparse
import datetime
import re
import shutil
import subprocess
import textwrap
import urllib.request
from pathlib import Path


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "recipe"


def download_image(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())


def copy_local_image(path: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        raise FileNotFoundError(f"Image path not found: {path}")
    shutil.copy2(path, dest)


def update_nav(title: str, slug: str) -> None:
    mkdocs = Path("mkdocs.yml")
    if not mkdocs.exists():
        raise FileNotFoundError("mkdocs.yml not found in repository root")
    lines = mkdocs.read_text().splitlines()
    entry = f'      - "{title}": {slug}.md'
    if entry in lines:
        return
    recipes_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "- Recipes:":
            recipes_idx = idx
            break
    if recipes_idx is None:
        raise ValueError("No '- Recipes:' block in mkdocs.yml nav")
    insert_idx = recipes_idx + 1
    while insert_idx < len(lines) and lines[insert_idx].startswith("      -"):
        insert_idx += 1
    lines.insert(insert_idx, entry)
    mkdocs.write_text("\n".join(lines) + "\n")


def render_markdown(args: argparse.Namespace, slug: str, image_ref: str | None) -> str:
    front_matter = ["---"]
    front_matter.append(f"title: {args.title}")
    front_matter.append(f"date: {args.date}")
    if args.tags:
        front_matter.append(f"tags: [{', '.join(args.tags)}]")
    if args.prep_time:
        front_matter.append(f"prep_time: {args.prep_time}")
    if args.total_time:
        front_matter.append(f"total_time: {args.total_time}")
    if args.servings:
        front_matter.append(f"servings: {args.servings}")
    if args.source_url:
        front_matter.append(f"source_url: {args.source_url}")
    if image_ref:
        front_matter.append(f"image: {image_ref}")
    front_matter.append("---\n")

    body = []
    if image_ref:
        body.append(f"![{args.image_alt}]({image_ref})\n")
    if args.description:
        body.append(args.description + "\n")
    if args.note:
        body.append(f"> **{args.note_title}**: {args.note}\n")
    if args.ingredients:
        body.append("#### Ingredients\n" + "\n".join(f"- {line}" for line in args.ingredients) + "\n")
    method_list = args.method or []
    if method_list:
        body.append("#### Method\n" + "\n".join(f"{idx}. {step}" for idx, step in enumerate(method_list, 1)) + "\n")
    if args.tip:
        body.append(f"> **Tip:** {args.tip}\n")
    if args.extra:
        body.append(args.extra + "\n")
    return "\n".join(front_matter + body)


def call_resize_script() -> None:
    subprocess.run(["python3", "scripts/resize_images.py"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new recipe page, copy its hero image, and update the navigation."
    )
    parser.add_argument("--title", required=True, help="Recipe title")
    parser.add_argument("--source-url", required=True, help="URL that will live in the source_url front matter")
    parser.add_argument("--date", default=datetime.date.today().isoformat(), help="Date for front matter (default: today)")
    parser.add_argument("--tags", nargs="*", default=[], help="List of tags (space separated)")
    parser.add_argument("--prep-time", help="Preparation time string")
    parser.add_argument("--total-time", help="Total time string")
    parser.add_argument("--servings", help="Servings count")
    parser.add_argument("--description", help="Intro paragraph describing the recipe")
    parser.add_argument("--note", help="Optional note to highlight after the intro (without formatting)")
    parser.add_argument("--note-title", default="Note", help="Header for the note (default: Note)")
    parser.add_argument("--image-path", type=Path, help="Local path to copy into recipes/assets/images")
    parser.add_argument("--image-url", help="Remote URL to download into recipes/assets/images")
    parser.add_argument("--image-alt", default="Recipe photo", help="Alt text for hero image")
    parser.add_argument("--ingredients", action="append", help="Ingredient line (can be passed multiple times)")
    parser.add_argument("--method", action="append", help="Method step (can be passed multiple times)")
    parser.add_argument("--tip", help="Optional tip or serving suggestion")
    parser.add_argument("--extra", help="Additional Markdown to append at the end")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing recipe file with the same slug")
    args = parser.parse_args()

    slug = slugify(args.title)
    recipe_dir = Path("recipes")
    recipe_file = recipe_dir / f"{slug}.md"
    if recipe_file.exists() and not args.force:
        raise SystemExit(f"Recipe file already exists: {recipe_file}. Use --force to replace it.")

    image_ref = None
    if args.image_path or args.image_url:
        dest = recipe_dir / "assets" / "images" / f"{slug}.jpg"
        if args.image_path:
            copy_local_image(args.image_path, dest)
        else:
            download_image(args.image_url, dest)
        image_ref = f"assets/images/{slug}.jpg"
        call_resize_script()
    markdown = render_markdown(args, slug, image_ref)
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_file.write_text(markdown, encoding="utf-8")

    update_nav(args.title, slug)

    print("Recipe scaffolded:", recipe_file)
    print(" - Hero image:", image_ref or "(none)")
    print(" - Navigation entry inserted into mkdocs.yml")
    print("Next steps: run 'python3 -m mkdocs build --strict', inspect, branch, commit, and open a PR.")


if __name__ == "__main__":
    main()
