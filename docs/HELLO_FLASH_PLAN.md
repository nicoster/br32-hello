# 基于 SDK 写 hello world（刷 Flash，且刷完可再刷）——需求分析

2026-11-19 整理。只分析，未动设备。

## 一、需求拆解

| 项 | 内容 |
|---|---|
| 显性需求 | 基于（官方）SDK 写一个 hello world 固件 |
| 交付形式 | 刷进设备内部 Flash，上电即运行（不是 RAM 加载） |
| 隐性硬约束 | **刷完之后必须还能再次刷机** |
| 真正的难点 | 不在 hello world，而在"可再刷"这一条 |

关键认知：**"刷完还能再刷"不是刷机本身的属性，而是 app 固件的属性。**烧录器只负责这一次写入；下一次能不能刷，取决于 flash 里跑的那个程序给不给"入口"。

## 二、"刷完还能再刷"的三条通路

来自 `unbrick/notes.md`（本项目已验证/调研过）：

| 通路 | 原理 | 谁提供 | 评价 |
|---|---|---|---|
| **A. 软触发 0xFC0A** | app 实现 USB 从机（U 盘/MSC），电脑发杰理私有 SCSI 命令 `FC0A`，app 自行复位进 UBOOT，重新枚举成 `BR23 UBOOT1.00` | **运行中的 app** | 常规通道。stock v1.0.94 和 lztttt 都有；`br23_tool.py` 的"进入 UBOOT"就是用它 |
| **B. 无有效固件自动进** | ROM 启动 flash 失败（空片/固件无效）时自动进 USB 下载模式 | 芯片 ROM | 只能救"已经坏了"的，不能当常规通道 |
| **C. USB_KEY 强制下载** | 上电期间在 D+ 打 50kHz 时钟、D- 发 `0x16EF`（MSB 先），打断芯片正常启动，强制进下载模式 | **外部硬件** | 与 app 内容无关的保底手段。已有实测方案：xiayang0521/esp32c3-jl-unbrick（ESP32 SuperMini，源码在手） |

结论：本需求等价于——

> 你的 hello world **要么自带 USB 从机 + 0xFC0A 响应（通路 A）**，
> **要么接受每次再刷都需要 USB_KEY 硬件兜底（通路 C）**。

## 三、实现路线

### 路线 1：官方 AC695N SDK（推荐）

lztttt 本身就是 AC695N SDK（BR23, SOUNDBOX 方案，`PID=AC695N_soundbox`）的产物。走这条路，USB 设备栈 + 升级协议在闭源库（liba/cpu.a）里现成，只要不在板级配置里砍掉 USB slave，"可再刷"就是免费附赠。

步骤：

1. 取 AC695N SDK（gitee Jieli-Tech 或 pkgman.jieliapp.com；本机目前只有提取出的碎片：`tmp/jl-sdk/` 的头文件、board_ac695x_demo、download 脚本，**没有完整 SDK 和 .a 库**）。
2. 板级配置基于 `board_ac695x_demo_cfg.h` 裁剪：保留 USB slave + update 模块；UART 走 PB04 @ 1M（已在 hello-ram/hello-lcd 上验证）。
3. app 主任务只做 hello world（串口打印；屏幕可用 hello-lcd 已逆向的 ST7305 驱动）。
4. 编译：官方 Linux 工具链 tarball 已在 `tmp/jl-tc/`（pi32v2 clang，hello-lcd 就是用它编的）；SDK 的 download.c 支持 `__SHELL__` Linux 分支。**注意：Linux 工具链在 Windows 上需要 WSL，或另下 Windows 工具链（C:\JL\pi32）。**
5. 烧录：app 用自己编译的；**uboot.boot / key.txt / isd_config.ini 直接用 lztttt 的**（见"坑"第 5 条）。

产物形态：SDK app 是 XIP 运行（`ENTRY=0x1E00100`，flash 映射区），不是 RAM 程序那种 0x12000 加载。`-boot 0x12000` 表示 app 放在 flash 偏移 0x12000（uboot 占 0x0–0x12000）。

成本：需要下载完整 SDK；首次跑通 SDK 工程的编译链；闭源库导致 app 体积大（lztttt 的 app 860KB）。

### 路线 2：自研 mini-SDK（hello-lcd 的 flash 版）

把现有 bare-metal 程序改成 flash 布局，从"UBOOT 跳转进 RAM"改为"uboot 正常引导 app"。启动环境差异要自己摸（时钟、栈、入口）。

- 要满足"可再刷"，必须**自己实现 USB 设备栈**：枚举 → MSC/U 盘 → INQUIRY `BR23 UDISK` → 响应 `FC 0A` 复位进 UBOOT。这是整条路线 90% 的工作量，等于重写 SDK update 模块。
- 变通：不带 USB，靠通路 C 硬件兜底（ESP32 SuperMini dongle，材料你已研究过：fsusb30 / STC15W101）。

评价：能学到最多，但为 hello world 不值；适合作为后续深入课题。

### 路线 3（探索性）：app 直接跳回 flash 里的 uboot 升级分支

uboot 常驻 flash 0x0–0x12000 且同在映射区；理论上 app 可以直接调 uboot 的代码/入口进升级模式，省掉整个 USB 栈。手上有 `rom.lst` / maskrom_stubs.ld / stock.lst 逆向资料支撑研究。风险：入口约定未知，纯逆向活。**不作为首选项。**

## 四、必须处理的坑

1. **key / efuse**：商品板 efuse 必烧 key。烧录必须带 `-key key.txt`，且必须用 **lztttt 附带的 key**（已匹配这台机器；之前那次 433 失败发生在写入阶段，没有报 ERR KEY，说明 key 阶段已通过）。芯片没烧 key 才能去掉 -key；不要赌。
2. **管理员权限 + USB 直通**：上次 `isd_download` 报 `error 433 / Device offline`（写到 block 13 掉线）就是从我这边非管理员环境跑的。烧录动作应在**用户自己的管理员终端**执行；我这边的沙箱对 USB 设备直通有限制。
3. **当前 Flash 可能是半写入状态**：上次失败已写入约 13 个块（可能是 uboot 区开头）。动手前先用 `br23_tool.py` 只读确认设备当前状态；有全片备份可回滚。
4. **ENTRY 差异**：RAM 程序（0x12000）与 SDK app（0x1E00100 XIP）是两种世界。用 SDK 自建 app 时，isd_config.ini 的 `ENTRY`、`FLASH_BIN_CNT` 要与 SDK 产出对齐。
5. **isd_config.ini 直接抄 lztttt 的**：`UTTX=PB04`（uboot 串口）、`UTBD=1000000`、`RESET=PB01_08_0`（PB01 长按 8 秒低电平复位）、`SPI=2_3_0_0`、`EX_FLASH=PA03_1A_NULL`、`VLVD=4`——这些板级参数已证明匹配这台机器，别自己发明。
6. **回滚资产已在手**：`pinyin-fw/backup/stock_flash_20261113_110444.bin`（1MB 全片原厂镜像）→ `br23_tool.py` 菜单 2 可恢复。

## 五、建议的最小验证闭环（先证明"可再刷"，再谈功能）

```
1. （用户管理员终端）br23_tool 只读确认设备当前状态
2. 编译 SDK hello world
3. 用 lztttt 的 uboot + key + isd_config 烧入自己的 app
4. 验证：上电 → D: 出现（UDISK）→ hello 输出可见
5. 验证再刷：br23_tool 发 0xFC0A → BR23 UBOOT1.00 → 再刷一次（哪怕是同一份）
   → 闭环成立，之后随便迭代
6. 任何异常 → 用全片备份恢复
```

## 六、待确认

- SDK 获取渠道（gitee Jieli-Tech / pkgman.jieliapp.com 下载中心）
- 编译环境：WSL（用现有 Linux 工具链）还是装 Windows 工具链
- hello world 的输出形式：串口日志（PB04 1M）还是 ST7305 屏幕（驱动已逆向）
- TF 卡 / U 盘挂载要不要保留（影响 USB slave 配置）
