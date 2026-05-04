# API Run Archive

This folder is used by the API runtime to store fresh run response payloads.

Each fresh `/run` or `/multi-run` call writes:

- one JSON file containing the complete API response payload;
- one Markdown audit summary;
- one SQLite row in `data/api_runtime.db`, table `run_archive`.

Generated archive files are intentionally ignored by Git. The API response includes an `archive` block with the `archive_id`, storage status and runtime paths.
