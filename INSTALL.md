# Z 轴回差补偿插件 - 安装指南

Z 轴丝杆与螺母存在间隙，方向反转时会产生空程。本插件在换向时多走一段补偿脉冲，**G-code 与 M114 的 Z 仍与指令一致**。

## 安装方式（推荐：Git）

需已安装 **git**（如 `sudo apt install git`）。

### 克隆仓库并复制文件

```bash
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
cd klipper-z-backlash
cp klippy/extras/z_backlash.py ~/klipper/klippy/extras/
```

若 Klipper 不在 `~/klipper`，请改成实际路径（如 `/home/pi/klipper`）。

可选：复制配置示例：

```bash
cp config/z_backlash.cfg ~/printer_data/config/
```

在 `printer.cfg` 中加入：

```ini
[include z_backlash.cfg]
```

或手动写入 `[z_backlash]` 段（见 [README.md](README.md) 参数表）。

### 一键安装脚本

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh)
```

### 克隆报错：RPC failed / HTTP2 framing

```bash
git config --global http.version HTTP/1.1
# 或
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
```

仍失败时，用 curl 只下载单文件：

```bash
mkdir -p ~/klipper/klippy/extras ~/printer_data/config
curl -fsSL -o ~/klipper/klippy/extras/z_backlash.py \
  https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/klippy/extras/z_backlash.py
curl -fsSL -o ~/printer_data/config/z_backlash.cfg \
  https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/config/z_backlash.cfg
```

---

## 完整安装步骤

### 1. 安装模块

```bash
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
cp klipper-z-backlash/klippy/extras/z_backlash.py ~/klipper/klippy/extras/
```

### 2. 添加配置

```ini
[z_backlash]
backlash: 0.1
# 可选
# compensation_scale: 1.0
# split_pause: 0.08
# takeup_speed: 0
```

或使用 `[include z_backlash.cfg]`（需先把示例文件复制到配置目录）。

### 3. 重启 Klipper

```bash
sudo systemctl restart klipper
```

或在控制台执行 **`FIRMWARE_RESTART`**。

---

## 不同 Klipper 路径

| 环境 | 典型路径 |
|------|----------|
| 树莓派 / Mainsail | `~/klipper` 或 `/home/pi/klipper` |
| Fluidd | `~/klipper` |

示例：

```bash
cp klipper-z-backlash/klippy/extras/z_backlash.py /home/pi/klipper/klippy/extras/
```

---

## 工作原理说明（简要）

- **换向**且 **`|ΔZ| > backlash`**：两段——第一段物理终点为 `z_phys + ΔZ`（步进长度 `|ΔZ|`），第二段再沿同向补偿；**`|ΔZ| ≤ backlash`** 时只走一段，同样用 **`z_phys + ΔZ`** 作为单段终点。
- **同向**连续移动：单段终点也是 **`z_phys + ΔZ`**（逻辑位移与物理步进一致）；若误用 `z_target` 当底层终点，在补偿后「逻辑≠物理」时会出现**少走路程**（约 `|回差|`）。
- **ΔZ 来源**：`move()` 里用 **`get_position()`** 作起点，避免与 `SAVE/RESTORE` 宏冲突。
- **归零**：`home_rails_begin`～`end` 期间不拆段、不补偿。
- **`get_position()`** 对逻辑 Z 做修正，与 G-code 一致；**M114** 仍来自 G-code 状态，本身不含补偿段。
- 插件在 `load_config` 中对模块 `reload`，一般 **`FIRMWARE_RESTART`** 可加载新版；若仍报配置项无效，请 **`sudo systemctl restart klipper`**。

---

## 验证安装

重启后，在 Klipper 控制台执行：

```
Z_BACKLASH_COMPENSATE VALUE=0.1
```

若返回 `Z backlash compensation set to 0.100 mm`，则安装成功。

---

## 卸载

```bash
rm ~/klipper/klippy/extras/z_backlash.py
```

从 `printer.cfg` 中删除 `[z_backlash]` 或 `[include z_backlash.cfg]`，并重启 Klipper。
