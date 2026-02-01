# Security Policy

## Overview

This cookbook accepts draft content from automation (OpenClaw + GitHub Actions) but **never publishes automatically**. The workflow is designed for heightened permissions (agents can draft, parse, and format), while final publication is gated by human review.

## Lethal-trifecta guard

To prevent unsafe outbound content, we apply a lethal-trifecta guard:
- **Sanitize metadata** (strip HTML/links, drop unknown fields, normalize text).
- **Review outbound text** for hidden links or fabricated claims.
- **Require a human** to approve every publish.

The ingest pipeline enforces schema checks (`data/schema.json`) and sanitation before writing draft Markdown. It is safe to re-run; it only writes drafts under `recipes/`.

## AI assistance

When AI assists drafts (openai-codex/gpt-5.2), the PR must mention the model and confirm a full human review. AI does not auto-merge, auto-publish, or bypass the outbound check.

## Reporting

If you spot a vulnerability or unintended outbound behavior, open a GitHub issue or PR with details. We’ll patch quickly and update this policy.
