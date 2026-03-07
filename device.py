"""OpenRazer device connection utility."""

import sys
import time


def get_device(name_filter=None, retries=10, retry_delay=3):
    """Find a Razer device with per-key RGB (matrix) support.

    On startup, the OpenRazer daemon may not be ready yet.
    Retries several times before giving up.
    """
    try:
        from openrazer.client import DeviceManager
    except ImportError:
        print("openrazer Python library not found.", file=sys.stderr)
        print("Install openrazer for your distribution:", file=sys.stderr)
        print("  https://openrazer.github.io/#download", file=sys.stderr)
        sys.exit(1)

    for attempt in range(retries):
        try:
            manager = DeviceManager()
        except Exception as e:
            if attempt < retries - 1:
                print(f"OpenRazer not ready, retrying in {retry_delay}s... ({e})", file=sys.stderr)
                time.sleep(retry_delay)
                continue
            print(f"Could not connect to OpenRazer daemon: {e}", file=sys.stderr)
            sys.exit(1)

        if not manager.devices:
            if attempt < retries - 1:
                print(f"No devices found, retrying in {retry_delay}s...", file=sys.stderr)
                time.sleep(retry_delay)
                continue
            print("No Razer devices found. Is openrazer-daemon running?", file=sys.stderr)
            sys.exit(1)

        for device in manager.devices:
            if not device.fx.advanced:
                continue
            if name_filter is None or name_filter.lower() in device.name.lower():
                return device

        # Found devices but none with matrix support — no point retrying
        break

    print("No Razer device with per-key RGB support found.", file=sys.stderr)
    if name_filter:
        print(f"Filter: '{name_filter}'", file=sys.stderr)
    print("Available devices:", file=sys.stderr)
    for d in manager.devices:
        has_matrix = "yes" if d.fx.advanced else "no"
        print(f"  {d.name} (matrix: {has_matrix})", file=sys.stderr)
    sys.exit(1)
