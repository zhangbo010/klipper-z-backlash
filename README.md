# Klipper Z轴回差补偿插件

为 Klipper 固件提供 Z 轴机械回差（背隙）补偿功能，适用于丝杆/螺母存在间隙的打印机。

## 功能说明

当 Z 轴运动方向反转时（例如从上升变为下降），机械间隙会导致实际位移小于指令位移。本插件在检测到方向反转时，自动在运动指令中增加补偿量，以消除回差影响。

## 安装方法

1. 将 `klippy/extras/z_backlash.py` 复制到你的 Klipper 安装目录下的 `klippy/extras/` 文件夹中：
   ```bash
   cp klippy/extras/z_backlash.py ~/klipper/klippy/extras/
   ```

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

## 许可证

GNU GPLv3
