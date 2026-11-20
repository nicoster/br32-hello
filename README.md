# AC695N / BR23 "hello world" flash build — reproduction kit

[中文说明](#中文说明) | [BUILD.md](BUILD.md) | [FLASH.md](FLASH.md) | [REPRODUCE.md](REPRODUCE.md) | [EVIDENCE.md](EVIDENCE.md)

## What this is

A complete, byte-level reproducible snapshot of a **self-compiled "hello world" firmware**
for the Jieli (杰理) **AC695N / BR23** board inside the 35 RMB *拼音学习机* (Pinyin learning
machine). Built from the official public AC695N SOUNDBOX SDK release 3.1.2.

**The problem to be diagnosed:** after a flash that the downloader reported as fully
successful (`Download completed`, exit 0), the device **no longer enumerates on USB at all**
(no `VID_4C4A`, no `D:` mass-storage drive). It appears bricked. Replugging USB did not help.

**This repository deliberately does not contain a root-cause conclusion.** It contains the
source, the exact build chain, the exact flashing parameters, the flashes' artifacts, the
full downloader log, and an objective diff against a known-good firmware package. The goal
is to let someone else reproduce and diagnose.

> ⚠️ **Do not flash this onto your own device unless you have a hardware recovery path.**
> See [REPRODUCE.md § Safety](REPRODUCE.md#safety--recovery).

## What is in here

| Path | Why it matters |
|---|---|
| [`patches/hello_app.c`](patches/hello_app.c) | The entire new application source (one task, prints to UART) |
| [`tools/apply_patches.py`](tools/apply_patches.py) | Exact, idempotent source edits to the SDK tree |
| [`sdk-diff/sdk-changes.patch`](sdk-diff/sdk-changes.patch) | The same edits as a plain `git diff` (69 lines, 4 files) |
| [`sdk-diff/sdk.ld.generated`](sdk-diff/sdk.ld.generated) | Linker script produced by `pre_build` |
| [`tools/build.py`](tools/build.py), [`tools/package_app.py`](tools/package_app.py) | Exact compile + `sdk.elf` → `app.bin` packaging chain |
| [`tools/bootstrap.py`](tools/bootstrap.py) | One-command environment setup (SDK + toolchain) |
| [`artifacts/sdk.elf`](artifacts/sdk.elf) | The linked ELF (symbols, sections) — for disassembly |
| [`hello-flash/`](hello-flash/) | **The complete 16-file directory that was actually flashed** |
| [`history/flash_hello.bat.as-flashed`](history/flash_hello.bat.as-flashed) | The exact launcher used in the failing flash |
| [`logs/flash_hello_20261119.log`](logs/flash_hello_20261119.log) | Verbatim downloader output |
| [`BUILD.md`](BUILD.md) | **Step-by-step rebuild, with toolchain URLs and hashes** |
| [`FLASH.md`](FLASH.md) | **Every flashing command, side by side** |
| [`REPRODUCE.md`](REPRODUCE.md) | Timeline, symptoms, verification, recovery |
| [`EVIDENCE.md`](EVIDENCE.md) | Objective hashes / diffs / config values, no conclusions |
| [`docs/`](docs/) | Original design docs, the "固件目录包制作要求" spec, unbrick notes |
| [`MANIFEST.sha256`](MANIFEST.sha256) | Hash of every file in this repo |

## Quick start (rebuild the exact same `app.bin`)

```bat
python tools/bootstrap.py          :: clone SDK at locked commit + fetch toolchain
python tools/apply_patches.py      :: apply the 5 source changes
python tools/build.py              :: pre_build -> sdk.elf -> app.bin (never touches a device)
python tools/verify.py             :: compare your app.bin with the published hash
```

Then read [FLASH.md](FLASH.md) **before** going anywhere near hardware.

## Third-party binaries

`hello-flash/` contains Jieli's `isd_download.exe`, `uboot.boot`, `br23loader.bin`,
`key.txt`, `ota.bin`, `font.bin`, etc. as shipped with the SDK / the lztttt tool pack.
They are included **only because they are required to reproduce the exact failing flash**.
Copyright belongs to Jieli / the original pack authors. See [NOTICE.md](NOTICE.md).
The 289 MB SDK tree itself is **not** vendored — `bootstrap.py` clones it from Jieli's
public GitLab at a pinned commit instead.

---

<a name="中文说明"></a>
## 中文说明

这是一份**可完整复刻**的现场快照：用杰理官方公开 SDK（AC695N SOUNDBOX 3.1.2）自行编译的
hello world 固件，刷入拼多多 35 元《拼音学习机》（AC695N / BR23）后，
烧录器报告 `Download completed`、退出码 0，**但设备重启后 USB 完全不枚举**（无 `VID_4C4A`、
无 `D:` 盘），重插无效，疑似变砖。

仓库里**不写根因结论**，只摆事实：源码、完整编译链、烧录参数、编译产物、烧录日志全文、
以及与一套已刷成功固件的逐文件哈希对照。请自行复刻并判断。

最关键的三份文档：

1. **[BUILD.md](BUILD.md)** — `app.bin` 到底是怎么编译出来的（SDK commit、工具链下载与免安装解包、
   两条 make 命令、逐段 objcopy 打包规则、产物 sha256）。
2. **[FLASH.md](FLASH.md)** — 四条烧录命令逐字对比：**当时实际执行的那条**（缺
   `-tonorflash` / `-format all`）、事后修正版、**已验证成功**的明日香 v0.9.177 包、
   以及 SDK 官方 `download.bat`；外加 `isd_config.ini` 全部关键字段。
3. **[REPRODUCE.md](REPRODUCE.md)** — 完整时间线、设备现象、验证方式、救砖资料。

别急着刷真机：`hello-flash/` 是**导致问题的那一包**，仅供复现与离线分析。
