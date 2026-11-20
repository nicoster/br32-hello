# Objective evidence tables

Hashes are SHA-256 truncated to 24 hex chars (full hashes in
[`MANIFEST.sha256`](MANIFEST.sha256)). "Asuka" = the
`AC695N-SOUND-BOX_v0.9.177_isd-20261119--明日香` package that was flashed successfully
on this same board before. Nothing here is a conclusion.

## 1. Every file in the 16-file flashed directory

| File | Bytes | SHA-256 (24) | mtime (11-19) |
|---|---|---|---|
| `app.bin` | 805470 | `5a502b609a0c9306384fa913` | 16:51:39 |
| `br23loader.bin` | 24576 | `2bf56d6d4692424aa4b3be19` | 18:46:20 |
| `cfg_tool.bin` | 916 | `21334ccee5588a3e72bd871c` | 16:51:53 |
| `eq_cfg_hw.bin` | 1149 | `5bcd0724d9ce1d87c0f4e627` | 16:51:53 |
| `flash_hello.bat` | 1219 | `feb1efbb4ea3ceedfa25a5f6` | 19:25:09 ⚠️ edited after flash |
| `font.bin` | 806000 | `c994c762209dc275ab930eb8` | 18:46:20 |
| `gbk2utf8.tab` | 72198 | `877575496df1d773d316419b` | 18:46:21 |
| `isd_config.ini` | 4585 | `19278084a327a6eac896482b` | 16:51:53 |
| `isd_download.exe` | 2149408 | `35f5a24945882e99027086f9` | 16:51:56 |
| `jl_isd.bin` | 856064 | `dfe8e87cef7c654c619bb40e` | 18:53:24 ⚠️ generated during flash |
| `jl_isd.fw` | 863424 | `e764876728fc13267ab52b38` | 18:53:24 ⚠️ generated during flash |
| `key.txt` | 72 | `e4f4375ad26dd7f614b40612` | 16:51:52 |
| `ota.bin` | 13838 | `4d634819dd41f0a2875f4576` | 18:46:20 |
| `script.ver` | 27 | `9ae034d44c9a6b6e5b368e2e` | 18:46:21 |
| `tone.cfg` | 34672 | `5b210d909576c0f6f9b998cf` | 16:51:53 |
| `uboot.boot` | 8320 | `bec584bfbc84e0d393f02d0d` | 16:51:52 |

`jl_isd.bin` = 856,064 B = `0xd1000` = `FLASH_BIN_SIZE` printed in the downloader log.

## 2. Same-named files: our pack vs known-good Asuka pack

| File | Our bytes / Asuka bytes | Identical? | Asuka SHA-256 (24) |
|---|---|---|---|
| `app.bin` | 805470 / 878460 | **DIFF** | `3849972112e2f108dca83c3f` |
| `br23loader.bin` | 24576 / 24576 | SAME | `2bf56d6d4692424aa4b3be19` |
| `cfg_tool.bin` | 916 / 889 | **DIFF** | `418788bc121b80b6586ff74b` |
| `eq_cfg_hw.bin` | 1149 / 1149 | SAME | `5bcd0724d9ce1d87c0f4e627` |
| `isd_config.ini` | 4585 / 4585 | SAME | `19278084a327a6eac896482b` |
| `isd_download.exe` | 2149408 / 2149408 | SAME | `35f5a24945882e99027086f9` |
| `jl_isd.bin` | 856064 / 929792 | **DIFF** | `e4468037158c9117ca617917` |
| `jl_isd.fw` | 863424 / 937120 | **DIFF** | `1844f0544c619563cead6e9e` |
| `key.txt` | 72 / 72 | SAME | `e4f4375ad26dd7f614b40612` |
| `ota.bin` | 13838 / 13838 | SAME | `4d634819dd41f0a2875f4576` |
| `tone.cfg` | 34672 / 35568 | **DIFF** | `58e64f89763a0635a9dc9916` |
| `uboot.boot` | 8320 / 8192 | **DIFF** | `3070d65ff0ac812fdd559c08` |

Asuka additionally contains `0x0000.key` (72 B), `0xB165.key` (72 B),
`enter_uboot.ps1`, `download.bat`, `flash_all.bat`, `release_manifest.json`.

## 3. Provenance of our support files

| File | SDK 3.1.2 `cpu/br23/tools/` | lztttt `firmware/` | Our pack |
|---|---|---|---|
| `uboot.boot` | 8320 B, `bec584bf…` | 8320 B, `bec584bf…` | 8320 B, `bec584bf…` — all three identical |
| `cfg_tool.bin` | 916 B, `21334cce…` | 916 B, `21334cce…` | 916 B, `21334cce…` — all three identical |
| `tone.cfg` | 34672 B, `5b210d90…` | 34672 B, `5b210d90…` | 34672 B, `5b210d90…` — all three identical |
| `eq_cfg_hw.bin` | 1149 B | 1149 B | 1149 B — identical |
| `isd_config.ini` | 4585 B | 4585 B | 4585 B — identical |
| `key.txt` | 72 B | 72 B | 72 B — identical |
| `isd_download.exe` | 2149408 B | 2149408 B | 2149408 B — identical |

`SDK cpu/br23/tools/uboot_no_ota.boot` is a different 5,088 B file and was not used.

## 4. `uboot.boot` binary difference

| | Our 8,320 B | Asuka 8,192 B |
|---|---|---|
| First 32 bytes | `ff df 9f 1f fb 6b 2f ac 70 e1 a3 67 cc bd 5b 97 0f 1e 3c 78 d1 83 27 4e 9c 19 13 26 4c 98 30 60` | `01 00 f0 1f 00 40 00 00 10 00 00 00 7a eb f4 65 d8 e8 07 00 c0 ff 90 f6 e1 62 40 20 64 e0 80 01` |
| Version string | `UBOOT-$-@20220728-$9ec2e8d` | none found |
| First 8192 bytes equal | ❌ no | — |
| Extra trailing 128 B | ASCII table: `RESET`, `PSRAM`, `USBDP`, `USBDM`, `PLL_SRC`, `OSC_12M`, `UARTUPDATE` | — |

The downloader log printed
`UBOOT VERSION : 2022-07-27 19:38:08,UBOOT-$-@20220728-$9ec2e8d`, matching our file.

## 5. `cfg_tool.bin` header / project names

| | Ours (916 B) | Asuka (889 B) |
|---|---|---|
| First 16 bytes | `90 03 00 00 8f 5e c2 03 ff ff ff ff ff ff ff ff` | `75 03 00 00 3c 65 40 29 01 6a 6c 5f 73 6f 75 6e` |
| Embedded names | `AC695X_1` … `AC695X_11` | `jl_soundbox_1` … `jl_soundbox_11` |

## 6. `app.bin` structure checks

| Check | Result |
|---|---|
| Size | 805,470 B (Asuka 878,460 B, lztttt ~841 KiB) |
| First 64 bytes | `81 ea …` — same startup template as both other `app.bin` files |
| `.text` start in `sdk.elf` | `0x1E00100` = `ENTRY` in `isd_config.ini` = `ENTRY_ADDR` in log |
| ELF symbol `hello_task` | present |
| Literal `hello world` in `app.bin` | present at offset 681422 |
| `UPDATE-@…` version string | `UPDATE-@20240426-$65f3999` present in all three `app.bin` files |
| `key.txt` | byte-identical across our pack / lztttt / Asuka |
| Trailing `0xFF` run | only a few bytes in all three |

## 7. Final packed image (`jl_isd.fw`) string search

| Needle | Our `jl_isd.fw` | Our `jl_isd.bin` | Asuka `jl_isd.fw` |
|---|---|---|---|
| `hello world` | not found | not found | not found |
| `UBOOT-` | not found | not found | not found |
| `UPDATE-@` | not found | not found | not found |
| `app.bin` first 256 B verbatim | not found | — | — |
| `app.bin` first 4096 B verbatim | not found | — | — |

Same behaviour in the known-good package, so the downloader plainly packs/transforms the
image rather than embedding `app.bin` verbatim.

## 8. Downloader log verbatim

See [`logs/flash_hello_20261119.log`](logs/flash_hello_20261119.log). Key lines:
`ERASE MODE : NONE`, `no license`, `Download completed.`, `device rebooting...`,
`[INFO] downloader exited normally.`

`no license` was searched for in `isd_download.exe` as a plain ASCII/UTF-8 string and
**not found** there; its emitting component was not identified. It may come from a
loader blob or a device-side response. Left open.

## 9. Post-flash Windows enumeration (read-only checks)

```
Get-PnpDevice | ? InstanceId -match 'VID_4C4A'   -> all Present = False
Test-Path 'D:\'                                  -> False
USB Serial Device (COM6)                        -> VID_043E (NOT Jieli)
historical USB\VID_4C4A&PID_2342                 -> UBOOT entry from during download
```

Physical USB replug did not restore the device.
