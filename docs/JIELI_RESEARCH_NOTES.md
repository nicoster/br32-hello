# 拼多多 35 元《拼音学习机》/ 杰理 AC695N(BR23) 外部资料研究笔记

- 整理时间：2026-11-19
- 范围：用户提供的立创开源硬件、杰理官方文档、key 机制文章、强制下载器方案。
- 原则：只记录能从公开页面取到的内容 + 与 `C:\br23` 现有工程的对应关系；无法抓取正文的条目标注清楚，不臆测。
- 相关本地资料：
  - `workspace/pinyin-fw/REPORT.md`
  - `workspace/pinyin-fw/unbrick/notes.md`（强制进 UBOOT 的三种方法、USB_KEY 时序）
  - `workspace/pinyin-fw/hello-lcd/README.md`（ST7305 初始化序列、引脚表、显存格式）
  - `workspace/lztttt/`（4.2 寸 RLCD 电子书固件包，`firmware/key.txt`、`isd_config.ini`）

---

## 1. 设备硬件：拼多多《拼音学习机》

来源：<https://oshwhub.com/pla155/project_pyeunvkd>（标题：拼多多的口袋学习机测试平台，作者 pla155，2026-09-08，GPL 3.0）

已确认要点：

- 主控：杰理芯片，负责蓝牙和音频解码。本项目对应 **AC6956C8 / AC695X / BR23**（`lztttt/firmware/isd_config.ini` 里 `CHIP_NAME=AC695X`、`PID=AC695N_soundbox`）。
- 屏幕：**ST7305**，300×400，单色全反射 LCD；清晰细腻，是这台机器最值得玩的部分。
- 触控：**CST836U** 电容触摸，支持手势和两点触摸。
- 原机 TYPE-C 的几个“隐藏功能”（作者从抄板电路看出）：
  1. 耳机输出：虽然没有耳机孔，但设计者预留了通过 TYPE-C 输出音频的可能——拆掉 D+/D- 保护电阻，换上隔直电容，自制 TYPE-C 耳机。
  2. CC 线：推测用于耳机插入检测；补焊一个电阻可把 UART 映射到 **PB2**，输出 log。
  3. U 盘功能：通过 C 口访问**内置 TF 卡**内容，可复制教材出来，也可放入歌曲。

作者自制的测试平台：

- 99% 复刻原电路，但 PCB 排版为 DIY 留了扩展空间。
- 上下两层板设计，用 12mm 铜柱支撑；上层是屏幕模块，下层是主电路。
- 双排插针：一排母座给屏幕模块，一排弯针接逻辑分析仪；电源针故意留空，避免误插，同时也是屏信号与触控信号的分界。
- 扩展：双路功放 + 喇叭输出（默认静音，短路使能）、耳机孔（耦合电容直连 DAC）、外部 LDO、PB8 状态 LED、备用 IO、FM 输出、弹出式 TF 卡槽、USB-A 母座（接官方下载器）、PB0 双针 log 输出、杰理标准 10 按键位（丝印提供大部分信息）。
- 复刻成本标注约 ¥66（不是机器本身 35 元）。

与本地工程的关系：

- `hello-lcd/README.md` 已从 lztttt 固件逆向出 ST7305 引脚：**SCK=PB09、MOSI=PB10、CS=PC02、DC=PA10、RST=PB11、PB00/PA00 输出高**，并说明原固件用硬件 SPI2 + DMA，测试程序用 GPIO bit-bang SPI mode 0。
- 该引脚表与开源项目“逻辑分析仪双排针”的设计动机一致：就是为了抓这些信号。
- CST836U 在本地代码中只确认“没有动它”（`hello-lcd/README.md`），触摸抓包文章正文未能抓取，暂不补写细节。

---

## 2. 屏幕初始化抓包 / 触控抓包

来源：

- <https://oshwhub.com/article/article_zmcynsyu>（抓拼多多《口袋学习机》反射屏初始化逻辑，2026-09-10）
- <https://oshwhub.com/article/article_rayqrmjl>（抓包 CST836U 触摸屏，2026-09-14）

抓取状态：**正文为动态加载，WebFetch 只拿到标题和简介**。可确认的作者意图：

- ST7305 那篇原话：“手册的初始化数据绝对没问题，但是我相信，学习机厂家会为这个显示屏匹配更加合身的参数。必须抓出来看看，不然会很难受。”——即**厂家实际初始化参数与数据手册通用值不同**，需要按实机抓包。
- CST836U 那篇原话：“抓包 CST836U 触摸屏，看看这个芯片是怎么工作的。”

本地已有的等价成果（比文章简介更具体）：

- `workspace/pinyin-fw/hello-lcd/README.md` 中保存了从 lztttt 固件 `set_pixel` / 初始化流程逆向出的完整 ST7305 初始化序列（`D6 17 02; D1 01; C0 11 04; ... 21; 38; delay 10ms; 29; delay 20ms` 等），并记录了显存位格式 `(y>>1)*75 + (x>>2)`、位号 `7 - (((x&3)<<1)|(y&1))`、1=白、刷新命令 `2A/2B/2C` + 15000 字节。
- 结论：这篇开源文章的方向与本地逆向结果一致；若以后要核对原厂参数，优先看本地 README，不必重新抓包。

---

## 3. 自制杰理强制下载器

### 3.1 杰理强制下载器 V3.0

来源：<https://oshwhub.com/pla155/project_ehhtaagt>（2026-03-29 创建，2026-11-03 更新，GPL 3.0）

硬件：

- 早期版本已能强制 AC690N / AC692N 系列进入 ISD 模式，通过 PC USB 下载。
- V3 是“阉割版”：删除电源共模电感、USB 信号共模电感、USB TVS、TPS2561A 电源管理；改为 **P-MOS + 限流电阻**。代价：一些目标板因电容过大导致识别能力下降。
- USB 适配方式与官方相反：下载器上用 **USB-A 公头插电脑/Hub**，输出用 **USB 母头**接各种成品线；另留杜邦针。
- 带 CH340G 串口（10 pin，线序与 DB9 RS232 一致，第 10 针是 117-33 LDO 输出）。
- 主控可为 **STC15F100W**；2026-09-06 增加 **AI8G1K08A-8PIN** 固件，完全兼容原 PCB、更容易买（但对 AC696/636 支持不好，慎用）。
- V3 与 V2 硬件不兼容：LED/按键 GPIO 调换；按键在 **P31**，不支持沿触发中断，软件完全重构。V3 固件仅 342 字节。不能用 V2 固件直接烧。

软件/时序（关键）：

- 大电容目标板问题：500ms 掉电不足。V3 改为 **2500ms 延时 + 10000 次魔幻字输出**，给操作留足时间，也允许上电后按开机键再进入下载。
- 2026-08-26 的 `ISD_V3_M1.HEX`：掉电时间从固定 2.5s 改为 **250ms + 用户按键保持时间 + 250ms**，改善体验。
- 灯语：绿灯亮=供电正常；红灯慢闪 1.25Hz=待机；红灯快闪 5Hz=发送魔幻字；红灯常亮=已联机等待烧录。按键只做状态切换：待机时按下联机，联机时按下待机。
- 支持芯片家族（作者列出并标注实测）：
  - 蓝牙音频：**br17/AC690N（实测）**、br20/AC691N（实测）、br21/AC692X、br22/AC693N、**br23/AC695X（实测）**、br25/AC696X（实测）、br28/AC701N（实测）、br30/AC697X（实测）、br34/AC698N、br36/AC700X 等。
  - 其他：AC6321/AC6323A4/AC630N/AC635N/AC636N、AC4100、AC460X 等。
- 附件：`ISD_V3.hex`、`ISD_V3_M1.hex`、`ISD V3(AI8G1K08专用).hex`、`随便聊聊杰理的ISD.pdf`。

### 3.2 二合一下载器 V3.0 plus

来源：<https://oshwhub.com/pla155/project_wnuwxedi>（2026-10-17，GPL 3.0）

- 目标：ISD 烧录 + 串口调试二合一。
- 必须配一个 USB Hub；作者用 **CH344**，因为 STT 的 Hub 在串口打开时会干扰 ISD 识别，导致联机失败。
- USB 转串口用 **CH340E**（小体积）；USB 切换开关用 **FSUSB30**；主控仍是 **STC15F104**（也可用 STC8K1G）。
- RX/TX 之间预留 220Ω 电阻位，兼容友商串口烧录方式。
- 整改了电源路径，解决早期版本电源波动导致串口下线的问题。
- 固件统一到 V3.0 项目页面；**下载固件要匹配自己的单片机型号**。

用户给的两颗便宜芯片对应：

- FSUSB30：USB 2.0 高速 USB 开关，用于 DM/DP 在“下载器 ↔ 目标板”和“PC ↔ 目标板”之间切换。
- STC15W101 / STC15F104 / AI8G1K08A：低成本 MCU，跑 USB_KEY 状态机。

### 3.3 USB_KEY 强制进入下载模式的通用流程

（用户提供的“大白话说说怎么自制一个杰理强制下载器”，与 `workspace/pinyin-fw/unbrick/notes.md` 方法 C 一致）

普通方案：

1. 下载器断开 CPU 与 PC 的联系：断开 CPU 电源、断开 DM/DP。
2. 下载器接到 CPU 的 DM/DP，并给 CPU 上电。
3. 立刻在 **DP 线发 50kHz 时钟脉冲**，同时在 **DM 线发 0x16EF**（`0001 0110 1110 1111`），MSB 在前，上升沿有效。
4. 发完一组 USB_KEY 后，把 DM/DP 拉高。
5. 检测 DM/DP：若仍为高，回到第 3 步继续发。
6. 若任一线变低，说明 CPU 已中断正常启动过程。
7. 立刻断开下载器与 CPU 的 DM/DP，把 CPU 的 DM/DP 接到 PC。
8. 完成。

抗干扰 / 与 Hub 共享方案（在第 6 步后插入）：

7. 等待 DP 变高。
8. 向 DP 精确发送**相隔 1ms 的负脉冲**（喂 SOF）。
9. 等待 DP 高电平，否则回到第 8 步。
10. 再切换到 PC。

重要更正（本地 `unbrick/notes.md` 已记录）：kagaimiq 文档正文写成“D- 时钟、D+ 数据”，但波形图、杰理官网 usb-key 页、以及实测成功的 xiayang esp32c3-jl-unbrick 代码都是 **D+ 时钟、D- 数据**，以后者为准。按键/上电时序：设备先接 5V 供电，灯常亮后再拆 GPIO、改插电脑，过程中不能断电，否则前功尽弃。

### 3.4 官方的进下载模式方法

来源：<https://doc.zh-jieli.com/AC82/zh-cn/master/getting_started/preparation/usb_updater.html>

杰理官方列出 4 种：

1. 未烧录过有效固件的新片/新 FLASH，插 USB 自动进下载模式。
2. 外置 FLASH 芯片：短接 FLASH 的 MISO 到 GND 后上电，再取消短接。
3. 内置 FLASH 芯片：用杰理强制升级工具（通过代理商申请或官方淘宝购买）。
4. **固件中打开了 USB 从机模式时，设备运行过程中即可直接下载**。

第 4 条就是本项目 `load_ram.py` / `br23_tool.py` 使用的软触发 `0xFC0A + 14×FF`（GET_ONLINE_DEVICE），也是 `isd_download.exe` 宣称“自动进入下载模式”的机制。

---

## 4. 杰理 key / efuse（对本项目最关键）

来源：

- <https://m.elecfans.com/article/1926605.html>
- <https://www.sohu.com/a/606091761_121433218>（同文转载）

要点：

- key 文件本质上是**密码文件**，用来加密芯片/固件。
- 由杰理分配给代理商，分配后固定、不可修改；一旦烧进芯片，**不可修改、不可删除**。
- 只能通过**一拖二**或**一拖八**量产烧写器写入芯片控制器（不是普通用户随便能写）。
- 架构原因：杰理 SoC = 控制器（杰理自研，带 OTP，引导代码）+ 外购 SPI NOR Flash（存用户程序）。为降成本把程序放外部 Flash，为防止开盖读出 Flash bin 被破解，就用 key 加密最终固件bin；读出密文也没用。
- 早期虚拟存储映射有 bank 切换，现在有虚拟存储映射后不再需要手动切 bank。
- 典型报错：
  - `错误:KEY不匹配!!`
  - `芯片没有被烧写过KEY，请删除“-key参数”`
  - `ERROR: Failed to parse device info, error info:ERR KEY`
  - 含义：目标芯片没有烧过 key，而工程里带了 `-key` 参数；去掉 `-key` 即可。

用户自己补充的实操判断：

1. 早年 AC690x 没有 key 限制，不需要 key 文件。
2. 新买的空 IC 不需要 key 文件（需向卖家问清楚）。
3. **购买成品板二次开发，一定要匹配的 key 文件**。不要侥幸——商品板出货前会 trim 晶体匹配电容和 LDO 电压，顺手把 efuse 烧了。

对 `C:\br23` 的直接含义：

- `workspace/lztttt/firmware/key.txt`（72 字节）就是 lztttt 固件的 key。`flash_only.bat` 和 `一键工具.py` 都会带 `-key key.txt`。
- 如果这台拼多多学习机的 efuse/key 与这个文件不匹配，`isd_download.exe` 会报 `ERR KEY` / `KEY不匹配`，或者刷进去也无法正常解密启动。**刷机前必须确认 key 匹配**；若芯片本来没烧 key，应去掉 `-key` 参数再刷。
- 不要试图用“读 Flash bin”来备份/还原 key：Flash 内容可能是加密的，key 在控制器 efuse 里。

---

## 5. 开发环境与官方/社区资料入口

### 5.1 杰理官方开发环境

来源：<https://doc.zh-jieli.com/Tools/zh-cn/dev_tools/dev_env/index.html>、<https://doc.zh-jieli.com/Tools/zh-cn/dev_tools/build_download/index.html>

- Windows：SDK 默认用 **Code::Blocks**。三步：装 Code::Blocks → 打开再关闭（生成基础配置）→ 装最新版杰理 Windows 工具链。
- Linux：SDK 支持 **Makefile** 编译；`download.sh` 改造后可生成 `.fw`，但**不支持下载到设备**。
- macOS：**没有工具链支持**。
- 编译入口：Code::Blocks 工程 `.cbp`、Makefile、VSCode 配置。
- 本地已有：`tmp/jl-tc/jieli-linux-toolchains-20260730.1.tar.xz`，MD5 `eb6b1a897e2fda73d166a4f00c10353a`；交叉编译 `clang -target pi32v2 -mcpu=r3`。与官方“Linux 只能编译”一致——下载要靠 Windows 的 `isd_download.exe` 或 USB loader。

### 5.2 杰理 Gitee 组织

<https://gitee.com/organizations/Jieli-Tech/projects>

公开仓库以各系列 SDK 为主，例如：

- `fw-AC63_BT_SDK`：支持 AC631N/AC635N/AC636N/AC637N/AC632N，兼容 AC69 系列（不含 audio）。
- `fw-AD15N`：AD14N/AD15N/AC104N/AD17N/AD18N 通用 MCU SDK。
- `fw-AC79_AIoT_SDK`、`fw-AC792_SDK`、`fw-AW31N_BLE_SDK` 等新型号。

首页未直接看到 AC695N/BR23 的公开 SDK；本项目已有 SDK 摘录在 `tmp/jl-sdk/`、`tmp/jieli-sdk/`，以本地为准。

### 5.3 云信 YunThinker

<https://doc.yunthinker.com/#/>

- 杰理一级代理商的文档站：快速上手、常用工具、选型手册、硬件设计、测试 Demo、生产与测试。
- SDK 仓库：<https://gitcode.com/yunthinker>；B站教程、飞书知识库链接见该页。
- 作为中文补充资料源，优先级低于杰理官网。

### 5.4 AC690N 系列经验文章

- <https://oshwhub.com/article/jerry-ac690n-fangfang>：一个 <100 字节的最小系统——初始化栈、关看门狗、把 UART0 映射到 PC2(TX)、定时发字节；纯 SRAM 运行，体现“编译零等待、测试零磨损”。AC6904 可参考图片位置引出 PC2。
- <https://oshwhub.com/article/jerry-ac690n-compile2burn>：讲从 C 文件到固件镜像再到手动烧录的完整过程。**正文动态加载，只抓到简介**，待有浏览器环境时再补。
- 这两篇的思路与本项目 `hello-ram` / `hello-lcd` 的 RAM 加载路线一致：先做最小系统验证，不碰 Flash。

---

## 6. 对当前刷机任务的行动清单

1. **先确认 key**：确认这台机器的 efuse key 是否与 `lztttt/firmware/key.txt` 匹配。若不匹配或芯片无 key，去掉 `-key key.txt` 后再刷，否则会 `ERR KEY`。
2. **备份优先**：刷 lztttt 前用 `br23_tool.py` 菜单 1 做整片 1MB 只读备份（本机需管理员 + 设备回到原厂 UDISK 模式；若还在跑 RAM 程序，先断电复位）。
3. **只刷 Flash**：用 `C:\br23\workspace\lztttt\flash_only.bat`（纯英文 ASCII 启动器），它不格式化 TF 卡、不拷字库、不建索引。
4. **进下载模式**：优先用软件方式（`0xFC0A` 软触发 / `isd_download.exe` 自动进 UBOOT）；失败时用自制下载器或强制升级工具做 USB_KEY 硬件触发。
5. **失败回滚**：`br23_tool.py` 菜单 2 恢复备份，必须输入完整 `YES`；工具会写后校验。

---

## 7. 原始链接清单

| 类别 | 链接 | 抓取状态 |
|---|---|---|
| 原板/测试平台 | https://oshwhub.com/pla155/project_pyeunvkd | 正文完整 |
| ST7305 抓包 | https://oshwhub.com/article/article_zmcynsyu | 仅标题/简介 |
| CST836U 抓包 | https://oshwhub.com/article/article_rayqrmjl | 仅标题/简介 |
| 强制下载器 V3 | https://oshwhub.com/pla155/project_ehhtaagt | 正文完整 |
| 二合一 V3 plus | https://oshwhub.com/pla155/project_wnuwxedi | 正文完整 |
| FSUSB30 | https://item.taobao.com/item.htm?id=873179293506 | 商品页，未抓取 |
| STC15W101 | https://item.taobao.com/item.htm?id=893387222418 | 商品页，未抓取 |
| AC690N fangfang | https://oshwhub.com/article/jerry-ac690n-fangfang | 正文完整 |
| compile2burn | https://oshwhub.com/article/jerry-ac690n-compile2burn | 仅标题/简介 |
| 官方开发环境 | https://doc.zh-jieli.com/Tools/zh-cn/dev_tools/dev_env/index.html | 正文完整 |
| 官方编译下载 | https://doc.zh-jieli.com/Tools/zh-cn/dev_tools/build_download/index.html | 正文完整 |
| 官方强制升级 | https://doc.zh-jieli.com/AC82/zh-cn/master/getting_started/preparation/usb_updater.html | 正文完整 |
| Gitee 组织 | https://gitee.com/organizations/Jieli-Tech/projects | 列表完整 |
| YunThinker | https://doc.yunthinker.com/#/ | 正文完整 |
| key 原理（电子发烧友） | https://m.elecfans.com/article/1926605.html | 正文完整 |
| key 原理（搜狐转载） | https://www.sohu.com/a/606091761_121433218 | 正文完整 |
