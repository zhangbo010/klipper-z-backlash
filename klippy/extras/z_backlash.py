# Z Axis Backlash Compensation
#
# Compensates for Z-axis mechanical backlash (e.g. lead screw/nut clearance)
# by adding extra movement when Z direction reverses.
#
# Copyright (C) 2025
#
# This file may be distributed under the terms of the GNU GPLv3 license.


class ZBacklashCompensation:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.backlash = config.getfloat('backlash', 0.1, minval=0.)
        self.last_z_direction = None  # 1=up, -1=down
        self.last_logical_z = None    # 逻辑 Z 位置，用于方向判断
        self.last_compensation = 0.    # 上次补偿量：+backlash 向上补偿，-backlash 向下补偿；get_position 需减去此项以保持逻辑位置不变
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
        self.next_transform = gcode_move.set_move_transform(self, force=True)

    def _handle_home_rails_end(self, homing_state, rails):
        self.last_z_direction = None
        self.last_logical_z = None
        self.last_compensation = 0.

    def get_position(self):
        pos = list(self.next_transform.get_position())
        # 实际位置数据不做调整：返回逻辑位置（物理位置 - 已补偿量）
        pos[2] = pos[2] - self.last_compensation
        return pos

    def move(self, newpos, speed):
        z_target = newpos[2]
        # 使用逻辑位置判断方向，避免分段移动时 get_position() 返回补偿后的物理位置导致错误触发补偿
        z_current = self.last_logical_z
        if z_current is None:
            z_current = self.next_transform.get_position()[2]
        z_delta = z_target - z_current

        if abs(z_delta) > 1e-9:
            if z_delta > 0:
                new_direction = 1   # moving up
            else:
                new_direction = -1  # moving down

            if self.last_z_direction is not None and new_direction != self.last_z_direction:
                # 回程：补偿一个补偿值对应的脉冲，实际位置数据不做调整
                if new_direction > 0:
                    newpos = list(newpos)
                    newpos[2] = z_target + self.backlash
                    self.last_compensation = self.backlash
                else:
                    newpos = list(newpos)
                    newpos[2] = z_target - self.backlash
                    self.last_compensation = -self.backlash

            self.last_z_direction = new_direction
        else:
            self.last_compensation = 0.  # 同向移动，无补偿
        self.last_logical_z = z_target

        self.next_transform.move(newpos, speed)

    cmd_Z_BACKLASH_COMPENSATE_help = "Set Z backlash compensation value"
    def cmd_Z_BACKLASH_COMPENSATE(self, gcmd):
        self.backlash = gcmd.get_float('VALUE', self.backlash, minval=0.)
        gcmd.respond_info("Z backlash compensation set to %.3f mm" % self.backlash)

    def get_status(self, eventtime):
        return {'backlash': self.backlash}


def load_config(config):
    return ZBacklashCompensation(config)
