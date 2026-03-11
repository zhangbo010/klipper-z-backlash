#!/bin/bash
# Klipper Z轴回差补偿插件 - 一键安装脚本
# 在 Klipper 主机（树莓派等）上执行: bash install.sh

set -e

REPO_URL="https://raw.githubusercontent.com/zhangbo010/klipper-z-backlash/main"
EXTRAS_FILE="klippy/extras/z_backlash.py"
CONFIG_FILE="config/z_backlash.cfg"

echo "=========================================="
echo "  Klipper Z轴回差补偿 - 一键安装"
echo "=========================================="
echo ""

# 检测 Klipper 路径
KLIPPER_PATH=""
for path in "$HOME/klipper" "/home/pi/klipper" "/home/mainsail/klipper" "/home/fluidd/klipper"; do
    if [ -d "$path/klippy/extras" ]; then
        KLIPPER_PATH="$path"
        break
    fi
done

if [ -z "$KLIPPER_PATH" ]; then
    echo "错误: 未找到 Klipper 安装目录"
    echo "请手动指定路径，例如: KLIPPER_PATH=/path/to/klipper bash install.sh"
    exit 1
fi

echo "检测到 Klipper 路径: $KLIPPER_PATH"
EXTRAS_DIR="$KLIPPER_PATH/klippy/extras"
TARGET_FILE="$EXTRAS_DIR/z_backlash.py"

# 下载模块
echo ""
echo "[1/3] 下载 z_backlash.py ..."
if command -v wget &>/dev/null; then
    wget -q -O "$TARGET_FILE" "$REPO_URL/$EXTRAS_FILE"
elif command -v curl &>/dev/null; then
    curl -sSL -o "$TARGET_FILE" "$REPO_URL/$EXTRAS_FILE"
else
    echo "错误: 需要 wget 或 curl"
    exit 1
fi

echo "      已安装到: $TARGET_FILE"

# 查找 printer.cfg
echo ""
echo "[2/3] 配置检查 ..."
PRINTER_CFG=""
for cfg in "$KLIPPER_PATH/printer.cfg" "$HOME/printer_data/config/printer.cfg" "/home/pi/printer_data/config/printer.cfg"; do
    if [ -f "$cfg" ]; then
        PRINTER_CFG="$cfg"
        break
    fi
done

if [ -n "$PRINTER_CFG" ]; then
    if grep -q "\[z_backlash\]" "$PRINTER_CFG" 2>/dev/null; then
        echo "      printer.cfg 中已存在 [z_backlash] 配置"
    else
        CONFIG_DIR="$(dirname "$PRINTER_CFG")"
        CONFIG_DEST="$CONFIG_DIR/z_backlash.cfg"
        if command -v wget &>/dev/null; then
            wget -q -O "$CONFIG_DEST" "$REPO_URL/$CONFIG_FILE"
        else
            curl -sSL -o "$CONFIG_DEST" "$REPO_URL/$CONFIG_FILE"
        fi
        echo "      已下载配置到: $CONFIG_DEST"
        echo ""
        echo "      请在 printer.cfg 中添加以下行:"
        echo "      [include z_backlash.cfg]"
        echo ""
        echo "      或直接添加:"
        echo "      [z_backlash]"
        echo "      backlash: 0.1"
    fi
else
    echo "      未找到 printer.cfg，请手动添加 [z_backlash] 配置"
fi

# 重启 Klipper
echo ""
echo "[3/3] 重启 Klipper 服务 ..."
if systemctl is-active --quiet klipper 2>/dev/null; then
    sudo systemctl restart klipper
    echo "      Klipper 已重启"
else
    echo "      未检测到 klipper 服务，请手动重启"
fi

echo ""
echo "=========================================="
echo "  安装完成!"
echo "=========================================="
echo ""
echo "验证: 在 Klipper 控制台执行 Z_BACKLASH_COMPENSATE VALUE=0.1"
echo ""
