# `flash_hello.bat.as-flashed`

Reconstruction of the launcher **as it was when the device was flashed** on 2026-11-19.
The `flash_hello.bat` currently in `hello-flash/` was edited afterwards (two switches
added) and has never been run — see [FLASH.md §B](../FLASH.md).

The banner, the `[INFO] downloader exited normally.` line and the `Expected log: ...`
line in this reconstruction are confirmed verbatim by the captured terminal output in
[`logs/flash_hello_20261119.log`](../logs/flash_hello_20261119.log).

This reconstruction is **908 bytes**, which matches the size recorded for
`flash_hello.bat` in the directory listing taken before the edit. Diffing it against the
current `hello-flash/flash_hello.bat` (1,219 bytes) yields exactly four added `REM` lines
plus the two added switches — nothing else changed. So the `isd_download.exe` command
line below is exact:

```
isd_download.exe -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -key key.txt -reboot 2500
```

Missing versus the SDK official / known-good command: `-tonorflash` and `-format all`.
That is why the log shows `ERASE MODE : NONE`.
