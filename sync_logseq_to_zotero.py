#!/usr/bin/env python3
"""
Sync Logseq pages with #zotero tag to Zotero by adding 'in_logseq' tag.
Uses batch checking to efficiently tag only items that need it.

Usage:
    python sync_logseq_to_zotero.py [GRAPH_NAME]

Example:
    python sync_logseq_to_zotero.py "2025-10-26 Logseq DB"

If no graph name is provided, it will attempt to auto-detect.
"""

import sys
import subprocess
import re
import keyring
from pyzotero import zotero

SERVICE_NAME = "zotero-tag-automation"  # Share credentials with zotero-tag-automation
TAG_NAME = "in_logseq"

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

    try:
        result = subprocess.run(
            ['logseq', 'query', graph_name, query],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract item keys from URLs
        # Format: zotero://select/library/items/XXXXXXXX
        pattern = r'zotero://select/library/items/([A-Z0-9]+)'
        matches = re.findall(pattern, result.stdout)

        item_keys = set(matches)
        print(f"Found {len(item_keys)} items in Logseq with Zotero URLs")

        return item_keys

    except subprocess.CalledProcessError as e:
        print(f"✗ Error querying Logseq: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

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
    if len(sys.argv) > 1:
        graph_name = sys.argv[1]
    else:
        # Try to auto-detect most recent graph
        try:
            result = subprocess.run(['logseq', 'list'], capture_output=True, text=True, check=True)
            # Parse output to find first DB graph
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if 'DB Graphs:' in line and i + 1 < len(lines):
                    graph_name = lines[i + 1].strip()
                    break
            else:
                print("✗ Error: Could not auto-detect graph. Please provide graph name.")
                print()
                print("Usage: python sync_logseq_to_zotero.py [GRAPH_NAME]")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Error listing Logseq graphs: {e}")
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
    logseq_items = get_logseq_zotero_items(graph_name)

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
