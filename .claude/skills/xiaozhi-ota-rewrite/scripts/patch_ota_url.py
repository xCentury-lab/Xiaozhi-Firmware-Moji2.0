#!/usr/bin/env python3
"""In-place OTA URL rewrite for Xiaozhi firmware binaries.

Replaces `https://api.tenclass.net/xiaozhi/ota/` (and known variants) with the
target URL inside a .bin file (merged-binary or full flash dump). The new URL
must be <= the original length; remaining bytes are NUL-padded so file size and
all subsequent offsets stay byte-identical.

Creates `<file>.orig` backup unless one already exists. Requires exactly one
occurrence of a known source URL — refuses ambiguous inputs.
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

KNOWN_SOURCES = [
    b"https://api.tenclass.net/xiaozhi/ota/",
]
DEFAULT_TARGET = b"https://classism.net/xiaozhi/ota/"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path, help="firmware .bin to patch in place")
    ap.add_argument(
        "--url",
        default=DEFAULT_TARGET.decode(),
        help=f"new OTA URL (default: {DEFAULT_TARGET.decode()})",
    )
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="skip creating <file>.orig backup",
    )
    args = ap.parse_args()

    path: Path = args.file
    new_url: bytes = args.url.encode()

    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 2

    data = path.read_bytes()
    matches = [(src, data.count(src)) for src in KNOWN_SOURCES]
    total = sum(n for _, n in matches)
    if total == 0:
        print("error: no known OTA URL found in file", file=sys.stderr)
        for src, _ in matches:
            print(f"  searched for: {src.decode()}", file=sys.stderr)
        return 3
    if total > 1:
        print(f"error: expected 1 occurrence total, got {total}", file=sys.stderr)
        for src, n in matches:
            if n:
                print(f"  {src.decode()}: {n}", file=sys.stderr)
        return 4

    src = next(s for s, n in matches if n == 1)
    if len(new_url) > len(src):
        print(
            f"error: new URL ({len(new_url)}B) longer than source "
            f"({len(src)}B). Cannot patch in place.",
            file=sys.stderr,
        )
        return 5

    offset = data.index(src)
    patch = new_url + b"\x00" * (len(src) - len(new_url))
    assert len(patch) == len(src)

    if not args.no_backup:
        backup = path.with_suffix(path.suffix + ".orig")
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f"backup: {backup} (md5: {md5(backup)})")
        else:
            print(f"backup exists, not overwriting: {backup}")

    with path.open("r+b") as f:
        f.seek(offset)
        f.write(patch)

    after = path.read_bytes()
    assert len(after) == len(data), "size changed unexpectedly"
    assert after.count(src) == 0, "source URL still present"
    assert after.count(new_url) >= 1, "new URL not written"

    print(f"patched: {path}")
    print(f"  offset:    0x{offset:x} ({offset})")
    print(f"  src ({len(src)}B): {src.decode()}")
    print(f"  new ({len(new_url)}B): {new_url.decode()}")
    print(f"  pad:       {len(src) - len(new_url)} NUL byte(s)")
    print(f"  size:      {len(after)} bytes (unchanged)")
    print(f"  new md5:   {md5(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
