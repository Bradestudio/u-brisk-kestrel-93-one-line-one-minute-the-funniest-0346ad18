#!/usr/bin/env python3
"""Write the one-line AI excuse entry to /output/entry.txt.

Stdlib only, no network, no external files. Validates the entry
(1-200 characters, single line, not whitespace-only), writes it
atomically (temp file + os.replace + fsync), then reads it back
byte-for-byte and fails on any mismatch.
"""

import os
import sys
import tempfile

ENTRY = "I finished it on time in a parallel branch \u2014 then I merged the wrong timeline."

OUTPUT_PATH = "/output/entry.txt"


def main() -> int:
    entry = ENTRY

    # Validate: 1-200 characters, single line, not whitespace-only.
    if not entry or entry.strip() == "":
        print("error: entry is empty or whitespace-only", file=sys.stderr)
        return 1
    if len(entry) > 200:
        print(f"error: entry is {len(entry)} characters, max 200",
              file=sys.stderr)
        return 1
    if "\n" in entry or "\r" in entry:
        print("error: entry must be a single line", file=sys.stderr)
        return 1

    data = entry.encode("utf-8")

    # Atomic write: temp file in the same directory, fsync, replace.
    out_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".entry-",
                                    suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, OUTPUT_PATH)
        # Fsync the directory so the rename itself is durable.
        dir_fd = os.open(out_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Read back and verify byte-for-byte.
    with open(OUTPUT_PATH, "rb") as f:
        written = f.read()
    if written != data:
        print("error: read-back mismatch", file=sys.stderr)
        return 1

    print(f"Wrote {len(entry)} characters to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
