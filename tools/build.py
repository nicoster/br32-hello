#!/usr/bin/env python3
"""Build the hello SDK firmware: pre_build -> sdk.elf -> app.bin.

Deliberately does NOT invoke the post-build download.bat, so no device is
touched. Run: python tools/build.py
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SDK = os.path.join(ROOT, "SDK")
DEFAULT_TC = os.environ.get(
    "JL_PI32", os.path.join(ROOT, "toolchain", "pi32"))


def run(cmd, cwd, env):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=cwd, env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toolchain", default=DEFAULT_TC)
    args = ap.parse_args()
    # GNU make recipes are parsed by sh: forward slashes avoid escape loss.
    tc = args.toolchain.replace("\\", "/")
    for p in ("bin/clang.exe", "bin/llvm-objcopy.exe", "pi32v2-lib/r3/libc.a"):
        if not os.path.isfile(os.path.join(tc, *p.split("/"))):
            sys.exit(f"toolchain incomplete, missing {p}: {tc}")

    env = os.environ.copy()
    utils = os.path.join(SDK, "tools", "utils")
    env["PATH"] = utils + os.pathsep + os.path.join(tc, "bin") + os.pathsep + env.get("PATH", "")
    make = os.path.join(utils, "make.exe")
    common = [
        make, "OS=Windows_NT",
        f"TOOL_DIR={tc}/bin",
        f"SYS_LIB_DIR={tc}/pi32v2-lib/r3",
        f"SYS_INC_DIR={tc}/pi32v2-include",
    ]
    run(common + ["pre_build"], SDK, env)
    run(common + ["cpu/br23/tools/sdk.elf"], SDK, env)
    # Write to artifacts/ so the published (flashed) hello-flash/app.bin is
    # never overwritten -- verify.py needs it as the reference.
    out_bin = os.path.join(ROOT, "artifacts", "app.bin.rebuilt")
    run([sys.executable, os.path.join(HERE, "package_app.py"),
         "--toolchain", tc,
         "--out", out_bin], SDK, env)
    print("BUILD OK (no device touched)")
    print("rebuilt image:", out_bin, "- compare with: python tools/verify.py")


if __name__ == "__main__":
    main()
