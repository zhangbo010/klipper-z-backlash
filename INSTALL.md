# Z 轴回差补偿插件 - 安装指南

Z 轴丝杆与螺母存在间隙，方向反转时会产生空程，本插件通过补偿消除回差影响。

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

或手动写入 `[z_backlash]` 段（见下文）。

### 一键安装脚本

脚本通过 **git clone** 拉取仓库后复制文件：

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh)
```

或先下载脚本再执行：

```bash
wget -q -O install.sh https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh
bash install.sh
```

需已安装 `git`。

### 克隆报错：RPC failed / curl 16 Error in the HTTP2 framing layer

多为网络与 HTTP/2 兼容问题，任选其一：

```bash
# 方式 A：全局改用 HTTP/1.1（一次设置，长期有效）
git config --global http.version HTTP/1.1

# 方式 B：仅本次克隆（推荐）
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
```

仍失败时，不克隆整库，用 curl 只下载文件：

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

编辑 `printer.cfg`，加入：

```ini
[z_backlash]
backlash: 0.1
# 可选
# split_pause: 0.08
# takeup_speed: 0
```

或使用 include 引入示例配置：

```ini
[include z_backlash.cfg]
```

（需先将 `config/z_backlash.cfg` 复制到与 `printer.cfg` 同目录）

### 3. 重启 Klipper

```bash
sudo systemctl restart klipper
```

---

## 不同 Klipper 路径

若 Klipper 不在 `~/klipper`，请替换为实际路径：

| 环境 | 典型路径 |
|------|----------|
| 树莓派 / Mainsail | `~/klipper` 或 `/home/pi/klipper` |
| Fluidd | `~/klipper` |
| 自定义 | 根据实际安装路径 |

示例：

```bash
cp klipper-z-backlash/klippy/extras/z_backlash.py /home/pi/klipper/klippy/extras/
```

---

## 工作原理说明

- 换向且行程足够时拆成两段真实 `move`（消隙 + 到位），多走的脉冲消除丝杆间隙；`get_position()` 不篡改坐标。
- 可选 `split_pause` / `takeup_speed` 调节两段之间的停顿与第一段速度（见 README 参数表）。
- 插件在 `load_config` 中对模块 `reload`，一般 **`FIRMWARE_RESTART`** 可加载新版脚本；若仍报配置项无效，请 **`sudo systemctl restart klipper`** 一次。

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

然后从 `printer.cfg` 中删除 `[z_backlash]` 配置段，并重启 Klipper。
