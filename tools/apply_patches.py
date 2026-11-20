#!/usr/bin/env python3
"""Apply the hello project's minimal patches to the official SDK tree.

Idempotent: re-running does nothing. Every edit is a targeted string
replacement with strict assertions, so an SDK version change fails loudly
instead of silently corrupting the tree.

Run: python tools/apply_patches.py
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SDK = os.path.join(ROOT, "SDK")
PATCHES = os.path.join(ROOT, "patches")


def edit(path, old, new, count=1):
    data = open(path, encoding="utf-8", errors="surrogateescape").read()
    if new in data:
        print(f"  already applied: {os.path.relpath(path, ROOT)}")
        return False
    n = data.count(old)
    if n == count:
        data = data.replace(old, new)
        open(path, "w", encoding="utf-8", errors="surrogateescape").write(data)
        print(f"  patched {os.path.relpath(path, ROOT)}")
        return True
    sys.exit(f"FAIL: expected {count} occurrence(s) in {path}, found {n}: {old[:70]!r}")


def main():
    if not os.path.isdir(SDK):
        sys.exit(f"SDK not found: {SDK}")

    # 1) hello task source
    dst = os.path.join(SDK, "apps", "soundbox", "hello_app.c")
    src = os.path.join(PATCHES, "hello_app.c")
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print("  added apps/soundbox/hello_app.c")
    else:
        print("  hello_app.c already present")

    # 2) Makefile: compile hello_app.c, define CONFIG_BOARD_BR23_HELLO,
    #    and enable PC_POWER_ON_CHARGE (USB-connected boot must reach PC mode).
    mf = os.path.join(SDK, "Makefile")
    edit(mf, "\tapps/soundbox/app_main.c \\\n",
         "\tapps/soundbox/app_main.c \\\n\tapps/soundbox/hello_app.c \\\n")
    edit(mf, "\t-DCONFIG_CPU_BR23 \\\n",
         "\t-DCONFIG_CPU_BR23 \\\n"
         "\t-DCONFIG_BOARD_BR23_HELLO \\\n"
         "\t-DPC_POWER_ON_CHARGE \\\n")

    # 3) Board config: UART0 TX PA05 -> PB04 (this board's actual pin).
    cfg = os.path.join(SDK, "apps", "soundbox", "board", "br23",
                       "board_ac695x_demo", "board_ac695x_demo_cfg.h")
    data = open(cfg, encoding="utf-8", errors="surrogateescape").read()
    data2, n = re.subn(r"(TCFG_UART0_TX_PORT[^\n]*?)IO_PORTA_05",
                       r"\1IO_PORTB_04", data)
    if n == 1:
        open(cfg, "w", encoding="utf-8", errors="surrogateescape").write(data2)
        print("  board cfg: UART0 TX -> PB04")
    elif "TCFG_UART0_TX_PORT" in data and "IO_PORTB_04" in data:
        print("  board cfg: UART0 TX already PB04")
    else:
        sys.exit("FAIL: UART TX patch did not match")

    # SD0 demo port 'B' is not this board's wiring; keep the card unmounted in M1.
    edit(cfg, "#define TCFG_SD0_ENABLE\t\t\t\t\t\tENABLE_THIS_MOUDLE",
              "#define TCFG_SD0_ENABLE\t\t\t\t\t\tDISABLE_THIS_MOUDLE")

    # 4) app_main.c: start the hello task before the app task loop.
    am = os.path.join(SDK, "apps", "soundbox", "app_main.c")
    edit(am, "void app_main()\n{\n    log_info(\"app_main\\n\");\n",
         "void app_main()\n{\n"
         "    extern void hello_app_init(void);\n"
         "    hello_app_init();\n"
         "    log_info(\"app_main\\n\");\n")

    # 5) power_on.c: default to PC/UDISK task (the reflash entry point).
    po = os.path.join(SDK, "apps", "soundbox", "task_manager", "power_on", "power_on.c")
    # Two BT switches exist in this file; only the one in power_on_init()
    # (the one followed by the APPLE_DOCK branch) controls cold-boot mode.
    edit(po,
         "#endif\n\n#if TCFG_APP_BT_EN\n    app_task_switch_to(APP_BT_TASK);\n#else\n\n#if TCFG_USB_APPLE_DOCK_EN",
         "#endif\n\n#if TCFG_APP_BT_EN\n"
         "    app_task_switch_to(APP_PC_TASK);   /* HELLO: UDISK mode = reflash entry */\n"
         "#else\n\n#if TCFG_USB_APPLE_DOCK_EN")

    print("PATCHES OK")


if __name__ == "__main__":
    main()
