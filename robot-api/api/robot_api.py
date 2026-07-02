#!/usr/bin/env python3

COMS_PORT = 29001
RTD_PORT = 29000

from .ctrl import Control
import logging
import sys
import socket
import struct
import math
import time

def _to_rad(x):
    return x * math.pi / 180.0

CTRLR_COMS_STOP = 0
CTRLR_COMS_MOVE_ADD_WP = 1
CTRLR_COMS_MOVE_RUN = 2
CTRLR_COMS_MOVE_SCALE = 3
CTRLR_COMS_RESERVED0 = 4
CTRLR_COMS_POWER = 5
CTRLR_COMS_RESERVED1 = 6
CTRLR_COMS_RESERVED2 = 7
CTRLR_COMS_JOG = 8
CTRLR_COMS_NOP = 9
CTRLR_COMS_RESERVED3 = 10
CTRLR_COMS_RESERVED4 = 11
CTRLR_COMS_RESERVED5 = 12
CTRLR_COMS_RESERVED6 = 13
CTRLR_COMS_SET_OUTPUTS = 14
CTRLR_COMS_ZG = 15
#control unlocking
CTRLR_COMS_UNLOCK = 100
#settings functions
CTRLR_COMS_SET_GRAVITY = 1016
CTRLR_COMS_GET_GRAVITY = 1116
CTRLR_COMS_SET_ZG_FSCALE = 1017
CTRLR_COMS_GET_ZG_FSCALE = 1117
CTRLR_COMS_SET_TRQ_WIN = 1018
CTRLR_COMS_GET_TRQ_WIN = 1118
CTRLR_COMS_SET_FLW_ERR = 1019
CTRLR_COMS_GET_FLW_ERR = 1119
CTRLR_COMS_SET_MAX_VEL = 1020
CTRLR_COMS_GET_MAX_VEL = 1120
CTRLR_COMS_SET_PAYLOAD = 1021
CTRLR_COMS_GET_PAYLOAD = 1121
CTRLR_COMS_SET_TOOL = 1022
CTRLR_COMS_GET_TOOL = 1122
CTRLR_COMS_SET_JOG_PARAM = 1023
CTRLR_COMS_GET_JOG_PARAM = 1123
CTRLR_COMS_SET_FORCE_PARAM = 1024
CTRLR_COMS_GET_FORCE_PARAM = 1124
CTRLR_COMS_SET_IO_FUNC = 1025
CTRLR_COMS_GET_IO_FUNC = 1125
CTRLR_COMS_SET_DH_MODEL = 1026
CTRLR_COMS_GET_DH_MODEL = 1126
CTRLR_COMS_SET_TOOL_CAPSULE_COUNT = 1027
CTRLR_COMS_GET_TOOL_CAPSULE_COUNT = 1127
CTRLR_COMS_SET_TOOL_CAPSULE = 1028
CTRLR_COMS_GET_TOOL_CAPSULE = 1128
CTRLR_COMS_GET_LINK_CAPSULE_COUNT = 1129
CTRLR_COMS_GET_LINK_CAPSULE = 1130
#service functions
CTRLR_COMS_FKINE = 2000
CTRLR_COMS_IKINE = 2001

CTRLR_COMS_POWER_CMD_OFF = 0
CTRLR_COMS_POWER_CMD_STBY = 1
CTRLR_COMS_POWER_CMD_ON = 2
CTRLR_COMS_POWER_CMD_RUN = 3

#motion types for add_wp command
MOVE_WP_TYPE_JOINT = 0
MOVE_WP_TYPE_LINEAR_CART = 1
MOVE_WP_TYPE_LINEAR_POSE = 2

CTRLR_PROTO_VERSION = 0x02000100


class Variables:

    def __init__(self):
        self.t = 0
        self.des_q = [0, 0, 0, 0, 0, 0]
        self.des_x = [0, 0, 0, 0, 0, 0]
        self.force = [0, 0, 0, 0, 0, 0]
        self.force_en = [0, 0, 0, 0, 0, 0]
        self.in_tcp = 0
        self.vmax_t = 0
        self.vmax_r = 0
        self.amax_t = 0
        self.amax_r = 0
        self.vmax_j = 0
        self.amax_j = 0
        self.rblend = 0


class RobotAPI:
    def __init__(self, ip):
        self.coms_port = COMS_PORT
        self.coms_port = COMS_PORT
        self.rtd_port = RTD_PORT
        self.ctrl = None
        self.ip = ip
        self.logger = logging
        self.socket = None
        self.vars = Variables()
        self._cmd_cntr = None
        self.scale_v = 0
        self.scale_a = 0


    def _init_control(self):
        self.ctrl = Control(ip=self.ip)
        if not self.ctrl.start_thread():
            self.ctrl = None
        return True


    def _connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.coms_port))
            self.socket.settimeout(1)
            logging.debug(f"Socket connect [{self.ip}:{self.coms_port}] --> Ok")
            self._cmd(CTRLR_COMS_UNLOCK, struct.pack("I", CTRLR_PROTO_VERSION));
            return True
        except Exception as error:
            logging.error(
                f"Socket connect [{self.ip}:{self.coms_port}] --> False\n{error}"
            )
            self._stop()
            return False

    def _recv(self, l):
        try:
            d = self.socket.recv(l)
            if d == b'':
                print("CTRL connection lost")
                self._stop()
        except Exception as error:
            self._stop()
            return False

        return d

    def _send(self, d):
        try:
            s = self.socket.send(d)
            if s == 0:
                print("CTRL connection lost")
                self._stop()
        except Exception as error:
            self._stop()
            return False

    def _cmd(self, cmd_type, data = []):
        self._send(struct.pack("i", len(data) + 4))
        self._send(struct.pack("i", cmd_type))
        if len(data) > 0:
            self._send(data)

    def _resp(self, cmd_type):
        d = self.socket.recv(4);
        sz = struct.unpack("i", d);

        if sz[0] < 4:
            return []

        d = self._recv(4);
        t = struct.unpack("i", d);

        d = self._recv(sz[0] - 4)

        if t[0] != cmd_type:
            return []

        return d

    def add_wp_deg(
        self,
        t = 0,
        des_q = [0, 0, 0, 0, 0, 0],
        des_x = [0, 0, 0, 0, 0, 0],
        force = [0, 0, 0, 0, 0, 0],
        force_en = [0, 0, 0, 0, 0, 0],
        in_tcp = 0,
        vmax_t = 0,
        vmax_r = 0,
        amax_t = 0,
        amax_r = 0,
        vmax_j = 0,
        amax_j = 0,
        rblend = 0,
    ):

        des_q_rad = des_q.copy()
        des_x_rad = des_x.copy()

        for i in range(0,6):
            des_q_rad[i] = _to_rad(des_q[i])

        for i in range(0,3):
            des_x_rad[i] = des_x[i]

        for i in range(3,6):
            des_x_rad[i] = _to_rad(des_x[i])

        self.add_wp(
            t,
            des_q_rad,
            des_x_rad,
            force,
            force_en,
            in_tcp,
            vmax_t,
            vmax_r,
            amax_t,
            amax_r,
            vmax_j,
            amax_j,
            rblend,
        )

    def add_wp(
        self,
        t = None,
        des_q = None,
        des_x = None,
        force = None,
        force_en = None,
        in_tcp = None,
        vmax_t = None,
        vmax_r = None,
        amax_t = None,
        amax_r = None,
        vmax_j = None,
        amax_j = None,
        rblend = None,
    ):

        if not t:
            t = self.vars.t
        if not des_q:
            des_q = self.vars.des_q
        if not des_x:
            des_x = self.vars.des_x
        if not force:
            force = self.vars.force
        if not force_en:
            force_en = self.vars.force_en
        if not in_tcp:
            in_tcp = self.vars.in_tcp
        if not vmax_t:
            vmax_t = self.vars.vmax_t
        if not vmax_r:
            vmax_r = self.vars.vmax_r
        if not amax_t:
            amax_t = self.vars.amax_t
        if not amax_r:
            amax_r = self.vars.amax_r
        if not vmax_j:
            vmax_j = self.vars.vmax_j
        if not amax_j:
            amax_j = self.vars.amax_j
        if not rblend:
            rblend = self.vars.rblend

        self._cmd(CTRLR_COMS_MOVE_ADD_WP,
            struct.pack(
                "i6d6d6d6BB7di0q",
                t,
                *des_q,
                *des_x,
                *force,
                *force_en,
                in_tcp,
                vmax_t,
                vmax_r,
                amax_t,
                amax_r,
                vmax_j,
                amax_j,
                rblend,
                0,
            )
        )

        self._cmd_cntr = (self._cmd_cntr + 1) & 65535

    def is_motion_stopped(self):
        return self.ctrl.data["buff_fill"] == 0

    def await_buffer(self, value):
        while int(self.ctrl.data["buff_fill"]) > value:
            time.sleep(0.001)
            if not self.ctrl.run:
                self._stop()
        return False if self.is_hold() else True

    def await_hold(self):
        while int(self.ctrl.data["motion_mode"]) != 0:
            time.sleep(0.001)
            if not self.ctrl.run:
                self._stop()

    def await_physical_stop(self, threshold):
        while True:
            qdm = 0
            for qd in self.ctrl.data["act_qd"]:
                qdm = qdm + qd**2
            if qdm**0.5 < threshold:
                break
            time.sleep(0.001)
            if not self.ctrl.run:
                self._stop()

    def await_accepted(self):
        while int(self.ctrl.data["cmd_cntr"]) != self._cmd_cntr:
            time.sleep(0.001)
            if not self.ctrl.run:
                self._stop()


    def await_motion(self):
        self.await_accepted()
        return self.await_buffer(0)


    def hold(self):
        self._cmd(CTRLR_COMS_STOP)

    def is_hold(self):
        return self.ctrl.data["motion_mode"] == 0

    def zg(self, en):
        self._cmd(CTRLR_COMS_ZG, struct.pack("B", en))

    def _stop(self):
        print("Exiting...")
        sys.exit()

    def set_speed_scaling(self, scale):
        self.scale_v = scale
        self._cmd(CTRLR_COMS_MOVE_SCALE, struct.pack("dd", self.scale_v, self.scale_a))


    def set_accel_scaling(self, scale):
        self.scale_a = scale
        self._cmd(CTRLR_COMS_MOVE_SCALE, struct.pack("dd", self.scale_v, self.scale_a))


    def run_wps(self):
        self.await_accepted()
        self._cmd(CTRLR_COMS_MOVE_RUN)


    def run(self):
        for i in range(0, 10):
            time.sleep(0.1)
            try:
                if self.ctrl.data["state"] <= 1:
                    self._cmd(CTRLR_COMS_POWER, struct.pack("i", CTRLR_COMS_POWER_CMD_OFF))
                break
            except:
                pass

        self._cmd(CTRLR_COMS_POWER, struct.pack("i", CTRLR_COMS_POWER_CMD_RUN))

        for i in range(0, 200):
            time.sleep(0.1)
            if "state" in self.ctrl.data:
                if self.ctrl.data["state"] == 4:
                    self._cmd_cntr  = int(self.ctrl.data["cmd_cntr"])
                    self.logger.debug('Robot is running')
                    return True

        return False


    def off(self):
        self._cmd(CTRLR_COMS_POWER, struct.pack("i", CTRLR_COMS_POWER_CMD_OFF))

    def stby(self):
        for i in range(0, 10):
            time.sleep(0.1)
            try:
                if self.ctrl.data["state"] <= 1:
                    self._cmd(CTRLR_COMS_POWER, struct.pack("i", CTRLR_COMS_POWER_CMD_OFF))
                break
            except:
                pass

        self._cmd(CTRLR_COMS_POWER, struct.pack("i", CTRLR_COMS_POWER_CMD_STBY))

        for i in range(0, 200):
            time.sleep(0.1)
            if "state" in self.ctrl.data:
                if self.ctrl.data["state"] == 2:
                    self._cmd_cntr  = int(self.ctrl.data["cmd_cntr"])
                    self.logger.debug('Robot is STBY')
                    return True

        return False

    def write_dig_output(self, n, v):
        dm = [0, 0, 0, 0, 0, 0, 0, 0]
        dv = [0, 0, 0, 0, 0, 0, 0, 0]
        am = [0, 0, 0, 0]
        ac = [0, 0, 0, 0]
        av = [0, 0, 0, 0]

        if n >= self.ctrl.data["dig_out_count"] | n < 0:
            self.logger.debug('Wrong digital output number')
            return

        dm[int(n / 8)] = 1 << (n % 8)
        dv[int(n / 8)] = (1 if v else 0) << (n % 8)

        c = struct.pack("24B4d", *dm, *dv, *am, *ac, *av)
        self._cmd(CTRLR_COMS_SET_OUTPUTS, c)

    def write_an_output(self, n, v, cm):
        dm = [0, 0, 0, 0, 0, 0, 0, 0]
        dv = [0, 0, 0, 0, 0, 0, 0, 0]
        am = [0, 0, 0, 0]
        ac = [0, 0, 0, 0]
        av = [0, 0, 0, 0]

        if n >= self.ctrl.data["an_out_count"] | n < 0:
            self.logger.debug('Wrong analog output number')
            return

        am[n] = 1
        av[n] = v * 1e-3 if cm else v
        ac[n] = 1 if cm else 0

        c = struct.pack("24B4d", *dm, *dv, *am, *ac, *av)
        self._cmd(CTRLR_COMS_SET_OUTPUTS, c)

    def write_an_output_volt(self, n, v):
        self.write_an_output(n, v, False)

    def write_an_output_curr(self, n, v):
        self.write_an_output(n, v, True)

    def read_dig_input(self, n):
        if n >= self.ctrl.data["dig_in_count"] | n < 0:
            self.logger.debug('Wrong digital input number')
            return
        byte = int(n / 8);
        mask = 1 << (n % 8);
        return 1 if self.ctrl.data["dig_in"][byte] & mask != 0 else 0

    def read_an_input(self, n):
        if n >= self.ctrl.data["an_in_count"] | n < 0:
            self.logger.debug('Wrong analog input number')
            return
        v = self.ctrl.data["an_in_value"][n]
        c = self.ctrl.data["an_in_curr_mode"][n]
        return v * 1e3 if c else v

    def init_robot(self):
        if not self._connect():
            self._stop()
        if not self._init_control():
            self._stop()
        if not self.run():
            self._stop()


    def set_gravity(self, v):
        self._cmd(CTRLR_COMS_SET_GRAVITY, struct.pack("3d", *v))

    def set_zg_fscale(self, fs):
        self._cmd(CTRLR_COMS_SET_ZG_FSCALE, struct.pack("6d", *fs))

    def set_trq_win(self, w):
        self._cmd(CTRLR_COMS_SET_TRQ_WIN, struct.pack("6d", *w))

    def set_flw_err(self, j, ct, cr):
        self._cmd(CTRLR_COMS_SET_FLW_ERR, struct.pack("3d", j, ct, cr))

    def set_max_vel(self, j, ct):
        self._cmd(CTRLR_COMS_SET_MAX_VEL, struct.pack("7d", *j, ct))

    def set_payload(self, m, com):
        self._cmd(CTRLR_COMS_SET_PAYLOAD, struct.pack("4d", m, *com))

    def set_tool(self, t):
        self._cmd(CTRLR_COMS_SET_TOOL, struct.pack("6d", *t))

    def set_jog_param(self, in_tcp, force_en, force, spd_max, accel, decel):
        self._cmd(CTRLR_COMS_SET_JOG_PARAM, struct.pack("B6B6d6d6d6d", in_tcp,
                    *force_en, *force, *spd_max, *accel, *decel))

    def set_force_param(self, vi, damp, vmax):
        self._cmd(CTRLR_COMS_SET_FORCE_PARAM, struct.pack("18d", *damp, *vi, *vmax))

    def set_io_func(self, hold_in, zg_in):

        if hold_in[1]:
            hold_in[0] |= 0x80000000
        if zg_in[1]:
            zg_in[0] |= 0x80000000

        self._cmd(CTRLR_COMS_SET_IO_FUNC, struct.pack("2I", hold_in[0], zg_in[0]))

    def set_dh_model(self, dh):
        self._cmd(CTRLR_COMS_SET_DH_MODEL, struct.pack("6d6d6d6d6d", *dh["alpha"], *dh["A"],
                *dh["D"], *dh["theta"], *dh["offset"]))

    def get_dh_model(self):
        self._cmd(CTRLR_COMS_GET_DH_MODEL)
        d = self._resp(CTRLR_COMS_GET_DH_MODEL)

        if len(d) == 0:
            return []

        res = list(struct.unpack("6d6d6d6d6d", d))

        return {"alpha" : res[0:6], "A" : res[6:12],
                "D" : res[12:18],  "theta" : res[18:24],
                "offset" : res[24:30]}

    def fkine(self, q):
        self.socket.settimeout(1)
        self._cmd(CTRLR_COMS_FKINE, struct.pack("6d", *q))
        d = self._resp(CTRLR_COMS_FKINE)

        if len(d) == 0:
            return []

        res = list(struct.unpack("i6d", d))

        if res[0] == 0:
            return res[1:7]
        else:
            return []

    def ikine(self, x):
        self.socket.settimeout(1)
        self._cmd(CTRLR_COMS_IKINE, struct.pack("6d", *x))
        d = self._resp(CTRLR_COMS_IKINE)

        if len(d) == 0:
            return []

        res = list(struct.unpack("i48d", d))

        if res[0] == 0:
            return [res[i*6+1:i*6+7] for i in range(8)]
        else:
            return []

    def set_tool_capsule(self, n, c):
        self._cmd(CTRLR_COMS_SET_TOOL_CAPSULE, struct.pack("2i8d",
            0,  n, *c["start"], c["length"], *c["rot"], c["R"]))

    def set_tool_capsule_count(self, ncap):
        self._cmd(CTRLR_COMS_SET_TOOL_CAPSULE_COUNT, struct.pack("2i", 0, ncap))













