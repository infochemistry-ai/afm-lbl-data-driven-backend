#!/usr/bin/env python

import socket
import struct
import logging
import logging
from threading import Thread
import threading
import sys

PORT_INPUT = 29000 

PARAMETERS_LIST = (
    ("cycle_time", 1),
    ("cycle_duty", 1),
    ("state", 1),
    ("servo_mode", 1),
    ("motion_mode", 1),
    ("jcond", 1),
    ("buff_sz", 1),
    ("buff_fill", 1),
    ("cmd_cntr", 1),
    ("res0", 1),
    ("move_des_q", 6),
    ("move_des_qd", 6),
    ("move_des_x", 6),
    ("move_des_xd", 6),
    ("act_q", 6),
    ("act_qd", 6),
    ("act_x", 6),
    ("act_xd", 6),
    ("act_tq", 6),
    ("frict_t", 6),
    ("act_ext_tq", 6),
    ("act_force_e", 6),
    ("act_force_0", 6),
    ("des_trq", 6),
    ("des_qd", 6),
    ("temp_m", 6),
    ("temp_e", 6),
    ("arm_current", 1),
    ("arm_voltage", 1),
    ("psu_voltage", 1),
    ("dig_in_count", 1),
    ("an_in_count", 1),
    ("dig_in", 8),
    ("an_in_curr_mode", 4),
    ("an_in_value", 4),
    ("dig_out_count", 1),
    ("an_out_count", 1),
    ("dig_out", 8),
    ("an_out_curr_mode", 4),
    ("an_out_value", 4)
)

STRUCT_FORMAT = "6d4H105d14b4d14b4d"


class Control:
    def __init__(self, ip, port=PORT_INPUT):
        self.data = {}
        self.ip = ip
        self.port = port
        self.is_run = False
        self.sd = None
        self._struct_size = struct.calcsize(STRUCT_FORMAT)
        self.logger = logging
        self.run = True

    def _connect(self):
        try:
            self.sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sd.connect((self.ip, self.port))
            self.sd.settimeout(1)
            logging.debug(f"Socket connect [{self.ip}:{self.port}] --> Ok")
        except Exception as error:
            logging.debug(f"Socket connect [{self.ip}:{self.port}] --> False\n{error}")
            self.run = False
            sys.exit()

    def _recv(self, l):
        d = self.sd.recv(l)
        if d == b'':
            print("RTD connection lost")
            self.run = False
            sys.exit()
        
        return d

    def _recive_data(self):
        try:
            raw_data = self._recv(self._struct_size)
                
            while len(raw_data) < self._struct_size:             
                chunk = self._recv(self._struct_size - len(raw_data))
                raw_data += chunk
                        
            unpack_data = struct.unpack(STRUCT_FORMAT, raw_data)
            
            n = 0
            for i, p in enumerate(PARAMETERS_LIST):
                if p[1] > 1:
                    self.data[p[0]] = unpack_data[n:n+p[1]]
                else:
                    self.data[p[0]] = unpack_data[n]
                n += p[1]
                           
        except Exception as error:
            self.logger.error(error)
            self.run = False
            sys.exit()

    def _thread(self, main_thread):
        self.logger.debug("Recive data thread started")
        while self.run:
            if not main_thread.is_alive():
                self.sd.close()
                break
            self._recive_data()
        self.logger.debug("Recive data thread stopped")

    def start_thread(self):
        self._connect()
        if not self.sd:
            return False
        thread = threading.Thread(target=self._thread, args=(threading.current_thread(),))
        thread.start()
        return True
    

