# 详细设计：AC695N SDK hello world（Flash 常驻、可再刷）

2026-11-19。上游文档：`HELLO_FLASH_PLAN.md`（需求分析）。本文件为实施级设计，未开始编码。

---

## 1. 目标与验收标准

| 目标 | 内容 |
|---|---|
| D1 | 基于 AC695N SDK（BR23 / SOUNDBOX case）构建最小 hello world 固件 |
| D2 | 经 `isd_download` 刷入设备内部 Flash，上电自启动（XIP 运行） |
| D3 | **刷入后无需拆机、无需硬件，即可再次刷机**（0xFC0A 软触发） |
| D4 | 任意时刻可回滚（原厂全片备份 + `br23_tool.py` 恢复） |

可测试的验收标准：

- **A1** 烧录日志出现 `ERASE MODE : NONE` → `下载完毕` → `正在复位`，退出码 0。
- **A2** 上电后串口 PB04 @ 1 Mbaud 周期输出 hello 心跳；设备管理器出现 `VID_4C4A`；插 USB 出现 `D:` 盘（UDISK 模式）。
- **A3（核心）** `br23_tool.py` 发 0xFC0A → 设备重新枚举为 `BR23 UBOOT1.00` → **第二次烧录成功**（重复 A1）。闭环成立。
- **A4** `br23_tool.py` 菜单 3（查看设备信息）正常返回。
- **A5**（可选演练）用备份恢复原厂固件成功。

---

## 2. 总体架构

### 2.1 Flash 布局（1 MB 内置 flash，沿用 lztttt 已验证配置）

| 区域 | 位置 | 内容 | 来源 | 烧录时操作 |
|---|---|---|---|---|
| uboot | 0x0 – 0x12000 | `uboot.boot`（8320 B） | **lztttt**（本板已验证） | 写入 |
| app | 0x12000 起 | `app.bin` | **自己编译** | 写入 |
| res | 工具自动分配 | tone.cfg / cfg_tool.bin / eq_cfg_hw.bin | lztttt | 写入 |
| BTIF | AUTO，4K | 出厂信息 | — | `OPT=1` 不操作 |
| LRIF | AUTO，4K | 歌词区 | — | `OPT=1` 不操作 |
| VM | 32K | 系统参数（含升级标志） | — | `OPT=1` 不操作 |

烧录命令**不带 `-format all`** → `ERASE MODE : NONE` → VM/BTIF 保留。升级标志位于 VM（0xFC0A 响应后由固件置位、复位，uboot 看到即停在 UBOOT）。

### 2.2 运行时启动链与再刷链路

```
上电 → ROM → flash uboot（检查 VM 升改标志 / USB_KEY 握手）
     ├─ 无升级请求 → 跳 app（ENTRY=0x1E00100，XIP）
     │                → SDK 系统初始化（setup.c / board_*_init）
     │                → app 框架 → hello 线程 + USB slave（U 盘模式）
     └─ 有升级请求 → 停在 UBOOT（BR23 UBOOT1.00）等 isd_download

再刷：PC 端 br23_tool / isd_download 向运行中固件的 UDISK 发 SCSI 0xFC0A
      → SDK USB 栈 update 模块置 VM 标志并复位
      → 设备重新枚举为 BR23 UBOOT1.00 → 开始写入
```

### 2.3 现有资产复用表

| 资产 | 位置 | 本设计中的用途 |
|---|---|---|
| SDK 碎片（头文件 / board demo / download.c / Makefile.br23） | `tmp/jl-sdk/`、`tmp/tf-flag-pack-staging/sdk/` | SDK 结构与板级配置模板（demo 板配置不可直接用：SD 口、串口脚都不同） |
| Linux 工具链 tarball | `tmp/jl-tc/jieli-linux-toolchains-20260730.1.tar.xz` | 编译（hello-lcd 已用它编过，MD5 `eb6b1a89...`） |
| ST7305 / UART / WDT 驱动 | `pinyin-fw/hello-lcd/src/` | M2 屏幕阶段移植 |
| 烧录全家桶（uboot.boot / key.txt / isd_config.ini / res / isd_download.exe） | `workspace/lztttt/firmware/` | 除 app.bin 外全部沿用 |
| 验证 / 再刷 / 回滚工具 | `pinyin-fw/src/pinyin-br23-restore/br23_tool.py` | 验收 A3 / A4 / 恢复 |
| 原厂全片备份 | `pinyin-fw/backup/stock_flash_20261113_110444.bin`（1 MB） | 回滚兜底 |
| USB_KEY 救砖方案 | esp32c3-jl-unbrick（源码已调研，`unbrick/notes.md`） | 硬件保底 |

---

## 3. SDK 获取与工程组织

### 3.1 获取

- 渠道一：gitee `Jieli-Tech` 组织（用户已收藏链接）；
- 渠道二：`pkgman.jieliapp.com` 下载中心（工具链即来自此处）；
- 要求：**AC695N / BR23 SDK，SOUNDBOX case**（与 lztttt 同源：`PID=AC695N_soundbox`、`SDK_TYPE=SOUNDBOX`、`CHIP_NAME=AC695X`）。
- 芯片版本兼容性由 `isd_config.ini` 的 `SUPPORTED_LIST=A,B,D,E` 覆盖。

### 3.2 工程组织

SDK 工程是"改板级 + apps"模式，不新建独立工程，在 SDK 树内做最小侵入改造：

```
hello-sdk/                     ← 我们的仓库（pinyin-fw/hello-sdk/）
├── SDK/                       ← 官方 SDK 原树（git submodule / 直接解压，尽量不改）
├── patches/                   ← 对 SDK 的全部改动（板级 + app）
│   ├── board_hello_cfg.h     ← 新板型配置（§4.1）
│   ├── board_hello.c
│   ├── hello_app.c           ← hello 线程（§4.2）
│   └── app_config.diff
├── hello-flash/               ← 烧录包（§5.3）
│   ├── app.bin               ← 自编产物
│   ├── uboot.boot / key.txt / isd_config.ini / tone.cfg / cfg_tool.bin / eq_cfg_hw.bin
│   │                          ← 全部复制自 lztttt/firmware/
│   ├── isd_download.exe
│   └── flash_hello.bat       ← 纯 ASCII 英文（吸取乱码教训）
├── verify/                    ← 验收脚本（调 br23_tool）
└── README.md
```

改动全部以"新增板型 `CONFIG_BOARD_BR23_HELLO`"方式落地，不覆盖 SDK 自带 demo 板，随时可回退到 SDK 原始构建。

---

## 4. 模块设计

### 4.1 板级配置 `board_hello_cfg.h`（对 demo 板的改动表）

| 宏 | demo 值 | 新值 | 理由 |
|---|---|---|---|
| `TCFG_UART0_TX_PORT` | `IO_PORTA_05` | **`IO_PORTB_04`** | 本板 UART0 TX 实测为 PB04（hello-lcd 源码佐证；与 isd_config `UTTX=PB04` 一致，bootloader 与 app 串口同脚） |
| `TCFG_UART0_RX_PORT` | `NO_CONFIG_PORT` | 不变 | 仅打印 |
| `TCFG_UART0_BAUDRATE` | `1000000` | 不变 | |
| `TCFG_APP_PC_EN` | 1 | **1（必须保留）** | U 盘模式 = 再刷入口 |
| `TCFG_UDISK_ENABLE` | `ENABLE_THIS_MOUDLE` | **必须保留** | 同上 |
| `TCFG_SD0_ENABLE` | ENABLE | **0**（M1 阶段） | 本板实际用 SD1 'A' 1-bit；demo 的 SD0 'B' 与本板接线不符，先不挂卡。是否启用 SD1 见决策点 |
| `TCFG_SD1_ENABLE` | DISABLE | 0（M1） | 同上 |
| `TCFG_APP_BT_EN` | 1 | 1（保守） | 关 BT 可减体积但牵动 SDK 链路；M1 不动，M3 再裁 |
| `TCFG_APP_MUSIC/FM/LINEIN/RECORD/RTC_EN` | 1 | 逐个试关 | hello 用不到；**渐进裁剪**，编译不过就回退（风险 R2） |
| `TCFG_USB_DM_MULTIPLEX_WITH_SD_DAT0` | DISABLE | 不变 | 别把 DM 分复用出去 |
| `TCFG_SOUNDBOX_TOOL_ENABLE` / `TCFG_EFFECT_TOOL_ENABLE` | DISABLE | 不变 | 避免 COMM 配置占用 USB |
| 充电 / 低功耗 | demo 默认 | 不动 | 本机是锂电设备 |

### 4.2 hello 应用任务（方案 H1，最小侵入）

不动 SDK 的 app mode 表，在 app 启动处创建独立线程：

```c
/* hello_app.c */
static void hello_task(void *arg)
{
    int n = 0;
    while (1) {
        log_info("hello world #%d  (BR23 hello-flash, built " __DATE__ ")");
        n++;
        os_time_dly(100);          /* 1s 心跳；禁止紧循环，喂给 SDK 调度 */
    }
}

static int hello_app_init(void)    /* 挂到 app 启动钩子 */
{
    return os_task_create(hello_task, NULL, "hello");
}
```

默认工作模式设为 PC 模式（U 盘），使上电即出现 `D:`，无需按键。方案 H2（完整 `APP_MODE_HELLO`、按键切模式）留到 M3，非必须。

### 4.3 输出通道

- **串口（M1，主通道）**：走 SDK log 系统（`debug.h` 的 `log_info`），输出到 PB04 @ 1M。uboot 串口同脚同波特率（isd_config `UTTX=PB04 / UTBD=1000000`），从 bootloader 到 app 全程可观测。
- **屏幕（M2，可选增强）**：移植 `hello-lcd/src/st7305.c`（GPIO bit-bang SPI）。两个适配点：
  1. hello-lcd 的 delay 基于 UBOOT 环境时钟，SDK 下主频不同 → 刷新节拍统一改 `os_time_dly`，初始化序列中的 100 ms/50 ms 延时用 SDK 毫秒延时重校准；
  2. 引脚表原样复用：SCK=PB09、MOSI=PB10、CS=PC02、DC=PA10、RST=PB11、电源脚 PB00/PA00 拉高。
- 显存格式与初始化序列直接照抄 hello-lcd（已从 lztttt 固件逆向验证）。

### 4.4 USB 从机与升级支持（核心需求，零代码模块）

**本模块不写任何代码。** SDK 闭源库（`usb/device/msd.h`、update 模块）已实现 0xFC0A。设计上只做三件事：

1. 配置层保证 USB slave 可用（§4.1 的三个"必须保留"）；
2. 默认模式设为 PC/U 盘，保证上电即可见；
3. 验证不靠读代码，靠实测（验收 A3）。

---

## 5. 构建设计

### 5.1 工具链

- 现有：`tmp/jl-tc/jieli-linux-toolchains-20260730.1.tar.xz`（Linux pi32v2 clang/ld/objcopy，hello-lcd 已用它编过 1.1 KB 镜像）。
- Windows 上二选一（**决策点 2**）：WSL 内解压到 `/opt/jieli` 用 SDK Makefile；或另下官方 Windows 工具链（`C:\JL\pi32`）+ Code::Blocks。
- SDK 的 `download.c` 有 `__SHELL__`（Linux）分支，Linux 构建是官方支持的路径。

### 5.2 编译 → 打包流水线

```
make（CORE=pi32v2, CPU=br23, BOARD=hello, APP_CASE=soundbox）
  → sdk.elf
  → objcopy 出 text.bin / data.bin / data_code.bin（+ overlay 段）
  → 拼接为 app.bin                    ← 明文，无头部结构负担，入口由打包流程定
  →（isd_download + key.txt 加密）→ jl_isd.bin / jl_isd.fw → 写 flash
```

### 5.3 烧录包与命令

`hello-flash/flash_hello.bat`（纯 ASCII）核心命令，参数逐字沿用 `flash_only.bat`（已在本板跑通到写入阶段，失败点仅在权限）：

```
isd_download.exe -dev br23 -boot 0x12000 -div8 -wait 300
    -uboot uboot.boot -app app.bin
    -res tone.cfg cfg_tool.bin eq_cfg_hw.bin
    -key key.txt -reboot 2500
```

**打包一致性注意（风险 R3）**：isd_config.ini 的 `ENTRY=0x1E00100` 是 lztttt 工程入口。自编 app 入口由 SDK 打包流程决定。首烧前核对：若 SDK 产出的 app 入口与 0x1E00100 不一致，改用 **SDK 自带 download.bat 全流程**（它用配套 isd_config 打包），只把 `key.txt` 替换为 lztttt 的（匹配本板 efuse）。uboot 优先用 lztttt 的（同 SDK 体系、本板已验证）。

---

## 6. 烧录与验证流程（每轮固定剧本）

前置（一次性）：
1. 用户管理员终端运行 `br23_tool.py`，只读确认设备当前状态（上次 433 后 Flash 疑似半写入，见风险 R6）；
2. 确认 `backup/stock_flash_20261113_110444.bin` 在位。

每轮烧录：
```
1. [用户管理员终端] 运行 hello-flash\flash_hello.bat
   判定：ERASE MODE : NONE / 下载完毕 / 正在复位 / 退出码 0 → A1
   失败分派：
     - "ERR KEY"          → key 不匹配（R4）
     - "Device offline"/433 → 权限或 USB 掉线（R5）：管理员、换数据线/口
2. [验证] br23_tool.py 菜单 3（设备信息）→ A4
3. [验证] 上电观察：串口心跳（A2 串口项）、插 USB 出 D:（A2 U 盘项）
4. [再刷闭环] br23_tool.py 软触发 0xFC0A → 等待 BR23 UBOOT1.00 枚举
   → 立即重跑第 1 步 → A3
   （每轮开发迭代都走 1→4，闭环即"随时可再刷"的证据）
```

任何一轮失败两连击：先 0xFC0A 重试；再不行上 USB_KEY dongle（esp32c3 方案，接线与时序已在 `unbrick/notes.md` §方法 C 固化）；最终兜底 `br23_tool.py` 菜单 2 恢复全片备份。

---

## 7. 风险与对策

| # | 风险 | 对策 |
|---|---|---|
| R1 | SDK 不可得 / 版本不匹配 | 双渠道备选；`SUPPORTED_LIST=A,B,D,E` 已覆盖芯片版本 |
| R2 | 板级裁剪编译失败 | 渐进：先原样编通 demo → 再逐项改宏，每改一项编译一次 |
| R3 | 自编 app 与 lztttt 的 isd_config ENTRY/打包不匹配 | 首烧核对入口；不一致就切 SDK 官方 download.bat 全流程，只换 key |
| R4 | ERR KEY（efuse 不匹配） | 用 lztttt 的 key.txt；绝不去掉 `-key`（商品板必烧 key，不赌） |
| R5 | 433 / Device offline | 只在用户管理员终端烧录；数据线换短粗的；`-wait 300` 足够 |
| R6 | 当前 Flash 半写入状态 | 动手前先只读确认；反正有全片备份，最坏恢复 |
| R7 | hello 线程阻塞系统 | 只用 `os_time_dly` 节拍，无紧循环、无长忙等 |
| R8 | 屏幕时序在 SDK 时钟下漂移（M2） | 延时全部换 SDK 毫秒接口重校准 |

---

## 8. 里程碑

| 里程碑 | 内容 | 验收 |
|---|---|---|
| **M0 环境** | 取 SDK；工具链就位（WSL 或 Windows）；**原样编译 demo 不改一行**出 app.bin | 编译通过，产出 app.bin |
| **M1 hello-闭环** | 板级改动（PB04 串口 + 关无关外设）；hello 线程；烧录包；烧入；再刷闭环 | A1–A4 全过，**A3 闭环成立**（核心交付） |
| **M2 hello-屏幕** | 移植 ST7305 驱动，屏幕显示 hello | 屏幕出现预期画面且心跳持续 |
| **M3 收尾** | 裁剪（BT/体积）、flash_hello.bat 完善、README、可交付 | 一条命令刷入 + 一条命令再刷 |

M1 完成即满足用户需求的全部硬指标；M2/M3 为体验增强。

---

## 9. 待拍板决策点

1. **SDK 渠道**：gitee Jieli-Tech 还是 pkgman 下载中心（我先查哪个有 AC695N SDK）。
2. **编译环境**：WSL（用现有 Linux 工具链）还是装 Windows 工具链。
3. **TF 卡**：M1 是否启用 SD1（'A' 口 1-bit，本板真实接线）——默认不启用。
4. **蓝牙**：M1 保留（保守）还是直接关（减体积）——默认保留。
5. **输出优先级**：串口先行（默认）还是串口+屏幕同里程碑做。
