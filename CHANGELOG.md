# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-06-12

### Changed
- Rewrote the Logseq interface for the current `logseq` CLI that ships bundled with
  the Logseq desktop app. The script previously used the now-obsolete `@logseq/cli`
  npm package's command forms — bare `logseq list` for graph detection and a
  positional `logseq query GRAPH '<EDN>'` — both of which fail on the current CLI.
  It now uses `logseq graph list --output json` and
  `logseq query --graph NAME --query '<EDN>' --output json`.
- Logseq command results are parsed from JSON and checked against the response's
  `status` field, because the current CLI exits 0 even when a command fails. The
  harmless code-signing line the CLI prints to stderr is ignored.
- Updated the documented Python requirement to 3.10+ (required by the current
  pyzotero) and tidied the README install instructions.

### Added
- `setup_credentials.py`: stores your Zotero Library ID and API key in the macOS
  Keychain, then makes one read-only call to Zotero to confirm the key works and
  warns if it lacks the write access the sync needs. (The README and skill
  previously pointed at a setup script that did not exist.)
- A guard that stops with a clear message — before any Zotero write — if an
  auto-detected graph contains no Zotero links, so the sync never tags against the
  wrong graph. You can still pass a graph name explicitly to override auto-detection.

### Notes
- The Zotero/pyzotero side was unchanged. Every Zotero API call the script makes
  still works on the latest pyzotero (1.13.1) and Zotero Web API v3, verified by a
  live install and smoke test.

## [1.0.0] - 2025-10-26

### Added
- Initial release: a one-way, idempotent sync that tags Zotero items with
  `in_logseq` when they are referenced from Logseq. It queries Logseq for items
  carrying a Zotero URL, diffs them against the items already tagged in Zotero, and
  tags only the difference. Credentials are stored in the macOS Keychain (shared
  with the zotero-tag-automation skill). Packaged as a Claude Code skill.
