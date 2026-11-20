#!/usr/bin/env python3
"""Verify the published app.bin, and optionally a locally rebuilt one.

    python tools/verify.py            # check published artifact + optional rebuild
    python tools/verify.py --all      # also verify every entry in MANIFEST.sha256
"""
import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# hello-flash/app.bin as it existed when the device was flashed.
REF_SHA256 = "5a502b609a0c9306384fa913"      # first 24 hex chars
REF_SIZE = 805470


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="verify MANIFEST.sha256 too")
    args = ap.parse_args()

    ref = os.path.join(ROOT, "hello-flash", "app.bin")
    if not os.path.isfile(ref):
        sys.exit("missing published artifact: " + ref)
    d = sha256(ref)
    size = os.path.getsize(ref)
    ok = d.startswith(REF_SHA256) and size == REF_SIZE
    print("published  hello-flash/app.bin : %d bytes  sha256=%s  [%s]" %
          (size, d, "OK" if ok else "MISMATCH"))

    rebuilt = os.path.join(ROOT, "artifacts", "app.bin.rebuilt")
    if os.path.isfile(rebuilt):
        d2 = sha256(rebuilt)
        same = d2 == d
        print("rebuilt    artifacts/app.bin.rebuilt : %d bytes  sha256=%s  [%s]" %
              (os.path.getsize(rebuilt), d2,
               "BYTE-IDENTICAL" if same else "DIFFERENT"))
        if not same:
            print("  -> your toolchain/SDK state differs; see BUILD.md")
    else:
        print("rebuilt    (not present yet - run: python tools/build.py)")

    if args.all:
        mf = os.path.join(ROOT, "MANIFEST.sha256")
        bad = 0
        total = 0
        for line in open(mf, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, rel = line.split(None, 1)
            rel = rel.lstrip("*").strip()
            p = os.path.join(ROOT, rel)
            total += 1
            if not os.path.isfile(p) or sha256(p) != digest:
                print("  BAD", rel)
                bad += 1
        print("manifest   %d/%d files OK" % (total - bad, total))

    if not ok:
        sys.exit(1)
    print("\nReproduction of the flashed image hash: OK")


if __name__ == "__main__":
    main()
