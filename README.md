# Klipper Z轴回差补偿插件

为 Klipper 固件提供 Z 轴机械回差（背隙）补偿功能。Z 轴丝杆与螺母之间存在间隙，方向反转时会产生空程，导致实际位移与预期不一致，因此需要补偿。

## 功能说明

当 Z 轴**运动方向反转**（例如从上升变为下降），且本段行程 **大于** 设定的 `backlash` 时，插件将运动拆成**两段真实的直线移动**：先沿新方向走出约 `backlash` 的消隙行程，再走到目标 Z。补偿体现在**多发出的步进脉冲**上；**不**通过修改 `get_position()` 去「藏坐标」，因此 **M114 / 逻辑位置与 G-code 目标一致**。

### 工作原理

- **两段消隙**：换向且 `|ΔZ| > backlash` 时，先 `move` 到中间点（消隙），可选停顿后再 `move` 到目标；同向连续移动或行程不足以拆两段时不做拆分。
- **坐标不篡改**：`get_position()` 仅透传下层变换，便于与切片、显示一致。
- **分段移动兼容**：用逻辑目标 Z 与方向状态判断换向，减轻分段规划下的误判。
- **配置热更新**：`load_config` 内对模块做 `importlib.reload`，在多数情况下 **`FIRMWARE_RESTART`** 即可加载新版 `z_backlash.py`；若曾长期运行旧版进程且出现异常，建议执行一次 **`sudo systemctl restart klipper`** 完整重启主机进程。

## 安装方法

需要已安装 **git**。

### 推荐：克隆后复制

```bash
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
cp klipper-z-backlash/klippy/extras/z_backlash.py ~/klipper/klippy/extras/
# 可选：复制配置示例到 printer_data/config/
cp klipper-z-backlash/config/z_backlash.cfg ~/printer_data/config/
```

将 `~/klipper` 换成你机器上的 Klipper 路径。然后在 `printer.cfg` 中加入 `[z_backlash]` 或 `[include z_backlash.cfg]`，**重启 Klipper 服务**（见下文）。

### 一键脚本（git 克隆）

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh)
```

脚本内部使用 `git clone`（强制 HTTP/1.1）拉取仓库后复制文件。需已安装 `git`。

### 克隆失败（RPC failed / HTTP2 framing layer）

网络不稳定时 Git 走 HTTP/2 可能报错，可全局改用 HTTP/1.1 后再克隆：

```bash
git config --global http.version HTTP/1.1
```

或每次克隆时加上 `-c http.version=HTTP/1.1`（见上文命令）。仍失败时可用 `curl` 直接下载单文件（见 [INSTALL.md](INSTALL.md)）。

### 手动安装

1. 将 `klippy/extras/z_backlash.py` 复制到 Klipper 的 `klippy/extras/` 目录
2. 在 `printer.cfg` 中添加配置段（见下方配置说明）
3. 重启 Klipper 服务：`sudo systemctl restart klipper`

## 配置说明

在 `printer.cfg` 中添加（或 `include` 本仓库的 `config/z_backlash.cfg`）：

```ini
[z_backlash]
backlash: 0.1
# 以下为可选
# split_pause: 0.08
# takeup_speed: 0
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `backlash` | float | 0.1 | 回差补偿量（mm），需根据打印机实际测量 |
| `split_pause` | float | 0.08 | 两段消隙之间 dwell（秒），0 表示不停顿；可减轻 lookahead 将两段合成一条轨迹的观感 |
| `takeup_speed` | float | 0 | 第一段消隙速度（mm/s）；0 表示与本次移动速度相同；设小一点便于观察消隙段 |

Klipper 要求 **`[z_backlash]` 中出现的每个选项都必须被本插件读取**。请保持 **`z_backlash.py` 与上述配置同步**；若报 `Option 'xxx' is not valid`，多为插件文件未更新或需完整重启 Klipper 进程。

## G 代码命令

- **Z_BACKLASH_COMPENSATE VALUE=\<值\>**  
  运行时设置回差补偿量，例如：`Z_BACKLASH_COMPENSATE VALUE=0.08`

## 兼容性

- 与 `skew_correction`、`bed_mesh` 等模块兼容
- 归位（G28）后会自动重置方向状态
- 支持小步距往复移动（需满足换向且行程大于 `backlash` 才会拆两段）

## 许可证

GNU GPLv3
