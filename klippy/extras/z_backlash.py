# Z Axis Backlash Compensation
#
# 换向两段：① 步进长度=|ΔZ|（终点 z_phys+ΔZ；上一段若有补偿则 z_phys≠z_logical，第一段后 adj=z_after_main−target）；② 再脉冲 comp。
# get_position 用 _z_report_adj=commanded[Z]−G-code 目标 Z。ΔZ 用 get_position() 起点（与 M114 一致），
# 不用插件内缓存 last_z，避免 SAVE_GCODE_STATE/RESTORE 与宏重复 G1 时错位。
# homing:home_rails_begin→end 期间 _in_homing，不拆段、不补偿（归零用底层 move）。
#
# printer.cfg 示例：
#   [z_backlash]
#   backlash: 0.1
#   # split_pause: 两段之间 dwell(秒)；0=不停顿
#   # takeup_speed: 第二段补偿速度(mm/s)；0=与本次 G 移动同速
#   # compensation_scale: 补偿段长度系数，默认 1.0；实测仍偏多可改为 0.5～0.8
#
# Copyright (C) 2025
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import importlib
import logging


class ZBacklashCompensation:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.backlash = config.getfloat('backlash', 0.1, minval=0.)
        self.compensation_scale = config.getfloat(
            'compensation_scale', 1., above=0., maxval=2.)
        self.split_pause = config.getfloat('split_pause', 0.08, minval=0.)
        self.takeup_speed = config.getfloat('takeup_speed', 0., minval=0.)
        self.last_z_direction = None  # 1=up, -1=down
        # 补偿段导致的底层 Z 与逻辑 Z 之差，get_position 减去此项
        self._z_report_adj = 0.
        self._in_homing = False  # 归零过程中不拆段、不补偿（G28 等）
        self.next_transform = None
        self.printer.register_event_handler("klippy:connect",
                                            self._handle_connect)
        self.printer.register_event_handler("homing:home_rails_begin",
                                            self._handle_home_rails_begin)
        self.printer.register_event_handler("homing:home_rails_end",
                                            self._handle_home_rails_end)
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('Z_BACKLASH_COMPENSATE',
                               self.cmd_Z_BACKLASH_COMPENSATE,
                               desc=self.cmd_Z_BACKLASH_COMPENSATE_help)

    def _handle_connect(self):
        gcode_move = self.printer.lookup_object('gcode_move')
        self.toolhead = self.printer.lookup_object('toolhead')
        self.next_transform = gcode_move.set_move_transform(self, force=True)

    def _handle_home_rails_begin(self, homing_state, rails):
        self._in_homing = True

    def _handle_home_rails_end(self, homing_state, rails):
        self._in_homing = False
        self.last_z_direction = None
        self._z_report_adj = 0.

    def get_position(self):
        pos = list(self.next_transform.get_position())
        if self._z_report_adj:
            pos[2] -= self._z_report_adj
        return pos

    def get_trapq_z_adjustment(self):
        """trapq 物理 Z 相对逻辑 Z 的偏移；供 motion_report 与 get_position 一致"""
        return self._z_report_adj

    def move(self, newpos, speed):
        newpos = list(newpos)
        z_target = newpos[2]
        if self._in_homing:
            self._z_report_adj = 0.
            self.next_transform.move(newpos, speed)
            return
        # gcode_move 在调用本 move 前已把 last_position 更新为「本段终点」，不能用其算 ΔZ。
        # 逻辑起点 = 本段终点 − 位移；位移 = 逻辑当前 get_position（与 M114 一致）到终点的差。
        z_logical_start = self.get_position()[2]
        z_delta = z_target - z_logical_start
        # 底层物理 Z（commanded_pos）
        z_phys = self.next_transform.get_position()[2]
        phys_minus_logical = z_phys - z_logical_start
        # 单段移动时底层必须走到 z_phys+z_delta；若把 gcode 的 z_target 直接传给 toolhead，
        # 在「逻辑≠物理」（_z_report_adj≠0）时会把终点当成逻辑坐标，同向第二段会少走约 |adj|。

        if abs(z_delta) > 1e-9:
            if z_delta > 0:
                new_direction = 1
            else:
                new_direction = -1

            prev_dir = self.last_z_direction
            reversal = (prev_dir is not None
                        and new_direction != prev_dir)
            self.last_z_direction = new_direction

            # 换向：先走到 target；仅当 |ΔZ|>backlash 时再追加补偿（长行程已消隙，短行程只走一段避免重复加回差）
            if reversal and abs(z_delta) > self.backlash + 1e-9:
                s = 1.0 if z_delta > 0 else -1.0
                comp = self.backlash * self.compensation_scale
                # 第一段：步进长度 = |ΔZ|（z_phys→z_phys+z_delta）；若 z_phys≠z_logical，终点物理为 z_target+(z_phys−z_logical)，需 adj 使逻辑仍为 z_target
                z_after_main = z_phys + z_delta
                z_comp = z_after_main + s * comp
                logging.info(
                    "z_backlash: 两段 ① phys %.4f+ΔZ=%.4f -> %.4f ②补偿 -> phys=%.4f (|dZ|=%.4f comp=%.4f)",
                    z_phys, z_delta, z_after_main, z_comp, abs(z_delta), comp)
                p1 = list(newpos)
                p1[2] = z_after_main
                self._z_report_adj = z_after_main - z_target
                self.next_transform.move(p1, speed)
                if self.split_pause > 0.:
                    self.toolhead.dwell(self.split_pause)
                p2 = list(newpos)
                p2[2] = z_comp
                sp2 = speed
                if self.takeup_speed > 0.:
                    sp2 = min(speed, self.takeup_speed)
                self.next_transform.move(p2, sp2)
                self._z_report_adj = (
                    self.next_transform.get_position()[2] - z_target)
            elif reversal:
                logging.info(
                    "z_backlash: 换向但 |dZ|=%.4f <= bl=%.4f，仅单段至 target（不追加补偿）",
                    abs(z_delta), self.backlash)
                self._z_report_adj = phys_minus_logical
                p = list(newpos)
                p[2] = z_phys + z_delta
                self.next_transform.move(p, speed)
                self._z_report_adj = (
                    self.next_transform.get_position()[2] - z_target)
            else:
                # 同向：终点物理 = 当前物理 + 逻辑位移（与两段里第一段 z_phys+z_delta 一致）
                self._z_report_adj = phys_minus_logical
                p = list(newpos)
                p[2] = z_phys + z_delta
                self.next_transform.move(p, speed)
                self._z_report_adj = (
                    self.next_transform.get_position()[2] - z_target)
        else:
            # 无 Z 变化：保持 Z 物理位置，勿把逻辑坐标当终点（否则在 adj≠0 时会误拉 Z）
            p = list(newpos)
            p[2] = z_phys
            self.next_transform.move(p, speed)

    cmd_Z_BACKLASH_COMPENSATE_help = "Set Z backlash compensation value"
    def cmd_Z_BACKLASH_COMPENSATE(self, gcmd):
        self.backlash = gcmd.get_float('VALUE', self.backlash, minval=0.)
        gcmd.respond_info("Z backlash compensation set to %.3f mm" % self.backlash)

    def get_status(self, eventtime):
        return {
            'backlash': self.backlash,
            'compensation_scale': self.compensation_scale,
            'split_pause': self.split_pause,
            'takeup_speed': self.takeup_speed,
        }


def load_config(config):
    # Klippy 的 FIRMWARE_RESTART 在同一 Python 进程内循环，不会重新 import extras。
    # 若进程曾在「未读取 split_pause/takeup_speed 的旧版」下导入过本模块，会一直用旧类，
    # 导致 printer.cfg 里写了 split_pause 却报 Option is not valid。reload 后每次加载配置都
    # 与磁盘上的 z_backlash.py 一致。
    mod = importlib.import_module('extras.z_backlash')
    importlib.reload(mod)
    return mod.ZBacklashCompensation(config)
