# Reproduction & symptom record

Objective timeline. No conclusions are drawn here; [EVIDENCE.md](EVIDENCE.md) holds the
raw comparisons.

## Hardware under test

| Item | Value |
|---|---|
| Device | 拼多多 35 元《拼音学习机》(Pinyin learning machine), reverse-engineered clone boards documented at `oshwhub.com/pla155/project_pyeunvkd` |
| SoC | Jieli **AC695N / BR23** |
| SPI NOR flash | **1 MB**, online id `eb6014`, uuid `11 20 04 11 05 08 09 03 B9 00 C2 00 FF FF FF FF` |
| Display | ST7305, 300×400 reflective LCD (bistable; keeps last image without power) |
| Touch | CST836U |
| USB VID/PID | `VID_4C4A` / `PID_4155` in normal UDISK mode; `PID_2342` seen in UBOOT mode |
| Mass storage | `D:`, ~4 GB FAT32 removable (TF card inside the unit) |
| Reset / download key | `RESET=PB01_08_0` in `isd_config.ini` → PB01 held 8 s |
| **Observable channels** | **USB only.** No serial console was wired. No screen output from our firmware (no LCD driver). |

## Timeline

1. **Earlier attempts** — `isd_download.exe` without administrator rights failed with
   `ERROR: Failed to download data to device br23, error = 433` after `Write block:13`.
   Flash may have been partially written at that point.

2. **RAM loading worked** — `python load_ram.py bin/nes_mario.bin` succeeded once the
   script gained Windows `\\.\PhysicalDrive*` scanning and UAC elevation. This confirmed
   administrator rights + SCSI pass-through + Jieli USB enumeration were all functional.
   RAM loading does **not** write flash.

3. **Original SDK cloned and compiled unmodified** — SDK 3.1.2 at commit `641e45d…`
   built cleanly with the 2.5.3 Windows toolchain. `sdk.elf` produced.

4. **Five source changes applied** (see [BUILD.md §3](BUILD.md#3-source-changes-the-entire-diff)),
   hello firmware built → `app.bin` 805,470 B.

5. **Flash package assembled** — initially 9 files; after reading
   [`docs/固件目录包制作要求.md`](docs/固件目录包制作要求.md), 5 implicit files were added,
   giving the 16-file directory in `hello-flash/`. Static self-check passed
   (`DOWNLOAD_MODEL=usb`, `RESET=PB01_08_0`, `ENTRY=0x1E00100`).

6. **The failing flash (2026-11-19 ~18:53)** — administrator CMD, command (A) in
   [FLASH.md](FLASH.md). Downloader output:
   `SPI nor flash online` → `ERASE MODE : NONE` → `Write sector:209` →
   `Write block:12…0` → `no license` → `Download completed.` → `device rebooting...` →
   `[INFO] downloader exited normally.` (exit 0).
   Full log: [`logs/flash_hello_20261119.log`](logs/flash_hello_20261119.log).

7. **After reboot, device gone.** Read-only Windows inspection:
   - All `VID_4C4A` PnP entries: `Present = False` (historical ghosts, not live).
   - `D:\` does not exist.
   - A `USB Serial Device (COM6)` appeared but is `VID_043E` — **not** a Jieli device.
   - A historical `USB\VID_4C4A&PID_2342` (UBOOT) entry exists from during the download.

8. **Physical USB replug did not restore enumeration.** User reports the unit is bricked.

## What "reproduce" means here

There are two independent things a reviewer may want to reproduce:

### R1 — Reproduce the build (safe, no hardware)

```bat
python tools/bootstrap.py
python tools/apply_patches.py
python tools/build.py
python tools/verify.py
```

`verify.py` compares the newly built `app.bin` against the published hash. If they match,
the exact same 805,470 bytes that were flashed have been recreated. Then inspect
`artifacts/sdk.elf`, `sdk-diff/sdk-changes.patch`, and `hello-flash/jl_isd.fw` offline.

### R2 — Reproduce the flash (⚠️ will likely brick a device)

Follow [FLASH.md §A](FLASH.md#a-the-command-that-produced-the-problem-2026-11-19-1853)
**exactly**: use the 16-file directory from `hello-flash/`, use command (A) — *not* the
edited `flash_hello.bat` — in an administrator CMD, with the device connected by USB only.

Suggested observations to capture, since there is no serial console:
- Device Manager / `Get-PnpDevice` before and after `-reboot 2500`.
- Whether `D:` appears.
- USB VID/PID enumeration events (a USB analyzer or `USBView` is ideal).
- Whether PB01 held 8 s (or a power cycle) makes `PID_2342` / UBOOT reappear.
- Screen state (reflective LCD keeps its last image, so a frozen frame is expected).

## Verification steps that were planned but never reached

The project's original acceptance criteria, for context:

| ID | Check | Status |
|---|---|---|
| A1 | Flash completes, exit 0 | ✅ observed in the log |
| A2 | After reboot, `D:` appears (UDISK mode ⇒ firmware alive) | ❌ did not happen |
| A3 | `br23_tool.py` menu 6 → `0xFC0A` → re-enumerate as `BR23 UBOOT1.00` → **second flash succeeds** | ⛔ never reachable |
| A4 | `hello world #N` on PB04 @ 1 Mbaud UART | ⛔ no serial console available |

Note A4 was never a viable check on this setup — USB was the only channel. A2 failing is
what makes the device look bricked.

## Safety / recovery

**Do not flash this package onto a device you care about unless you have a hardware path
in.** Software recovery tools all require the device to enumerate USB first, which is
exactly what stopped happening.

Available fallback assets referenced by this project (paths are from the original
workspace, not vendored here):

| Layer | Asset |
|---|---|
| Full-chip stock backup | `pinyin-fw/backup/stock_flash_20261113_110444.bin` |
| Restore tool | `pinyin-fw/src/pinyin-br23-restore/br23_tool.py` (menu 2 = restore, requires typing `YES`) |
| Soft trigger | same tool, menu 6 = `0xFC0A` enter UBOOT |
| Hardware forced download | USB_KEY dongle design + timing in [`docs/unbrick-notes.md`](docs/unbrick-notes.md) and [`docs/JIELI_RESEARCH_NOTES.md`](docs/JIELI_RESEARCH_NOTES.md). DP = 50 kHz clock, DM = `0x16EF` MSB-first; independent of app. |
| Key / efuse background | `docs/JIELI_RESEARCH_NOTES.md` §5 — commercial boards have efuse-trimmed keys; `key.txt` must match. |

The `ERASE MODE : NONE` flash did **not** erase the uboot region (`0x0–0x1000`), so in
principle the mask-ROM / uboot download path should still be reachable with the right
trigger — but that was not confirmed on this unit.

## Open facts that a reviewer may want to weigh

Presented neutrally, no ranking, no conclusion:

- Command (A) lacked `-tonorflash` and `-format all`; the SDK official command and the
  known-good package both have them.
- `ERASE MODE : NONE` means the previous firmware's VM area (`0xd2000–0xfc000`) survived.
- `no license` appeared once, just before `Download completed.` Its origin was not
  determined.
- `uboot.boot` used here is 8,320 B (SDK 3.1.2's own, version `UBOOT-@20220728`);
  the known-good package used a **different** 8,192 B `uboot.boot`.
- `cfg_tool.bin` used here is 916 B (`AC695X_1..11` project names); known-good used a
  different 889 B file (`jl_soundbox_1..11`). Similarly `tone.cfg` 34,672 vs 35,568 B.
- The demo board config was used with only two lines changed; the real board's key pin,
  charging behaviour, and LCD are wired differently from that demo.
- Cold boot was redirected to `APP_PC_TASK` with `-DPC_POWER_ON_CHARGE`; this path was
  never validated on hardware.
- `bank.bin` is named by the official `download.bat` concat but does not exist in the SDK
  tree, so `package_app.py` did not append it.
- `jl_isd.fw` / `jl_isd.bin` contain neither the plain `hello world` string nor the
  `UBOOT-` / `UPDATE-@` strings, and `app.bin`'s first 4 KiB is not present verbatim in
  `jl_isd.fw` — i.e. the downloader transforms/packs the image. The same is true of the
  known-good package.
