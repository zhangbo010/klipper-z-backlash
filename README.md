# Klipper Z 轴回差补偿插件

为 Klipper 提供 Z 轴丝杆螺母**机械间隙（回差）**补偿：换向时多走一段脉冲，**G-code / M114 的 Z 仍与指令一致**。

## 功能说明

当 Z 轴**运动方向反转**（上→下或下→上），且本段 **`|ΔZ| > backlash`** 时，将本次移动拆成**两段真实直线**：

1. **第一段**：步进长度等于 **`|ΔZ|`**（从当前物理 Z 走 `z_phys + ΔZ` 到 G-code 目标；若上一段曾补偿，物理与逻辑可能暂时不同，本段不会把「上一段多走的量」算进本段步距）。
2. **第二段**：沿**同一方向**再脉冲 **`backlash × compensation_scale`**，用于消隙；逻辑 Z 通过内部修正仍显示为 G-code 目标。

`|ΔZ| ≤ backlash` 的换向**不**拆第二段（短行程主段已在间隙内，避免过量）。

**归零（G28 单轴/多轴）**：在 `homing:home_rails_begin`～`home_rails_end` 整段过程中**不**做回差拆段与补偿，避免干扰归零。

## 工作原理（摘要）

- **本段 ΔZ**：在 `move()` 入口用 **`get_position()[2]`**（与 M114 一致的逻辑 Z）作为起点，与 `last_position` 解耦；**不**缓存「上一段目标 Z」，避免 `SAVE_GCODE_STATE` / `RESTORE_GCODE_STATE` 与宏连续 `G1` 时错位。
- **换向判断**：用上一段 Z 运动方向（`last_z_direction`）与当前方向比较。
- **`get_position()`**：`commanded[Z] − _z_report_adj`，使变换链上的 Z 与 G-code 目标一致；`_z_report_adj` 在每次移动后更新为「物理终点 − 逻辑目标」。
- **单段移动（同向，或换向但 |ΔZ|≤backlash）**：传给 `toolhead` 的 Z 终点为 **`z_phys + ΔZ`**（当前物理 Z 加**逻辑位移**），**不能**直接用 gcode 的 `z_target`。补偿后若逻辑与物理不一致（例如 `backlash=1` 时逻辑在 0、物理在 −1），若误把 `z_target` 当物理终点，同向连续第二段会少走路程约 **|回差|**。
- **本段 Z 无变化**：仅动 XY 等时，Z 传 **`z_phys`**，避免在 `_z_report_adj≠0` 时把逻辑坐标当物理终点误拉 Z。
- **界面 live Z**：若 Fluidd/Mainsail 等大数字与方括号目标不一致，可在完整 Klipper 树中对 `motion_report.py` 打补丁（见下文「可选：界面」）。

## 安装方法

需要已安装 **git**。

### 推荐：克隆后复制

```bash
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/zhangbo010/klipper-z-backlash.git
cp klipper-z-backlash/klippy/extras/z_backlash.py ~/klipper/klippy/extras/
cp klipper-z-backlash/config/z_backlash.cfg ~/printer_data/config/
```

将 `~/klipper` 换成你机器上的 Klipper 路径。在 `printer.cfg` 中加入 `[z_backlash]` 或 `[include z_backlash.cfg]`，执行 **`FIRMWARE_RESTART`** 或 `sudo systemctl restart klipper`。

### 一键脚本

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh)
```

### 克隆失败（HTTP2 / RPC）

```bash
git config --global http.version HTTP/1.1
```

详见 [INSTALL.md](INSTALL.md)。

## 配置说明

在 `printer.cfg` 中添加（或 `include` 本仓库的 `config/z_backlash.cfg`）：

```ini
[z_backlash]
backlash: 0.1
# 以下为可选
# compensation_scale: 1.0
# split_pause: 0.08
# takeup_speed: 0
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `backlash` | float | 0.1 | 补偿段长度基准（mm），按实机测量 |
| `compensation_scale` | float | 1.0 | 实际补偿 = `backlash × compensation_scale`（0～2）；仍偏多可调 0.5～0.8 |
| `split_pause` | float | 0.08 | 两段之间 dwell（秒）；`0` 为不停顿 |
| `takeup_speed` | float | 0 | 第二段补偿速度（mm/s）；`0` 表示与本次移动同速 |

Klipper 要求 **`[z_backlash]` 中出现的每个选项都必须被本插件读取**。若报 `Option 'xxx' is not valid`，请更新 `z_backlash.py` 或完整重启 Klipper 进程。

## G 代码命令

- **Z_BACKLASH_COMPENSATE VALUE=\<值\>**  
  运行时修改 `backlash`，例如：`Z_BACKLASH_COMPENSATE VALUE=0.08`

## 可选：界面 live 与目标 Z 对齐

`motion_report` 的 `live_position` 来自 trapq（物理插补），未经过本插件时，大屏 Z 可能比 G-code 目标多约 `backlash`。若需一致，可在**完整 Klipper 源码**中修改 `klippy/extras/motion_report.py`（在仓库 Issues/说明中可附补丁思路）。**本仓库仅包含 `z_backlash.py`**，不修改 Klipper 核心文件。

## 兼容性

- 与 `skew_correction`、`bed_mesh` 等常见模块配合使用；归位后方向/逻辑状态会重置。
- **`load_config` 内对模块 `reload`**，多数情况下 **`FIRMWARE_RESTART`** 即可加载新版 `z_backlash.py`；若异常可 **`sudo systemctl restart klipper`**。

## 许可证

GNU GPLv3
