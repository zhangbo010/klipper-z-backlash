# Klipper Z轴回差补偿插件

为 Klipper 固件提供 Z 轴机械回差（背隙）补偿功能。Z 轴丝杆与螺母之间存在间隙，方向反转时会产生空程，导致实际位移小于指令位移，因此需要补偿。

## 功能说明

当 Z 轴运动方向反转时（例如从上升变为下降），丝杆间隙会导致实际位移小于指令位移。本插件在检测到方向反转（回程）时，自动补偿一个补偿值对应的脉冲，以消除回差影响。

### 工作原理

- **仅补偿脉冲**：补偿只体现在步进脉冲上，多走/少走对应距离以消除丝杆间隙
- **坐标不补偿**：Z 坐标保持 G 代码原样，不修改，否则切片与打印会错乱
- **分段移动兼容**：使用逻辑位置判断方向，避免 Klipper 分段移动时错误触发补偿

## 安装方法

### 一键安装（推荐）

在 Klipper 主机终端执行：

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main/install.sh)
```

### 手动安装

1. 将 `klippy/extras/z_backlash.py` 复制到 Klipper 的 `klippy/extras/` 目录
2. 在 `printer.cfg` 中添加配置段（见下方配置说明）
3. 重启 Klipper 服务

## 配置说明

在 `printer.cfg` 中添加：

```ini
[z_backlash]
# 回差补偿量（单位：mm），根据实际测量调整
# 建议从 0.05 开始，逐步增加直到效果满意
backlash: 0.1
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `backlash` | float | 0.1 | 回差补偿量（mm），需根据打印机实际测量 |

## G 代码命令

- **Z_BACKLASH_COMPENSATE VALUE=\<值\>**  
  运行时设置回差补偿量，例如：`Z_BACKLASH_COMPENSATE VALUE=0.08`

## 兼容性

- 与 `skew_correction`、`bed_mesh` 等模块兼容
- 归位（G28）后会自动重置方向状态
- 支持 0.1mm 等小步距往复移动

## 许可证

GNU GPLv3
