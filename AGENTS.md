# AGENTS.md

Guidance for the standalone `volcengine-audio` SDK, including when checked out
as a dispatcher submodule. Run commands below from this package root. Keep
submodule changes distinct from parent-repository changes.

## Boundaries

- Preserve `requires-python >=3.10`; the parent dispatcher's Python target
  does not change this standalone package contract. Check `pyproject.toml`
  for current dependencies/build settings.
- Keep `src/volcengine_audio` standalone; do not import dispatcher modules.
- Preserve user-owned staged, unstaged, and untracked work. Do not commit, push,
  publish, or change a parent gitlink unless requested.
- Never SSH to hosts unless explicitly requested (git SSH to GitHub/GitLab is
  allowed). Keep secrets and temporary scrape artifacts out of tracked files.

## Code and tests

- STT, TTS, and realtime models/helpers live in `stt.py`, `tts.py`, and
  `realtime.py`; shared protocol/event constants belong in `protocol.py`.
  Update `__init__.py` for changed public exports.
- Use `orjson`, modern typing compatible with the package's Python floor,
  typed parameters/returns, and concise docstrings for added functions/APIs.
- Keep imports at top unless lazy loading is needed. Log with interpolation;
  never log credentials or signed URLs. Add helpers only for reuse or clarity.
- Follow Ruff: 2 spaces, 80 columns, single quotes.
- Tests live in `tests/`. Add regression coverage for schema, enum, protocol,
  or helper changes; prefer exact payload assertions and cover both generation
  and parsing when protocol behavior changes.
- Realtime TTS sentence events have their own response models with
  `question_id` and `reply_id`; do not reuse standalone TTS V3 event models.
  Keep speaker fields open strings rather than freezing the voice catalog.

```bash
uv sync --frozen --group dev
uv run pytest tests
uv run ruff check src tests
uv run ruff format --check src tests
```

Run focused tests first, then the package suite for SDK changes. Check standalone
buildability when packaging or the public SDK surface changes. For docs-only
edits, validate metadata/links and run `git diff --check`.

## Documentation maintenance

Use `doc_sync/volcengine/manifest.json` and its tracked snapshots as the first
source for SDK maintenance. Current timestamps and sync history belong in the
manifest and `README.md`/`README.zh-CN.md`, not duplicated here.

Use [.agents/skills/volcengine-audio-doc-sync/SKILL.md](.agents/skills/volcengine-audio-doc-sync/SKILL.md)
for snapshot refresh or SDK/doc reconciliation. A README or AGENTS-only update
against existing snapshots does not authorize a network refresh or SDK changes.

Update both README languages for material user-facing behavior changes. Keep
snapshot content as cleaned `Result.Content` text, source metadata/hashes in
the manifest, and raw JSON responses out of git. Snapshots are repo maintenance
artifacts, not wheel contents. Fetch all documents successfully before replacing
existing snapshots.
