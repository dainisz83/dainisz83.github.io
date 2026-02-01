# Dining with Dainis & Izabela

This repo drives an MkDocs/Material-powered cookbook. Every recipe lives under `recipes/` as Markdown with a small frontmatter block (`title`, `date`, `tags`, `prep_time`, `image`, etc.), so the site at `https://dainisz83.github.io/` renders a polished hero/recipe layout just like the Squidfunk demo.

## Security & permissions story

We use heightened permissions for automation (OpenClaw + GitHub Actions) so a trusted agent can gather drafts and prepare PRs, but **never publish directly**. Drafts are always reviewed by a human before merge. Outbound text is guarded by a lethal-trifecta check: only sanitized metadata and reviewed content can leave the workspace. When AI assistance is used (openai-codex/gpt-5.2), we record it in the PR and re-check for hidden links or fabricated claims.

See `SECURITY.md` and `AGENTS.md` for the full review/autonomy policy.

## Local preview

```bash
pip install mkdocs-material
mkdocs serve --dev-addr 127.0.0.1:8000
```

## Adding a recipe

1. Drop the structured Markdown file in `recipes/`.
2. Store supporting images under `assets/images/` (or point to a trusted remote URL).
3. Commit the draft, open a PR, and merge once you’re happy—they’ll appear in the nav automatically.

## Automations

We can feed WhatsApp photos + recipe URLs into this folder and generate PRs so you can review before anything goes live. The ingest workflow (`.github/workflows/ingest.yml`) runs `scripts/ingest_openclaw_updates.py`, which sanitizes metadata against `data/schema.json` before writing draft Markdown to `recipes/`.

---

Continue to use this README for notes, but the recipe data lives in `recipes/` now.
# test
# test
