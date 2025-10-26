# Logseq to Zotero Sync

Automatically tag Zotero items with `in_logseq` when they are referenced in Logseq pages with the #zotero tag.

## Overview

This tool syncs your Logseq knowledge base with Zotero by:
1. Querying Logseq (via CLI) for all pages with #zotero tag and Zotero URL property
2. Extracting the Zotero item keys from those URLs
3. Checking which items already have the `in_logseq` tag in Zotero
4. Batch tagging only the items that need it

This is **idempotent** - you can run it multiple times safely. It only tags items that don't already have the tag.

## Requirements

- **Logseq Desktop app** (CLI only works with desktop, not browser version)
- **@logseq/cli** installed globally (`npm install -g @logseq/cli`)
- Python 3.7+
- Zotero account with API access

## Installation

1. Clone or download this repository to `/Users/niyaro/Documents/Code/logseq-zotero-sync/`

2. Install Python dependencies:
   ```bash
   cd /Users/niyaro/Documents/Code/logseq-zotero-sync
   pip3 install -r requirements.txt
   ```

3. Set up credentials (shares credentials with zotero-tag-automation):

   If you've already set up zotero-tag-automation, you're done! This script uses the same keychain credentials.

   If not, run the setup from zotero-tag-automation:
   ```bash
   python /Users/niyaro/.claude/skills/zotero-tag-automation/setup_credentials.py
   ```

   You'll need:
   - Your Zotero Library ID (find at https://www.zotero.org/settings/keys)
   - Your Zotero API Key (create at https://www.zotero.org/settings/keys/new)

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

1. **Logseq Query**: Uses `logseq query` CLI command to find all pages with the Zotero URL property
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
- Run `logseq list` to see available graphs
- Specify the exact graph name as shown in the list

**"Credentials not found"**
- Run the setup_credentials.py script
- Check Keychain Access.app for the credentials

**"Command not found: logseq"**
- Install @logseq/cli: `npm install -g @logseq/cli`
- Verify: `logseq --version`

## Related Tools

- **zotero-tag-automation**: Tag Zotero items after search results
- **logseq-cli skill**: Interface with Logseq from Claude Code

## License

MIT License
