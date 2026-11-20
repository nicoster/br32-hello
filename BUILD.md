# How `app.bin` was built — exact, reproducible build chain

This is the most important document in the repo. It answers: **where did the source come
from, what was changed, which toolchain, which commands, and how do I know I got the same
bytes?**

Everything below is literal — no paraphrasing. Paths use **forward slashes** because
SDK make recipes are parsed by `sh`; backslashes get eaten.

---

## 1. SDK source (pinned)

| Item | Value |
|---|---|
| Upstream | `https://gitlab.zh-jieli.com/soundbox/novisualization/ac695n_soundbox_sdk.git` (public) |
| Locked commit | `641e45dff1a8dc455fc6ccd688236fa59688b9ee` |
| Commit date | 2025-02-13 11:10:45 +0800 |
| Release | AC695N SOUNDBOX SDK **release 3.1.2** |
| App / board | `apps/soundbox`, `board/br23/board_ac695x_demo` |
| Clone command | `git clone --depth 1 https://gitlab.zh-jieli.com/soundbox/novisualization/ac695n_soundbox_sdk.git SDK` |
| Size | 213 MB clone / 289 MB after build |

The SDK tree is deliberately **not** vendored here (contains Jieli's closed-source `.a`
libraries). `tools/bootstrap.py` clones it at the pinned commit.

## 2. Toolchain (pinned)

| Item | Value |
|---|---|
| Package | Jieli Windows toolchain **2.5.3** (Inno Setup installer, ~52 MB) |
| URL | `https://jl-update.oss-cn-shenzhen.aliyuncs.com/2.5.3.exe` |
| Unpacked path used | `C:\br23\tmp\jl-tc\extracted\tc\JL\pi32` |
| `clang --version` | `clang version 4.0.1`, `Target: i686-pc-windows-msvc`, `Thread model: posix` |
| Required subdirs | `bin/`, `pi32v2-lib/r3/` (contains `libc.a`), `pi32v2-include/` |
| GNU make | **SDK's own** `SDK/tools/utils/make.exe` (system make not used) |

No installation / UAC was needed. The installer was unpacked rather than executed:

```bat
:: innoextract 1.9 from https://constexpr.org/innoextract/files/innoextract-1.9-windows.zip
innoextract.exe -d <outdir> 2.5.3.exe
:: result: <outdir>\C$\JL\pi32   (rename C$ -> tc to avoid '$' in make variables)
```

`tools/bootstrap.py` does this automatically. If you install the toolchain normally to
`C:\JL\pi32`, pass `--toolchain C:/JL/pi32` to `build.py`.

## 3. Source changes (the entire diff)

Five changes. Full diff: [`sdk-diff/sdk-changes.patch`](sdk-diff/sdk-changes.patch) (69 lines).
Authoritative idempotent applier: [`tools/apply_patches.py`](tools/apply_patches.py).
New file: [`patches/hello_app.c`](patches/hello_app.c).

| # | File | Change |
|---|---|---|
| 1 | `apps/soundbox/hello_app.c` | **NEW.** One task `hello_task()` looping `log_info("hello world #%u  (AC695N SDK, flash build)")` + `os_time_dly(100)`; `hello_app_init()` calls `task_create(hello_task, NULL, "hello")`. No LCD, no USB, no update code. |
| 2 | `Makefile` | Add `apps/soundbox/hello_app.c` to `c_SRC_FILES`; add `-DCONFIG_BOARD_BR23_HELLO` and `-DPC_POWER_ON_CHARGE` to `CC_DEFINE`. |
| 3 | `board/br23/board_ac695x_demo/board_ac695x_demo_cfg.h` | `TCFG_UART0_TX_PORT`: `IO_PORTA_05` → **`IO_PORTB_04`** (this board's real UART pin, shared with uboot). `TCFG_SD0_ENABLE`: `ENABLE_THIS_MOUDLE` → `DISABLE_THIS_MOUDLE`. |
| 4 | `apps/soundbox/app_main.c` | In `app_main()`, call `hello_app_init()` before `log_info("app_main\n")`. |
| 5 | `apps/soundbox/task_manager/power_on/power_on.c` | In `power_on_init()`, cold-boot switch `app_task_switch_to(APP_BT_TASK)` → **`app_task_switch_to(APP_PC_TASK)`** (intent: boot straight into UDISK/PC mode so a later reflash is possible). |

### Board macros that were **left untouched** (potentially relevant)

Read from `board_ac695x_demo_cfg.h` after patching:

```
TCFG_APP_PC_EN     = 1                      (kept — PC/USB-slave mode enabled)
TCFG_UDISK_ENABLE  = ENABLE_THIS_MOUDLE    (kept — mass-storage enabled)
TCFG_APP_BT_EN     = 1                      (kept — Bluetooth still compiled in)
TCFG_CHARGE_ENABLE = DISABLE                (demo value; real board charges over USB)
AD key on PA10                              (demo value; real board is PB01 long-press 8 s)
```

The demo board config was used as-is apart from the two lines above. `isd_config.ini`
specifies `RESET=PB01_08_0` for this physical board — that is a **different key pin** from
the demo board's AD key. Nothing in this project reconciled the two.

### USB reflash support was **not** written by us

`TCFG_APP_PC_EN` / `TCFG_UDISK_ENABLE` were kept, and cold boot was pointed at
`APP_PC_TASK`. The `0xFC0A` "enter UBOOT" USB vendor command handling itself lives in
Jieli's closed-source libraries; **no code was added for it** and it was never verified on
this build.

## 4. Exact build commands

From the repo root, after `bootstrap.py` and `apply_patches.py`:

```bat
set TC=C:/br23/tmp/jl-tc/extracted/tc/JL/pi32
set PATH=<repo>/SDK/tools/utils;%TC%/bin;%PATH%

:: 4a. Generate linker script + download scripts. Does NOT touch a device.
cd SDK
tools\utils\make.exe OS=Windows_NT TOOL_DIR=%TC%/bin ^
    SYS_LIB_DIR=%TC%/pi32v2-lib/r3 SYS_INC_DIR=%TC%/pi32v2-include ^
    pre_build

:: 4b. Link sdk.elf. NOTE: target is given explicitly.
::     Do NOT run the default "all" target — it ends in download.bat, which flashes hardware.
tools\utils\make.exe OS=Windows_NT TOOL_DIR=%TC%/bin ^
    SYS_LIB_DIR=%TC%/pi32v2-lib/r3 SYS_INC_DIR=%TC%/pi32v2-include ^
    cpu/br23/tools/sdk.elf

:: 4c. Package sdk.elf -> app.bin (objcopy only, no flashing tool invoked)
cd ..
python tools/package_app.py --toolchain %TC% --out artifacts/app.bin.rebuilt
```

`tools/build.py` runs 4a → 4b → 4c in one shot. It never invokes `download.bat`.

> **One deliberate difference from the original workspace:** in this reproduction repo
> `build.py` writes to `artifacts/app.bin.rebuilt` instead of `hello-flash/app.bin`, so
> the published reference image (the one that was actually flashed) is never
> overwritten. `verify.py` then compares the two byte-for-byte. The build logic itself
> is unchanged.

Generated linker script is included at [`sdk-diff/sdk.ld.generated`](sdk-diff/sdk.ld.generated)
(really `cpu/br23/sdk.ld`). Linked ELF: [`artifacts/sdk.elf`](artifacts/sdk.elf),
object list: [`artifacts/sdk.elf.objs.txt`](artifacts/sdk.elf.objs.txt).

## 5. How `app.bin` is packaged (this matters)

Official SDK `cpu/br23/tools/download.bat` concatenates 13 raw section blobs:

```
copy /b text.bin+data.bin+data_code.bin+aec.bin+wav.bin+ape.bin+flac.bin+
        m4a.bin+amr.bin+dts.bin+fm.bin+mp3.bin+wma.bin+bank.bin app.bin
```

[`tools/package_app.py`](tools/package_app.py) mirrors this using `llvm-objcopy -O binary
-j <section>` on `sdk.elf`, in this order:

```
.text, .data, .data_code,
.overlay_aec  -> aec.bin   (trailing 0xFF trimmed)
.overlay_wav  -> wav.bin
.overlay_ape  -> ape.bin
.overlay_flac -> flac.bin
.overlay_m4a  -> m4a.bin
.overlay_amr  -> amr.bin
.overlay_dts  -> dts.bin
.overlay_fm   -> fm.bin    (trailing 0xFF trimmed)
.overlay_mp3  -> mp3.bin   (trailing 0xFF trimmed)
.overlay_wma  -> wma.bin   (trailing 0xFF trimmed)
bank.bin                   (appended ONLY if the file exists)
```

**Verified fact:** `bank.bin` does not exist anywhere in this SDK tree, so it was **not**
appended. The official `download.bat` names it unconditionally. Whether that matters is
left to the reader. Sections absent from the ELF are skipped with a printed notice.

Result:

| Artifact | Size | SHA-256 (first 24 hex) |
|---|---|---|
| `hello-flash/app.bin` | **805,470 B** | `5a502b609a0c9306384fa913` |
| `artifacts/sdk.elf` | 5,734,176 B | see `MANIFEST.sha256` |

Independent checks already performed on the published `app.bin`:
- ELF contains symbol `hello_task`; `app.bin` contains the literal string `hello world`
  at offset 681422.
- `.text` starts at `0x1E00100`, matching `ENTRY=0x1E00100` in `isd_config.ini`.
- First 64 bytes are `81 ea ...`, the same startup template as both the lztttt and Asuka
  `app.bin` files.
- Contains `UPDATE-@20240426-$65f3999`.

Run `python tools/verify.py` after rebuilding to compare hashes byte-for-byte.

## 6. What was NOT built / NOT included

- No LCD / ST7305 driver. The screen is never touched by this firmware.
- No TF-card / font / index processing.
- No OTA packaging from our side (`ota.bin` was copied from the lztttt pack).
- `jl_isd.bin` / `jl_isd.fw` in `hello-flash/` were **generated by `isd_download.exe`
  during the failing flash** (mtime 18:53:24), not by our toolchain. `jl_isd.bin` is
  856,064 B = `0xd1000` = the `FLASH_BIN_SIZE` printed in the log.
- The 16.6 MB `.bc` LTO intermediates are not included.
