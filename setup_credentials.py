#!/usr/bin/env python3
"""
setup_credentials.py - Store Zotero credentials in the macOS Keychain.

logseq-zotero-sync authenticates to the Zotero Web API using a Library ID and
an API key kept in the macOS Keychain. This script writes them there. The same
keychain service is shared with the zotero-tag-automation skill, so running this
once sets up both.

Stored under keychain service "zotero-tag-automation":
  - library_id : your numeric Zotero user/library ID
  - api_key    : your Zotero API key (needs library read + WRITE access)

Create an API key ("Allow library access" + "Allow write access"):
  https://www.zotero.org/settings/keys/new
Find your numeric Library ID ("Your userID for use in API calls"):
  https://www.zotero.org/settings/keys

After storing, this script makes one read-only call to Zotero to confirm the
key works and reports whether it has the write access the sync requires.

Usage:
  python setup_credentials.py
"""

import sys
import getpass

import keyring

SERVICE_NAME = "zotero-tag-automation"  # shared with the zotero-tag-automation skill


def store_credentials(library_id, api_key, service=SERVICE_NAME):
    """Write the Library ID and API key to the macOS Keychain under `service`."""
    keyring.set_password(service, "library_id", library_id)
    keyring.set_password(service, "api_key", api_key)


def verify_credentials(library_id, api_key):
    """
    Make one read-only Zotero call to confirm the credentials work.

    Returns (status, message):
      status is True  -> key is valid (message says whether it has write access)
      status is False -> Zotero rejected the credentials (or it couldn't connect)
      status is None  -> could not check (pyzotero not installed)
    """
    try:
        from pyzotero import zotero
    except ImportError:
        return None, "pyzotero is not installed, so the key was not verified live."

    try:
        zot = zotero.Zotero(library_id, "user", api_key)
        info = zot.key_info()
    except Exception as e:
        return False, f"Zotero rejected the credentials: {e}"

    # The sync adds tags, which requires library write access. Warn if missing.
    access = info.get("access", {}) if isinstance(info, dict) else {}
    user_access = access.get("user", {}) if isinstance(access, dict) else {}
    if user_access.get("write"):
        return True, "Key is valid and has library write access."
    return True, (
        "Key is valid, but it does NOT have library WRITE access. The sync needs "
        "write access to add tags - re-create the key with 'Allow write access' "
        "enabled, then run this again."
    )


def main():
    print("=" * 60)
    print("Zotero credential setup")
    print("=" * 60)
    print("Create an API key with 'Allow library access' + 'Allow write access':")
    print("  https://www.zotero.org/settings/keys/new")
    print("Find your numeric Library ID at:")
    print("  https://www.zotero.org/settings/keys")
    print()

    try:
        library_id = input("Zotero Library ID: ").strip()
        api_key = getpass.getpass("Zotero API key (hidden): ").strip()
    except EOFError:
        print("\nCancelled - no input received. Nothing was stored.")
        return 1

    if not library_id or not api_key:
        print("\nBoth Library ID and API key are required. Nothing was stored.")
        return 1

    store_credentials(library_id, api_key)
    print(f"\n[ok] Stored in macOS Keychain (service '{SERVICE_NAME}').")

    status, message = verify_credentials(library_id, api_key)
    if status is True:
        print(f"[ok] {message}")
        return 0
    if status is False:
        print(f"[FAILED] {message}")
        print(
            "  The values were stored, but verification failed. Double-check that "
            "the Library ID is your numeric userID and the API key is correct."
        )
        return 2
    print(f"[skipped] {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
