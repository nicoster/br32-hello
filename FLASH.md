# Flashing parameters — verbatim, side by side

**Read this together with [REPRODUCE.md](REPRODUCE.md).** The failing flash used the
launcher preserved in [`history/flash_hello.bat.as-flashed`](history/flash_hello.bat.as-flashed).
The file currently in [`hello-flash/flash_hello.bat`](hello-flash/flash_hello.bat) was
**edited afterwards** and has never been run.

---

## A. The command that produced the problem (2026-11-19, ~18:53)

```
isd_download.exe -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -key key.txt -reboot 2500
```

Run from `hello-flash/` in an **administrator** CMD. Note what is **absent**:
`-tonorflash`, `-format all`. The log consequently printed `ERASE MODE : NONE`.

Full launcher file: [`history/flash_hello.bat.as-flashed`](history/flash_hello.bat.as-flashed).
It is pure ASCII and contains an admin-rights check (`net session`).

## B. Post-mortem edit (NOT executed)

```
isd_download.exe -tonorflash -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all -key key.txt -reboot 2500
```

Only `-tonorflash` and `-format all` were added. This file is what
[`hello-flash/flash_hello.bat`](hello-flash/flash_hello.bat) contains **now**.
It has never been flashed onto the device. Its "Expected log: ERASE MODE : NONE" line is
stale text left over from version A and is **not** a prediction of its behaviour.

## C. Known-good reference — Asuka v0.9.177 package (flashed successfully before)

```
.\isd_download.exe -tonorflash -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all -key .\key.txt -reboot 2500
```

From `AC695N-SOUND-BOX_v0.9.177_isd-20261119--明日香/download.bat`. Its launcher first
runs `enter_uboot.ps1` to soft-trigger UBOOT from the running firmware, then downloads.
That package also ships `0x0000.key` and `0xB165.key` alongside `key.txt`.

## D. SDK 3.1.2 official `cpu/br23/tools/download/standard/download.bat`

Active line:

```
..\..\isd_download.exe -tonorflash -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all %1
```

Commented-out variant in the same file (extra resources):

```
:: ..\..\isd_download.exe ... -res font.bin gbk2utf8.tab AD10x_code.bin tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all %1
```

So the SDK's own standard flash **always** uses `-tonorflash -format all`, and the
3-file `-res` list is the SDK default (not an omission by us).

## E. lztttt `flash_only.bat` (tool pack this project borrowed its support files from)

```
isd_download.exe -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -key key.txt -reboot 2500
```

Identical to (A). That pack targets its own `app.bin`, not our SDK build.

## Parameter comparison table

| Switch | A (failing) | B (edited, unrun) | C (known-good) | D (SDK official) | E (lztttt) |
|---|---|---|---|---|---|
| `-tonorflash` | — | ✅ | ✅ | ✅ | — |
| `-format all` | — | ✅ | ✅ | ✅ | — |
| `-dev br23` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-boot 0x12000` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-div8` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-wait 300` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-uboot uboot.boot` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-app app.bin` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-res` (3 files) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `-key key.txt` | ✅ | ✅ | ✅ | `%1` (passed in) | ✅ |
| `-reboot 2500` | ✅ | ✅ | ✅ | ✅ | ✅ |
| pre-step `enter_uboot.ps1` | — | — | ✅ | — | — |

---

## `isd_config.ini` (identical in our pack and the known-good pack)

SHA-256 `19278084a327a6eac896482b` — byte-identical to the Asuka package.
Active keys:

```
NEW_FLASH_FS      = YES
FORCE_VM_ALIGN    = YES
ENTRY             = 0x1E00100
PID               = AC695N_soundbox
VID               = 0.01
DOWNLOAD_MODEL    = usb
FLASH_BIN_CNT     = 6
SDK_TYPE          = SOUNDBOX
SPI               = 2_3_0_0
RESET             = PB01_08_0
EX_FLASH          = PA03_1A_NULL
VM_ADR            = 0
VM_LEN            = 32K
VM_OPT            = 1
```

The downloader log reported a **computed** VM layout that differs from the literal
`VM_LEN=32K` above:

```
VM size          = 0x2a000
VM_START_ADDR    = 0xd2000
VM_END_ADDR      = 0xfc000
BTIF_RESERVED    = 0xfd000 - 0xfe000
LRIF_RESERVED    = 0xfe000 - 0xff000
FLASH_BIN_SIZE   = 0xd1000
FLASH_NEED_SIZE  = 0xff000
FLASH_REAL_SIZE  = 0x100000
ENTRY_ADDR       = 0x1E00100
ERASE MODE       : NONE
UBOOT VERSION    : 2022-07-27 19:38:08,UBOOT-$-@20220728-$9ec2e8d
```

## The 16 files present in the flashed directory

See [`EVIDENCE.md`](EVIDENCE.md) for full hashes and the file-by-file comparison against
the known-good package. Summary of provenance:

| Files | Source |
|---|---|
| `app.bin` | **ours**, built per [BUILD.md](BUILD.md) |
| `uboot.boot`, `key.txt`, `isd_config.ini`, `tone.cfg`, `cfg_tool.bin`, `eq_cfg_hw.bin`, `isd_download.exe` | copied from `workspace/lztttt/firmware/` (all **byte-identical** to SDK 3.1.2's own `cpu/br23/tools/` versions, verified) |
| `br23loader.bin`, `ota.bin` | copied from `lztttt/firmware/` |
| `font.bin`, `gbk2utf8.tab`, `script.ver` | copied from SDK `cpu/br23/tools/download/standard/` and `cpu/br23/tools/` |
| `jl_isd.bin`, `jl_isd.fw` | **generated by isd_download.exe during the flash** |
| `flash_hello.bat` | ours |

The five implicit files (`br23loader.bin`, `font.bin`, `gbk2utf8.tab`, `ota.bin`,
`script.ver`) were added **after** the first packaging attempt, following
[`docs/固件目录包制作要求.md`](docs/固件目录包制作要求.md). `br23loader.bin` is explicitly
required by that spec. None of them appear in the `-res` list.

## Note on `ota.bin`

Three copies (ours / lztttt / Asuka) are byte-identical: 13,838 B,
SHA-256 `4d634819dd41f0a2875f4576c6fd2dff`. Parsed header:
`magic=0x7713b256, ver=32, total=13758, header_len=65`, embedded filename `nor_ota.bin`.
No version string. It is a generic OTA container, not app-specific.

## Where the flash was done

Administrator CMD on Windows 11, `cd /d C:\br23\workspace\pinyin-fw\hello-sdk\hello-flash`,
then `flash_hello.bat`. The device was connected **only by USB** — no serial console, no
external debugger, no hardware dongle attached at the time.
