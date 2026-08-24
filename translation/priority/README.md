# Live gameplay translation queue

Generate the queue with Python 3.14:

```powershell
python tools/localization/build_live_gameplay_queue.py
```

Refresh the official roster cache explicitly with `--refresh`. Use `--offline`
to reproduce a queue without network access. Cached API payloads and the CURRENT
entity table are stored under `translation/cache/live/`.

The generator is read-only for Juvio. It reads CURRENT English from the
installed upstream archive and downloads the official active hero/item lists.

- `live_gameplay_queue.jsonl` — complete scoped inventory, including completed work.
- `live_next_work.jsonl` — only `TODO` and `STALE_REVIEW`, ordered for translation.
- `live_owner_progress.jsonl` — progress per active hero and item.
- `live_scope_snapshot.json` — reproducibility snapshot of API and upstream identities.
- `live_gameplay_progress.json` — aggregate report.
- `live_p0_work.jsonl` — stale or invalid translations that must be repaired first.
- `live_p1_work.jsonl` — active hero ability descriptions and state tooltips.
- `live_p2_work.jsonl` — active item descriptions and state tooltips.
- `live_p3_work.jsonl` — main menu, settings and bundled current patch-note UI.
- `translation/context/live/*_context_packs.jsonl` — complete per-owner context.

Priority policy: P0 repairs current errors; P1 covers all 106 active heroes; P2
covers all active items; P3 covers main menu, settings, current patch notes and
the final runtime audit through their existing dedicated pipelines.

Validate the P3 surfaces after applying the Preact human batches:

```powershell
py -3.14 tools/localization/apply_preact_human_batches.py
py -3.14 tools/localization/validate_p3_localization.py
```

Run the archive-free validator after every batch:

```powershell
py -3.14 tools/localization/validate_live_localization.py --batch translation/human/batch_NNN_name.json
```

Excluded by design: hero biographies/roles, voice and bot lines, flavor text,
entity names, search metadata, internal identifiers and deprecated empty values.

`STALE_REVIEW` means CURRENT English changed after a manual translation. Such a
row must be translated again from CURRENT; the previous Russian value is only a
reference and must not be applied automatically.

`INVALID_REVIEW` means an existing translation lost a structural token or a
protected canonical name. It is excluded from the completed count.
