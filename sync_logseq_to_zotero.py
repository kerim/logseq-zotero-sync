#!/usr/bin/env python3
"""
Sync Logseq pages with #zotero tag to Zotero by adding 'in_logseq' tag.
Uses batch checking to efficiently tag only items that need it.
Targets the Logseq.app-bundled `logseq` CLI (no npm install needed).

Usage:
    python sync_logseq_to_zotero.py [GRAPH_NAME]

Example:
    python sync_logseq_to_zotero.py "2025-10-26 Logseq DB"

If no graph name is provided, it will attempt to auto-detect.
"""

import sys
import subprocess
import re
import json
import keyring
from pyzotero import zotero

__version__ = "1.1.0"

SERVICE_NAME = "zotero-tag-automation"  # Share credentials with zotero-tag-automation
TAG_NAME = "in_logseq"


def run_logseq_json(args):
    """
    Run a logseq CLI command and return parsed JSON output.

    args: list of CLI arguments after 'logseq' (e.g. ['graph', 'list', '--output', 'json'])

    Returns (data_dict, raw_stdout) where data_dict is the parsed JSON.
    Raises RuntimeError if the output is not valid JSON or status != 'ok'.
    stderr is ignored entirely (Electron codesign noise on every call).
    """
    result = subprocess.run(['logseq'] + args, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Logseq CLI returned non-JSON output: {result.stdout[:500]}"
        )

    if data.get('status') != 'ok':
        raise RuntimeError(f"Logseq CLI error: {data}")

    return data, result.stdout


def detect_graph():
    """
    Auto-detect the first available Logseq graph.
    Returns the graph name string.
    Raises RuntimeError if no graphs are found.
    """
    data, _ = run_logseq_json(['graph', 'list', '--output', 'json'])
    graphs = data.get('data', {}).get('graphs')
    if not graphs:
        raise RuntimeError("No Logseq graphs found")
    return graphs[0]


def get_credentials():
    """Retrieve credentials from macOS Keychain"""
    library_id = keyring.get_password(SERVICE_NAME, "library_id")
    api_key = keyring.get_password(SERVICE_NAME, "api_key")

    if not library_id or not api_key:
        print("✗ Error: Credentials not found in Keychain")
        print()
        print("Please run setup_credentials.py first to store your credentials:")
        print("  python setup_credentials.py")
        print()
        sys.exit(1)

    return library_id, api_key

def get_logseq_zotero_items(graph_name):
    """
    Query Logseq CLI to get all pages with Zotero URLs.
    Returns a set of Zotero item keys.
    """
    print(f"Querying Logseq graph: {graph_name}")

    # Run logseq query to get Zotero URLs
    query = '[:find (pull ?b [:block/title {:user.property/ZoteroURL-om1JHnZv [:block/title]}]) :where [?b :user.property/ZoteroURL-om1JHnZv]]'

    data, raw = run_logseq_json(
        ['query', '--graph', graph_name, '--query', query, '--output', 'json']
    )

    # Extract item keys from URLs in the raw stdout
    # Format: zotero://select/library/items/XXXXXXXX
    pattern = r'zotero://select/library/items/([A-Z0-9]+)'
    matches = re.findall(pattern, raw)

    item_keys = set(matches)
    print(f"Found {len(item_keys)} items in Logseq with Zotero URLs")

    return item_keys

def get_tagged_items(zot):
    """
    Get all Zotero items that already have the 'in_logseq' tag.
    Returns a set of item keys.
    """
    print(f"Querying Zotero for items with '{TAG_NAME}' tag...")

    try:
        # Search for items with the tag
        items = zot.everything(zot.items(tag=TAG_NAME))
        item_keys = {item['key'] for item in items}
        print(f"Found {len(item_keys)} items already tagged with '{TAG_NAME}'")
        return item_keys

    except Exception as e:
        print(f"✗ Error querying Zotero: {e}")
        sys.exit(1)

def tag_items(zot, item_keys):
    """Tag Zotero items with 'in_logseq' tag"""
    if not item_keys:
        print("No items to tag!")
        return True

    print(f"\nTagging {len(item_keys)} items with '{TAG_NAME}'...")
    print()

    successful = 0
    failed = 0
    errors = []

    for i, item_key in enumerate(sorted(item_keys), 1):
        try:
            # Get the item
            item = zot.item(item_key)

            # Get existing tags
            existing_tags = [t['tag'] for t in item['data'].get('tags', [])]

            # Add new tag
            if TAG_NAME not in existing_tags:
                new_tags = existing_tags + [TAG_NAME]
                item['data']['tags'] = [{'tag': t} for t in new_tags]

                # Update the item
                zot.update_item(item)
                title = item['data'].get('title', 'Untitled')
                print(f"[{i}/{len(item_keys)}] ✓ {item_key}: {title}")
                successful += 1
            else:
                print(f"[{i}/{len(item_keys)}] ⊙ {item_key} (already tagged)")
                successful += 1

        except Exception as e:
            print(f"[{i}/{len(item_keys)}] ✗ {item_key}: {e}")
            errors.append((item_key, str(e)))
            failed += 1

    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Successful: {successful}/{len(item_keys)}")
    print(f"  Failed: {failed}/{len(item_keys)}")
    print(f"  Tag: {TAG_NAME}")
    print("=" * 60)

    if errors:
        print()
        print("Errors:")
        for item_key, error in errors:
            print(f"  {item_key}: {error}")
        return False

    return True

def main():
    # Get graph name from arguments or use default
    graph_specified_by_user = len(sys.argv) > 1
    if graph_specified_by_user:
        graph_name = sys.argv[1]
    else:
        # Try to auto-detect most recent graph
        try:
            graph_name = detect_graph()
            print(f"Auto-detected graph: {graph_name}")
        except RuntimeError as e:
            print(f"✗ Error listing Logseq graphs: {e}")
            print()
            print("Usage: python sync_logseq_to_zotero.py [GRAPH_NAME]")
            sys.exit(1)

    print("=" * 60)
    print("Logseq to Zotero Sync")
    print("=" * 60)
    print()

    # Get credentials
    library_id, api_key = get_credentials()

    # Connect to Zotero
    zot = zotero.Zotero(library_id, 'user', api_key)

    # Get items from Logseq
    try:
        logseq_items = get_logseq_zotero_items(graph_name)
    except RuntimeError as e:
        print(f"✗ Error querying Logseq: {e}")
        sys.exit(1)

    # Zero-result safety guard for auto-detected graphs
    if not graph_specified_by_user and len(logseq_items) == 0:
        print(f"Auto-detected graph '{graph_name}' has no Zotero URLs.")
        print(f"Specify the correct graph: python sync_logseq_to_zotero.py \"GRAPH NAME\"")
        sys.exit(1)

    # Get items already tagged in Zotero
    tagged_items = get_tagged_items(zot)

    # Find items that need tagging
    items_to_tag = logseq_items - tagged_items

    if not items_to_tag:
        print()
        print("✓ All Logseq items are already tagged in Zotero!")
        print("  No action needed.")
        return

    print()
    print(f"Found {len(items_to_tag)} items that need tagging:")
    for key in sorted(items_to_tag):
        print(f"  - {key}")

    # Tag the items
    success = tag_items(zot, items_to_tag)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
