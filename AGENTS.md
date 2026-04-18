# AGENTS.md

This repository uses **`CLAUDE.md`** as its single source of truth for AI agent instructions.

**→ Read `CLAUDE.md` in full before doing anything else.**

All routing, rules, workflows, ADR process, and diagram-update requirements live there. Do not treat this file as a summary — it is only a pointer. The substantive content is in `CLAUDE.md`.

## Why this file exists

Different AI coding tools look for different filenames at the repo root:
- Claude Code, Claude.ai, Cursor → `CLAUDE.md`
- OpenAI Codex CLI, Aider, some Cursor configs, Windsurf → `AGENTS.md`
- GitHub Copilot → `.github/copilot-instructions.md` (if added later)

This file ensures tools looking for `AGENTS.md` are redirected to the canonical instructions in `CLAUDE.md` rather than operating without context.

## If you are an AI agent reading this

1. Open `CLAUDE.md` at the repo root.
2. Read it end to end — especially §1 (Stop), §3 (Decision Tree), §5 (Non-Negotiable Rules), §7 (ADR Process), and §8 (Diagram Update Process).
3. Then proceed with the user's task, following the routing in `CLAUDE.md`.

Do not attempt work on CiteGuard without reading `CLAUDE.md` first. The three non-negotiables — privileged data handling, audit log integrity, and tenant isolation — are defined there, and violating any of them causes real legal and compliance harm to customers.

## If you are a human editing this file

Keep this file short. Do not duplicate content from `CLAUDE.md` here — duplicated rules drift apart and become contradictory. If you need to change agent behavior, edit `CLAUDE.md`.