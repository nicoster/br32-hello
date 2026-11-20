# 让杰理 AC6956C8 (BR23) 拼音机进入 USB 下载模式（BR23 UBOOT1.00, VID 4C4A）
2026-11-13 北京时间整理。只做了资料调研，没有刷写、没有接设备。

## 方法 A：软件触发（设备能正常开机时，首选）
- 原理：固件开着 USB 从机（U 盘/MSC）时，电脑发一条杰理私有的 SCSI 命令，固件就会自己复位进 ROM 下载模式，重新枚举成 `BR23 UBOOT1.00`。
- 命令（pinyin-br23-restore 实测）：**CDB = `FC 0A` + 14 个 `FF`（共 16 字节），data-in 16 字节**。这条在 loader 协议里叫 GET_ONLINE_DEVICE。
  - br23core.py `soft_trigger()`："向固件 UDISK 发 0xFC0A，促使其复位进 UBOOT1.00"，然后最多等 40 秒重新枚举。
  - `cmd_prepare_cdb()`：`cdb = cmd.to_bytes(2,'big') + args`，不足 16 字节用 `0xFF` 补齐。
  - 来源：https://github.com/xiayang0521/pinyin-br23-restore （br23core.py；README 写着"无需拆机、无需额外下载器"）
- 设备那边要做的：开机后让它进"固件 USB 模式"。使用说明原话是"正常开机后按设备的 USB 键"。具体哪个键、哪个菜单，原文没写清楚，**待实测**。在电脑上看到 VID 4C4A 的 U 盘（产品名 UDISK/DEVICE）就算进去了。
- 注意（同一仓库实测）：BR23 loader 里别发 0xFC15 / 0xFC16 / 0xFC09，会挂死 USB。
- lztttt 的一键工具（isd_download）宣称"自动进入下载模式，无需手动操作"，推测是同一个机制。
- 官方文档"设备进入升级模式方法 4"：固件开了 USB 从机，运行中就能直接下载。来源：https://doc.zh-jieli.com/AC82/zh-cn/master/getting_started/preparation/usb_updater.html

## 方法 B：flash 里没有有效程序时自动进入
- ROM 启动 flash 失败（空片或固件无效）时会自动进 USB 下载模式。kagaimiq how-to-enter-uboot.md 和杰理官方文档的"方法 1"都这么说。
- AC6956C8 用的是芯片内置 flash，"短接外置 flash 的 MISO 到 GND"那一招用不了。

## 方法 C：USB_KEY 握手（变砖时用，相当于强制升级工具/自制 dongle）
权威来源 kagaimiq：https://kagaimiq.github.io/jielie/isp/usb/usb-key.html
- key = **0x16EF**（二进制 0001 0110 1110 1111），**MSB 先发**。**D+ 是时钟，芯片在 D+ 上升沿采样；D- 是数据**。时钟约 50 kHz，要求不严，但不能太快（芯片是软件接收）。
- **芯片上电期间要一直重复发**。芯片收到后会把 **D+ 和 D- 同时拉低约 1–2 ms** 作为应答。这时就停发、释放两根线（改成高阻）。
- 检测应答：芯片有 15 kΩ 下拉，MCU 内置上拉太弱会误判。建议外接 **≤4.7 kΩ** 强上拉；或者像 xiayang 那样，改成检测之后的 D+ 上拉（soft-connect）。
- 应答之后芯片会拉高 D+，靠 SOF（每 1 ms 一个下降沿）来校准晶振；BR23 好像只试 3 次（kagaimiq 自己也标了 "verify"）。两种做法：
  1. 马上把总线切到电脑，电脑最好走独立的 USB 控制器或 USB2.0 hub，避免别的全速/低速设备干扰；
  2. dongle 自己在 D+ 上打**间隔严格 1 ms 的负脉冲**，一直打到芯片把 D+ 放下来，再接电脑。
- 注意：kagaimiq 仓库 docs/how-to-enter-uboot.md 的**正文**写成了"D- 是时钟、D+ 是数据"，但它的**波形图**和官网 usb-key 页都是 D+ 时钟、D- 数据。已在拼音机上实测成功的 xiayang 代码也是 **D+ 时钟、D- 数据**，以这个为准。https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/how-to-enter-uboot.md

### 本机实测成功的实现：xiayang0521/esp32c3-jl-unbrick（README 写"已实物测试刷机成功"）
https://github.com/xiayang0521/esp32c3-jl-unbrick/blob/main/firmware/esp32c3_jl_unbrick_supermini/esp32c3_jl_unbrick_supermini.ino
- 接线：GPIO4→D+（绿线），GPIO5→D-（白线），GND 共地；**VBUS 不接 C3**，设备用 5V 充电头单独供电。
- 发 key（原代码）：
  ```c
  gpioHi(PIN_DP); gpioHi(PIN_DM); delayMicroseconds(20);   // 空闲
  for (int i = 15; i >= 0; i--) {
    if ((0x16EF >> i) & 1) gpioHi(PIN_DM); else gpioLo(PIN_DM);
    delayMicroseconds(3);                    // 数据建立
    gpioHi(PIN_DP); delayMicroseconds(9);    // 时钟高（上升沿采样）
    gpioLo(PIN_DP); delayMicroseconds(8);    // 时钟低
  }
  gpioHi(PIN_DP); gpioHi(PIN_DM);
  ```
  一位约 20 µs（≈50 kHz），一帧约 340 µs。
- 等应答：两线都设成高阻 INPUT。300 µs 内 D+ 必须变低（芯片下拉或应答），否则判未命中。然后在 6 ms 窗口里检测"D+ 持续高 ≥600 µs"，看到就是 soft-connect，算握手成功。没命中就回到发 key，循环。
- 喂 SOF：D- 高阻；每 1 ms 把 D+ 拉低 80 µs 再放成高阻，**持续 3 秒**。
- 操作顺序：设备插 5V 充电头 → 灯常亮（锁定成功）→ **设备不能断电**，拆掉 GPIO4/5 → 设备立刻改插电脑 → 出现 `BR23 UBOOT1.00`。拆线、换插头的时候一断电就前功尽弃。
- 他们配套的 restore_factory.py 提示"先用 SuperMini 救砖器让拼音机进入下载模式，并拆掉 GPIO4/GPIO5"。说明书里提到的 Pico 救砖手册 `救砖/救砖完整手册.md` **没有公开**。

## 已确认 vs 推断
- 已确认（有源码，作者声称在本机实测）：0xFC0A 软触发；USB_KEY 0x16EF 的时序、接线和流程。
- 推断/待测：stock v1.0.94 具体怎么进"固件 USB 模式"（"USB 键"指什么）；开机按键组合——**没找到任何资料**；BR23 的 SOF 重试次数。
