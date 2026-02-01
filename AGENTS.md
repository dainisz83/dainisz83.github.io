# AGENTS.md

## Purpose

This repo allows AI assistants to draft recipe content and metadata, but **human review is mandatory** before anything is published.

## Autonomy & review policy

Agents may:
- Generate drafts under `recipes/` using the ingest script.
- Propose edits via PRs.
- Update supporting assets in `assets/images/`.

Agents must **not**:
- Publish directly to the live site.
- Add outbound links or claims without human verification.
- Bypass schema/metadata sanitation.

## Required workflow

1. Use `scripts/ingest_openclaw_updates.py` to sanitize incoming payloads (see `data/schema.json`).
2. Open a PR with the draft changes.
3. Complete the outbound check in the PR template (lethal-trifecta guard).
4. Human reviewer approves before merge.

## AI disclosure

If AI assistance was used (openai-codex/gpt-5.2), note it in the PR description and confirm manual verification of all outbound text.
