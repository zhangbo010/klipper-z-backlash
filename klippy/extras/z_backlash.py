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

    def get_position(self):
        return self.next_transform.get_position()

    def move(self, newpos, speed):
        current_pos = self.next_transform.get_position()
        z_current = current_pos[2]
        z_target = newpos[2]
        z_delta = z_target - z_current

        if abs(z_delta) > 1e-9:
            if z_delta > 0:
                new_direction = 1   # moving up
            else:
                new_direction = -1  # moving down

            if self.last_z_direction is not None and new_direction != self.last_z_direction:
                # Direction reversed: add backlash compensation
                if new_direction > 0:
                    newpos = list(newpos)
                    newpos[2] = z_target + self.backlash
                else:
                    newpos = list(newpos)
                    newpos[2] = z_target - self.backlash

            self.last_z_direction = new_direction
        else:
            # No Z movement - don't update direction
            pass

        self.next_transform.move(newpos, speed)

    cmd_Z_BACKLASH_COMPENSATE_help = "Set Z backlash compensation value"
    def cmd_Z_BACKLASH_COMPENSATE(self, gcmd):
        self.backlash = gcmd.get_float('VALUE', self.backlash, minval=0.)
        gcmd.respond_info("Z backlash compensation set to %.3f mm" % self.backlash)

    def get_status(self, eventtime):
        return {'backlash': self.backlash}


def load_config(config):
    return ZBacklashCompensation(config)
