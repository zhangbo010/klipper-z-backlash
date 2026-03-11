# Z 轴回差补偿插件 - 安装指南

## 一键安装（推荐）

在 Klipper 主机（如树莓派）的终端中执行：

```bash
cd ~/klipper/klippy/extras && wget -O z_backlash.py https://raw.githubusercontent.com/YOUR_USERNAME/klipper-z-backlash/master/klippy/extras/z_backlash.py
```

或使用 curl：

```bash
cd ~/klipper/klippy/extras && curl -sSL -o z_backlash.py https://raw.githubusercontent.com/YOUR_USERNAME/klipper-z-backlash/master/klippy/extras/z_backlash.py
```

> 将 `YOUR_USERNAME` 替换为实际的 GitHub 用户名；若仓库已推送到 GitHub，可从仓库页面获取 raw 链接。

---

## 从 Git 克隆安装

```bash
# 1. 克隆仓库到临时目录
cd /tmp && git clone https://github.com/YOUR_USERNAME/klipper-z-backlash.git

# 2. 复制模块到 Klipper
cp /tmp/klipper-z-backlash/klippy/extras/z_backlash.py ~/klipper/klippy/extras/

# 3. 清理
rm -rf /tmp/klipper-z-backlash
```

### 从本地已克隆的仓库安装

若已克隆本仓库到本地：

```bash
cp /path/to/klipper-z-backlash/klippy/extras/z_backlash.py ~/klipper/klippy/extras/
```

---

## 完整安装步骤

### 1. 下载并安装模块

```bash
# 进入 Klipper extras 目录（默认路径，按实际修改）
cd ~/klipper/klippy/extras

# 下载 z_backlash.py（任选一种方式）
# 方式 A：wget
wget https://raw.githubusercontent.com/YOUR_USERNAME/klipper-z-backlash/master/klippy/extras/z_backlash.py

# 方式 B：curl
curl -sSL -o z_backlash.py https://raw.githubusercontent.com/YOUR_USERNAME/klipper-z-backlash/master/klippy/extras/z_backlash.py
```

### 2. 添加配置

编辑 `printer.cfg`，加入：

```ini
[z_backlash]
backlash: 0.1
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

示例（自定义路径）：

```bash
cp z_backlash.py /home/pi/klipper/klippy/extras/
```

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
