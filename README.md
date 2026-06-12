# Logseq to Zotero Sync

Automatically tag Zotero items with `in_logseq` when they are referenced in Logseq pages with the #zotero tag.

## Skill Installation

### For Claude Code

1. Clone or download this repository
2. Copy the `skill/` folder to your Claude Code skills directory:
   ```bash
   cp -r skill ~/.claude/skills/logseq-zotero-sync
   ```
3. Restart Claude Code to load the skill

## Overview

This tool syncs your Logseq knowledge base with Zotero by:
1. Querying Logseq (via CLI) for all pages with #zotero tag and Zotero URL property
2. Extracting the Zotero item keys from those URLs
3. Checking which items already have the `in_logseq` tag in Zotero
4. Batch tagging only the items that need it

This is **idempotent** - you can run it multiple times safely. It only tags items that don't already have the tag.

## Requirements

- **Logseq Desktop app** with its bundled `logseq` CLI on your PATH (ships with current Logseq.app; no npm install needed)
- Python 3.10+
- Zotero account with API access

## Installation

1. Clone this repository and `cd` into it:
   ```bash
   git clone https://github.com/kerim/logseq-zotero-sync.git
   cd logseq-zotero-sync
   ```

2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Set up credentials (shares credentials with zotero-tag-automation):

   If you've already set up zotero-tag-automation, you're done! This script uses the same keychain credentials.

   If not, run the included setup script. It stores your Library ID and API key
   in the macOS Keychain and then makes one read-only call to Zotero to confirm
   the key works (and warns if it lacks the write access the sync needs):
   ```bash
   python setup_credentials.py
   ```

   You'll need:
   - Your Zotero Library ID (find at https://www.zotero.org/settings/keys)
   - Your Zotero API Key (create at https://www.zotero.org/settings/keys/new, with "Allow write access")

## Usage

### Basic Usage

Run with auto-detected graph:
```bash
python sync_logseq_to_zotero.py
```

Or specify a graph name:
```bash
python sync_logseq_to_zotero.py "2025-10-26 Logseq DB"
```

### Typical Workflow

1. Add new literature notes to Logseq with #zotero tag and Zotero URL property
2. Run this script periodically to sync the `in_logseq` tag to Zotero
3. Use the `in_logseq` tag in Zotero to filter/organize your referenced items

### Example Output

```
==============================================================
Logseq to Zotero Sync
==============================================================

Querying Logseq graph: 2025-10-26 Logseq DB
Found 14 items in Logseq with Zotero URLs
Querying Zotero for items with 'in_logseq' tag...
Found 10 items already tagged with 'in_logseq'

Found 4 items that need tagging:
  - AA8CFB7Y
  - DUF7Q2B6
  - M2QGSQA9
  - ZTSWUK3C

Tagging 4 items with 'in_logseq'...

[1/4] ✓ AA8CFB7Y: Here we are together
[2/4] ✓ DUF7Q2B6: Reflections on Orthography in Formosan Languages
[3/4] ✓ M2QGSQA9: Taiwan Archaeology
[4/4] ✓ ZTSWUK3C: Who owns "the culture of the Yellow Emperor"?

==============================================================
Summary:
  Successful: 4/4
  Failed: 0/4
  Tag: in_logseq
==============================================================
```

## How It Works

1. **Logseq Query**: Uses `logseq query --graph "NAME" --query 'EDN' --output json` CLI command to find all pages with the Zotero URL property
2. **Extract Keys**: Parses the output to extract Zotero item keys (e.g., "M2QGSQA9")
3. **Batch Check**: Queries Zotero API for all items already tagged with `in_logseq`
4. **Diff**: Compares the two lists to find items that need tagging
5. **Tag**: Only tags items that don't already have the tag

This batch approach is efficient because:
- Only one query to Zotero for existing tags
- Only tags items that need it
- Idempotent - safe to run repeatedly

## Credentials

Credentials are stored securely in macOS Keychain using the service name `zotero-tag-automation` (shared with the zotero-tag-automation skill).

To view/manage:
1. Open Keychain Access.app
2. Search for "zotero-tag-automation"

## Troubleshooting

**"Graph not found"**
- Make sure you're using Logseq Desktop app (not browser)
- Run `logseq graph list --output json` to see available graphs
- Specify the exact graph name as shown in the list

**"Credentials not found"** (or Zotero returns `403 Invalid key`)
- Run `python setup_credentials.py` to store (or replace) your Library ID and API key
- A `403 Invalid key` from Zotero means the stored key was revoked/regenerated — create a new one and re-run the setup script
- Check Keychain Access.app (search "zotero-tag-automation") for the stored credentials

**"Command not found: logseq"**
- Make sure Logseq Desktop app is installed — the bundled `logseq` CLI ships with current Logseq.app
- Verify: `logseq --version`

## Related Tools

- **zotero-tag-automation**: Tag Zotero items after search results
- **logseq-cli skill**: Interface with Logseq from Claude Code

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Current version: **1.1.0**.

## License

MIT License
