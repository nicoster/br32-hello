#!/usr/bin/env python3
"""Reproduce the exact build environment (no device is ever touched).

    1. clone the public Jieli AC695N SOUNDBOX SDK at the pinned commit
    2. download Jieli Windows toolchain 2.5.3 and unpack it WITHOUT installing
    3. print the next commands to run

All downloads go into <repo>/_cache. The SDK goes to <repo>/SDK (289 MB after build),
the toolchain to <repo>/toolchain/pi32. Re-running is safe/idempotent.

Usage:  python tools/bootstrap.py [--sdk URL] [--commit SHA] [--skip-toolchain]
"""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SDK = os.path.join(ROOT, "SDK")
CACHE = os.path.join(ROOT, "_cache")
TC = os.path.join(ROOT, "toolchain", "pi32")

SDK_URL = "https://gitlab.zh-jieli.com/soundbox/novisualization/ac695n_soundbox_sdk.git"
SDK_COMMIT = "641e45dff1a8dc455fc6ccd688236fa59688b9ee"
TC_URL = "https://jl-update.oss-cn-shenzhen.aliyuncs.com/2.5.3.exe"
INNO_URL = "https://constexpr.org/innoextract/files/innoextract-1.9-windows.zip"


def log(*a):
    print(*a, flush=True)


def download(url, dest):
    if os.path.isfile(dest) and os.path.getsize(dest) > 1024:
        log("  cached:", dest)
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    log("  downloading:", url)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    log("  saved:", dest, os.path.getsize(dest), "bytes")
    return dest


def ensure_sdk(url, commit):
    if os.path.isdir(os.path.join(SDK, ".git")):
        head = subprocess.check_output(["git", "-C", SDK, "rev-parse", "HEAD"], text=True).strip()
        log("[SDK] already present at", head[:12])
        if head != commit:
            log("[SDK] fetching pinned commit", commit[:12])
            subprocess.check_call(["git", "-C", SDK, "fetch", "--depth", "1", "origin", commit])
            subprocess.check_call(["git", "-C", SDK, "checkout", "--detach", commit])
        return
    log("[SDK] cloning", url)
    os.makedirs(ROOT, exist_ok=True)
    subprocess.check_call(["git", "clone", "--depth", "1", url, SDK])
    head = subprocess.check_output(["git", "-C", SDK, "rev-parse", "HEAD"], text=True).strip()
    if head != commit:
        log("[SDK] checking out pinned commit", commit[:12])
        subprocess.check_call(["git", "-C", SDK, "fetch", "--depth", "1", "origin", commit])
        subprocess.check_call(["git", "-C", SDK, "checkout", "--detach", commit])
    log("[SDK] HEAD:", subprocess.check_output(
        ["git", "-C", SDK, "rev-parse", "HEAD"], text=True).strip())


def ensure_toolchain():
    marker = os.path.join(TC, "bin", "clang.exe")
    if os.path.isfile(marker):
        log("[TC] already present:", TC)
        return
    if sys.platform != "win32":
        log("[TC] Windows toolchain required. On Linux/macOS, extract 2.5.3.exe manually")
        log("     or use the Linux toolchain tarball with the SDK's Linux make flow.")
        return

    inst = download(TC_URL, os.path.join(CACHE, "win-toolchain-2.5.3.exe"))
    iz = download(INNO_URL, os.path.join(CACHE, "innoextract.zip"))

    innodir = os.path.join(CACHE, "innoextract")
    if not os.path.isdir(innodir):
        with zipfile.ZipFile(iz) as z:
            z.extractall(innodir)
    exe = None
    for base, _dirs, files in os.walk(innodir):
        for f in files:
            if f.lower() == "innoextract.exe":
                exe = os.path.join(base, f)
                break
        if exe:
            break
    if not exe:
        sys.exit("innoextract.exe not found in downloaded archive")

    raw = os.path.join(CACHE, "tc-raw")
    log("[TC] unpacking (no install / no UAC)")
    subprocess.check_call([exe, "-d", raw, inst])

    # Inno Setup extracts absolute Windows paths into a "C$" folder.
    src = None
    for base, _dirs, _files in os.walk(raw):
        if os.path.isfile(os.path.join(base, "pi32", "bin", "clang.exe")):
            src = os.path.join(base, "pi32")
            break
    if src is None:
        # common layout: raw/C$/JL/pi32
        guess = os.path.join(raw, "C$", "JL", "pi32")
        if os.path.isfile(os.path.join(guess, "bin", "clang.exe")):
            src = guess
    if src is None:
        sys.exit("could not locate pi32 inside the extracted installer; inspect " + raw)

    os.makedirs(os.path.dirname(TC), exist_ok=True)
    if os.path.isdir(TC):
        shutil.rmtree(TC)
    shutil.move(src, TC)
    log("[TC] ready:", TC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdk", default=SDK_URL)
    ap.add_argument("--commit", default=SDK_COMMIT)
    ap.add_argument("--skip-toolchain", action="store_true")
    args = ap.parse_args()

    log("=" * 66)
    log("hello-sdk-repro environment bootstrap")
    log("=" * 66)
    ensure_sdk(args.sdk, args.commit)
    if not args.skip_toolchain:
        ensure_toolchain()

    log("\nNext steps:")
    log("  python tools/apply_patches.py")
    log("  python tools/build.py")
    log("  python tools/verify.py")
    log("\nIf your toolchain lives elsewhere:  python tools/build.py --toolchain C:/JL/pi32")


if __name__ == "__main__":
    main()
