# Z Axis Backlash Compensation
#
# 丝杆螺母间隙：仅在 Z 换向时先走 backlash 消隙，再沿新方向走完整 |ΔZ|（总路程 |ΔZ|+backlash）。
# 第二段长度为完整 |ΔZ|，故 plan_end = z_phys + sign(ΔZ)*backlash + ΔZ；get_position 减去 (plan_end−target)，使 M114 与 G-code 一致。
#
# printer.cfg 示例：
#   [z_backlash]
#   backlash: 0.1
#   # split_pause: 两段消隙之间 dwell(秒)；0=不停顿
#   # takeup_speed: 第一段消隙速度(mm/s)；0=与本次 G 移动同速
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
        self.split_pause = config.getfloat('split_pause', 0.08, minval=0.)
        self.takeup_speed = config.getfloat('takeup_speed', 0., minval=0.)
        self.last_z_direction = None  # 1=up, -1=down
        self.last_logical_z = None    # 上一段 G1 的目标 Z（与 gcode 一致）
        # 两段消隙完成后底层 Z 与逻辑 Z 的差（plan_end − z_target），get_position 减去此项以对齐 M114
        self._z_report_adj = 0.
        self.next_transform = None
        self.printer.register_event_handler("klippy:connect",
                                            self._handle_connect)
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

    def _handle_home_rails_end(self, homing_state, rails):
        self.last_z_direction = None
        self.last_logical_z = None
        self._z_report_adj = 0.

    def get_position(self):
        pos = list(self.next_transform.get_position())
        if self._z_report_adj:
            pos[2] -= self._z_report_adj
        return pos

    def move(self, newpos, speed):
        newpos = list(newpos)
        z_target = newpos[2]
        z_logical = self.last_logical_z
        if z_logical is None:
            z_logical = self.get_position()[2]
        z_phys = self.next_transform.get_position()[2]
        z_delta = z_target - z_logical

        if abs(z_delta) > 1e-9:
            if z_delta > 0:
                new_direction = 1
            else:
                new_direction = -1

            prev_dir = self.last_z_direction
            reversal = (prev_dir is not None
                        and new_direction != prev_dir)
            self.last_z_direction = new_direction

            # 两段消隙：换向且 |ΔZ| 严格大于 backlash（否则第一段消隙会越过目标）
            can_split = reversal and abs(z_delta) > self.backlash + 1e-9
            if can_split:
                s = 1.0 if z_delta > 0 else -1.0
                # 从物理 Z 起走 backlash 消隙，第二段再走完整 ΔZ（总脉冲 |ΔZ|+backlash）
                z_takeup = z_phys + s * self.backlash
                z_plan_end = z_takeup + z_delta
                plan_adj = z_plan_end - z_target
                logging.info(
                    "z_backlash: 两段消隙 log=%.4f phys=%.4f -> takeup=%.4f -> plan_end=%.4f (target=%.4f |dZ|=%.4f bl=%.4f adj=%.4f)",
                    z_logical, z_phys, z_takeup, z_plan_end, z_target,
                    abs(z_delta), self.backlash, plan_adj)
                p1 = list(newpos)
                p1[2] = z_takeup
                sp1 = speed
                if self.takeup_speed > 0.:
                    sp1 = min(speed, self.takeup_speed)
                self.next_transform.move(p1, sp1)
                # 消隙段结束后底层在 z_takeup，逻辑上仍应为 z_logical，便于 dwell 期间 M114 正确
                self._z_report_adj = z_takeup - z_logical
                if self.split_pause > 0.:
                    self.toolhead.dwell(self.split_pause)
                p2 = list(newpos)
                p2[2] = z_plan_end
                self.next_transform.move(p2, speed)
                # _z_report_adj 与消隙段后相同 (= z_plan_end - z_target)，底层已到 z_plan_end
            else:
                self._z_report_adj = 0.
                # 同向、首段、或行程不足以拆两段时：单次走到目标
                self.next_transform.move(newpos, speed)
        else:
            self.next_transform.move(newpos, speed)

        self.last_logical_z = z_target

    cmd_Z_BACKLASH_COMPENSATE_help = "Set Z backlash compensation value"
    def cmd_Z_BACKLASH_COMPENSATE(self, gcmd):
        self.backlash = gcmd.get_float('VALUE', self.backlash, minval=0.)
        gcmd.respond_info("Z backlash compensation set to %.3f mm" % self.backlash)

    def get_status(self, eventtime):
        return {
            'backlash': self.backlash,
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
