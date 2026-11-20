#!/usr/bin/env python3
"""Package sdk.elf into app.bin WITHOUT invoking any flashing tool.

Mirrors cpu/br23/tools/download.bat (the __SHELL__/Windows branch of the
official SDK) but stops before the final download step.

Usage:
    python tools/package_app.py [--sdk DIR] [--toolchain DIR] [--out FILE]

Defaults assume this script lives in <workspace>/hello-sdk/tools/ and that
the SDK was cloned to <workspace>/hello-sdk/SDK.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_SDK = os.path.join(ROOT, "SDK")
DEFAULT_TC = os.environ.get(
    "JL_PI32", os.path.join(ROOT, "toolchain", "pi32"))
# bootstrap.py unpacks Jieli's win-toolchain 2.5.3 installer here without
# installing it. Override with --toolchain or JL_PI32 for C:\JL\pi32 etc.

# Mirrors the concat order in download.bat (generic soundbox case).
SECTIONS = [
    (".text", None),
    (".data", None),
    (".data_code", None),
    (".overlay_aec", "aeco.bin"),
    (".overlay_wav", "wav.bin"),
    (".overlay_ape", "ape.bin"),
    (".overlay_flac", "flac.bin"),
    (".overlay_m4a", "m4a.bin"),
    (".overlay_amr", "amr.bin"),
    (".overlay_dts", "dts.bin"),
    (".overlay_fm", "fmo.bin"),
    (".overlay_mp3", "mp3o.bin"),
    (".overlay_wma", "wmao.bin"),
]
# download.bat trims trailing 0xFF from these four overlays.
TRIM_FF = {"aeco.bin", "fmo.bin", "mp3o.bin", "wmao.bin"}
TRIM_TO = {"aeco.bin": "aec.bin", "fmo.bin": "fm.bin",
           "mp3o.bin": "mp3.bin", "wmao.bin": "wma.bin"}
TAIL = ["aec.bin", "wav.bin", "ape.bin", "flac.bin", "m4a.bin",
        "amr.bin", "dts.bin", "fm.bin", "mp3.bin", "wma.bin", "bank.bin"]


def parse_sections(objdump, elf):
    out = subprocess.check_output([objdump, "-h", elf], text=True, errors="replace")
    return {line.split()[1] for line in out.splitlines()
            if line.strip().startswith(tuple(str(i) for i in range(10)))
            and len(line.split()) >= 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdk", default=DEFAULT_SDK)
    ap.add_argument("--toolchain", default=DEFAULT_TC)
    ap.add_argument("--elf", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "artifacts", "app.bin.rebuilt"))
    args = ap.parse_args()

    objcopy = os.path.join(args.toolchain, "bin", "llvm-objcopy.exe")
    objdump = os.path.join(args.toolchain, "bin", "llvm-objdump.exe")
    elf = args.elf or os.path.join(args.sdk, "cpu", "br23", "tools", "sdk.elf")
    work = os.path.dirname(elf)
    for exe in (objcopy, objdump, elf):
        if not os.path.isfile(exe):
            sys.exit(f"missing: {exe}")

    present = parse_sections(objdump, elf)
    print(f"ELF: {elf}")
    print(f"sections: {', '.join(sorted(present))}")

    blobs = []
    for section, alias in SECTIONS:
        if section not in present:
            print(f"  skip {section} (absent)")
            continue
        tmp = os.path.join(work, "_pkg_" + section.strip(".") + ".bin")
        subprocess.check_call([objcopy, "-O", "binary", "-j", section, elf, tmp])
        data = open(tmp, "rb").read()
        os.remove(tmp)
        if alias in TRIM_FF:
            data = data.rstrip(b"\xff")
            alias = TRIM_TO[alias]
            print(f"  {section}: {len(data)} bytes (0xFF trimmed)")
        else:
            print(f"  {section}: {len(data)} bytes")
        blobs.append(data)

    bank = os.path.join(work, "bank.bin")
    if os.path.isfile(bank):
        data = open(bank, "rb").read()
        print(f"  bank.bin: {len(data)} bytes")
        blobs.append(data)

    out_data = b"".join(blobs)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(out_data)
    print(f"WROTE {args.out}: {len(out_data)} bytes ({len(out_data)/1024:.1f} KiB)")


if __name__ == "__main__":
    main()
