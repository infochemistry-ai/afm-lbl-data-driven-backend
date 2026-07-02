import sys
import threading
import socket
import numpy as np

from api import RobotAPI
from time import sleep, time
from math import degrees


robot_ip = '192.168.125.10'
robot = RobotAPI(ip=robot_ip)

if robot.socket:
    try:
        robot.socket.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        robot.socket.close()
    finally:
        robot.socket = None

robot.init_robot()
robot.hold()
robot.set_payload(0.7, [0, 0, 0.060])
robot.set_tool([0, 0, 0, 0, 0, 0])
robot.set_speed_scaling(1)
robot.set_accel_scaling(1)

# point_j = [deg]
# point = [m, deg]
point_home_j = [210, -32, 245, -105, 90, -230]
point_common = [-0.600, 0, 0.530, 180, 0, -135]
point_common_j = [192.98, -94.15, 271.44, -87.32, 90.01, -121.98]
point_plate_box_start_open_help_j = [193.81, -111.13, 267.77, -156.64, -76.19, 45.0]
point_plate_box_start_open = [-0.68212, 0.01139, 0.32161, 90, -45, -90]
point_tweezers_in = [-0.66018, 0.12504, 0.37952, 90, 45, 180]
point_plate_take = [-0.67191, -0.03926, 0.2901, 90, 38.2, -90]
point_bottle_above = [-0.648, 0.0535, 0.330, 90, 38.2, -135]
point_tweezers_return_help_j = [202.58, -121.96, 294.05, -172.1, 22.58, -45.0]
point_tweezers_return_help_j_2 = [213, -127, 302.7, -175.6, 33, -45.0]

point_dish_up_help_j_1 = [216.34, -102.17, 251.0, -148.83, -53.66, -225.0]
point_dish_up_help_j_2 = [216.34, -106.11, 246.89, -140.78, -53.66, -225.0]
point_dish_take_base = [-0.544, -0.135, 0.237, -90, -45, 90]
point_dish_up_help_j_3 = [216.34, -103.18, 249.77, -146.59, -53.66, -45.0]
point_dish_up_help_j_4 = [216.34, -105.58, 247.34, -141.75, -53.66, -45.0]
point_dish_take_cap = [-0.544, -0.135, 0.233, 90, 45, -90]

point_dish_drop_help_j_1 = [228.35, -104.73, 226.72, -121.98, 18.36, -45.0]
point_dish_drop_help_j_2 = [228.35, -112.69, 224.39, -111.7, 18.35, -45.0]
point_dish_drop_base = [-0.37348, -0.02743, 0.07998, 90, 45, -150]

point_dish_take_ready = [-0.48349, 0.16951, 0.31499, -180, 0, -106]
point_plate_pre_drop = [-0.549, -0.088, 0.143, -90, 83, 0]
point_plate_pre_drop_j = [215.08, -131.35, 270.22, -138.87, 35.08, -97.0]

point_dish_drop_out = [-0.411, -0.119, 0.224, -180, -0, -45]


flag_rotator_initialized = False
rotator_message_received = ''
rotator_value_desired_message = ''
flag_gripper_initialized = False
gripper_message_received = ''
gripper_value = -1
rotator_value = -1
rotator_value_desired = 0
flag_socket_gripper_close = False
flag_socket_rotator_close = False
step = 0
time_in_liquid = time()
time_in_liquid_print = time()
passed_time_in_liquid = 0
flag_start_timer_in_liquid = True
rotator_rounds = 0
counter_plate = 0
counter_workflows = 0


def gripper_communication():
    global flag_gripper_initialized, gripper_message_received, gripper_value
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('', 7000))
        sock.listen()
        print('Server port 7000 is running')
        conn, addr = sock.accept()
        with conn:
            print(f'Сonnected to port 7000: {addr}')
            while True:
                if not flag_gripper_initialized:
                    gripper_message_received = conn.recv(1024).decode('utf8')
                    if gripper_message_received == 'ready':
                        flag_gripper_initialized = True
                else:
                    if gripper_value != -1:
                        conn.sendall(bytes(str(gripper_value), encoding='UTF-8'))
                        gripper_message_received = conn.recv(1024).decode('utf8')
                        gripper_value = -1
                if flag_socket_gripper_close:
                    sock.close()
                    break
                sleep(0.1)

def rotator_communication():
    global flag_rotator_initialized, rotator_message_received, rotator_value
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('', 6000))
        sock.listen()
        print('Server port 6000 is running')
        conn, addr = sock.accept()
        with conn:
            print(f'Сonnected to port 6000: {addr}')
            while True:
                if not flag_rotator_initialized:
                    rotator_message_received = conn.recv(1024).decode('utf8')
                    if rotator_message_received == 'ready':
                        flag_rotator_initialized = True
                else:
                    if rotator_value != -1:
                        conn.sendall(bytes(str(rotator_value), encoding='UTF-8'))
                        rotator_message_received = conn.recv(1024).decode('utf8')
                        rotator_value = -1
                if flag_socket_rotator_close:
                    sock.close()
                    break
                sleep(0.1)

thread_socket_gripper = threading.Thread(target=gripper_communication, args=(), name='thread-socket-gripper')
thread_socket_gripper.start()

thread_socket_rotator = threading.Thread(target=rotator_communication, args=(), name='thread-socket-rotator')
thread_socket_rotator.start()



while True:
    try:
        if step == 0:
            print("step: {0}".format(step))
            robot.vars.vmax_t, robot.vars.amax_t = 2.5, 2.5
            robot.vars.vmax_j, robot.vars.amax_j = 2.5, 2.5
            robot.vars.vmax_r, robot.vars.amax_r = 2.5, 2.5
            robot.vars.rblend = 0
            robot.vars.t = 0
            robot.add_wp_deg(t=0, des_q=point_home_j, vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            rotator_value = 0
            gripper_value = 180
            step = 1

        if (step == 1) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            rotator_value_desired = 1
            step = 2

        if (step == 2) and (gripper_message_received == 'RotateTo180') and (rotator_message_received == 'CurPos:0') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.080, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=point_tweezers_in, vmax_t=0.05, amax_t=0.05, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1], point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.1, amax_t=0.5, rblend=0.030)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1] - 0.150, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.1, amax_t=0.5, rblend=0.050)
            robot.add_wp_deg(t=0, des_q=point_plate_box_start_open_help_j, vmax_j=2.5, amax_j=2.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] - 0.037, point_plate_box_start_open[1], point_plate_box_start_open[2], point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.run_wps()
            step = 3

        if (step == 3) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 43
            step = 4

        if (step == 4) and (gripper_message_received == 'RotateTo43') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] + 0.010, point_plate_box_start_open[1] - 0.060 + (counter_plate * 0.084 / 6), point_plate_box_start_open[2] + 0.020, point_plate_box_start_open[3], point_plate_box_start_open[4] + 90, point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_take[0], point_plate_take[1] + (counter_plate * 0.084 / 6), point_plate_take[2] + 0.035, point_plate_take[3], point_plate_take[4], point_plate_take[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_take[0], point_plate_take[1] + (counter_plate * 0.084 / 6), point_plate_take[2], point_plate_take[3], point_plate_take[4], point_plate_take[5]], vmax_t=0.01, amax_t=0.1, rblend=0.001)
            robot.add_wp_deg(t=1, des_x=[point_plate_take[0], point_plate_take[1] + 0.003 + (counter_plate * 0.084 / 6), point_plate_take[2], point_plate_take[3], point_plate_take[4], point_plate_take[5]], vmax_t=0.01, amax_t=0.1, rblend=0)
            robot.run_wps()
            step = 5

        if (step == 5) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 26
            step = 6

        if (step == 6) and (gripper_message_received == 'RotateTo26') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(1.2)
            robot.add_wp_deg(t=1, des_x=[point_plate_take[0], point_plate_take[1] + 0.010 + (counter_plate * 0.084 / 6), point_plate_take[2] + 0.035, point_plate_take[3], point_plate_take[4], point_plate_take[5]], vmax_t=0.01, amax_t=0.1, rblend=0)
            robot.run_wps()
            step = 7

        if (step == 7) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0], point_plate_box_start_open[1], point_plate_box_start_open[2], point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] - 0.059, point_plate_box_start_open[1], point_plate_box_start_open[2], point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] - 0.059, point_plate_box_start_open[1], point_plate_box_start_open[2] - 0.024, point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] - 0.019, point_plate_box_start_open[1], point_plate_box_start_open[2] - 0.024, point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_box_start_open[0] - 0.025, point_plate_box_start_open[1], point_plate_box_start_open[2] + 0.040, point_plate_box_start_open[3], point_plate_box_start_open[4], point_plate_box_start_open[5]], vmax_t=0.1, amax_t=0.1, rblend=0.100)
            robot.add_wp_deg(t=1, des_x=[point_bottle_above[0], point_bottle_above[1], point_plate_box_start_open[2] + 0.040, point_bottle_above[3], point_plate_box_start_open[4], point_bottle_above[5]], vmax_t=3.0, amax_t=3.0, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_bottle_above[0], point_bottle_above[1], point_bottle_above[2] - 0.050, point_bottle_above[3], point_bottle_above[4], point_bottle_above[5]], vmax_t=3.0, amax_t=3.0, rblend=0)
            robot.run_wps()
            step = 8

        if (step == 8) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            rotator_value = rotator_value_desired
            rotator_value_desired_message = 'CurPos:' + str(rotator_value_desired)
            step = 9

        if (step == 9) and (rotator_message_received == rotator_value_desired_message) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_bottle_above[0], point_bottle_above[1], point_bottle_above[2] - 0.110, point_bottle_above[3], point_bottle_above[4], point_bottle_above[5]], vmax_t=0.02, amax_t=0.02, rblend=0)
            robot.run_wps()
            step = 10

        if (step == 10) and (robot.is_motion_stopped()):
            if flag_start_timer_in_liquid:
                print("step: {0}".format(step))
                time_in_liquid_print = time()
                time_in_liquid = time()
                flag_start_timer_in_liquid = False
                passed_time_in_liquid = 0

            if time() - time_in_liquid_print >= 1:
                passed_time_in_liquid = passed_time_in_liquid + (time() - time_in_liquid_print)
                remaining_time = 5 * 60 - passed_time_in_liquid
                print("Left, sec: {0}".format(round(remaining_time)))
                time_in_liquid_print = time()

            if time() - time_in_liquid >= 5 * 60:
                flag_start_timer_in_liquid = True
                robot.add_wp_deg(t=1, des_x=[point_bottle_above[0], point_bottle_above[1], point_bottle_above[2] - 0.050, point_bottle_above[3], point_bottle_above[4], point_bottle_above[5]], vmax_t=0.02, amax_t=0.02, rblend=0)
                robot.run_wps()
                rotator_value_desired += 2
                if rotator_value_desired == 9:
                    rotator_value_desired = 1
                    rotator_rounds += 1
                step = 11 if (rotator_rounds == 2) else 8
                rotator_rounds = rotator_rounds if (rotator_rounds < 2) else 0

        if (step == 11) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            rotator_value = 0
            robot.add_wp_deg(t=0, des_q=point_tweezers_return_help_j, vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 12

        if (step == 12) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 180
            step = 13

        if (step == 13) and (gripper_message_received == 'RotateTo180') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1], point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.2, amax_t=0.2, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.0015, point_tweezers_in[2] + 0.001, point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.02, amax_t=0.02, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.150, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.2, amax_t=0.2, rblend=0)
            robot.run_wps()
            step = 14

        if (step == 14) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_1, vmax_j=3.0, amax_j=3.0, rblend=0.080)
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_2, vmax_j=3.0, amax_j=3.0, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_base[0], point_dish_take_base[1], point_dish_take_base[2] - (counter_plate * 0.094 / 6), point_dish_take_base[3], point_dish_take_base[4], point_dish_take_base[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 15

        if (step == 15) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 155
            step = 16

        if (step == 16) and (gripper_message_received == 'RotateTo155') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(1.0)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_base[0], point_dish_take_base[1], point_dish_take_base[2] + (counter_plate * 0.094 / 6), point_dish_take_base[3], point_dish_take_base[4], point_dish_take_base[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_1, vmax_j=3.0, amax_j=3.0, rblend=0.070)
            robot.add_wp_deg(t=0, des_q=point_dish_drop_help_j_1, vmax_t=1.5, amax_t=1.5, amax_j=1.5, amax_r=1.5, rblend=0.080)
            robot.add_wp_deg(t=0, des_q=point_dish_drop_help_j_2, vmax_t=1.5, amax_t=1.3, amax_j=1.5, amax_r=1.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=point_dish_drop_base, vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 17

        if (step == 17) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 180
            step = 18

        if (step == 18) and (gripper_message_received == 'RotateTo180') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(1.0)
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_base[0], point_dish_drop_base[1], point_dish_drop_base[2] + 0.170, point_dish_drop_base[3], point_dish_drop_base[4], point_dish_drop_base[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.100, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.5, amax_t=0.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=point_tweezers_in, vmax_t=0.05, amax_t=0.05, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1], point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.1, amax_t=0.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1] - 0.230, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=1.0, amax_t=0.5, rblend=0)
            robot.run_wps()
            step = 19

        if (step == 19) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=0, des_q=point_plate_pre_drop_j, vmax_j=1.0, amax_j=1.0, rblend=0)
            robot.run_wps()
            gripper_value = 30
            step = 20

        if (step == 20) and (gripper_message_received == 'RotateTo30') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_plate_pre_drop[0], point_plate_pre_drop[1] + 0.016, point_plate_pre_drop[2], point_plate_pre_drop[3], point_plate_pre_drop[4] + 3, point_plate_pre_drop[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_pre_drop[0] + 0.005, point_plate_pre_drop[1] + 0.016, point_plate_pre_drop[2] - 0.007, point_plate_pre_drop[3], point_plate_pre_drop[4] + 3, point_plate_pre_drop[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_pre_drop[0] + 0.005, point_plate_pre_drop[1] + 0.030, point_plate_pre_drop[2] - 0.007, point_plate_pre_drop[3], point_plate_pre_drop[4] + 3, point_plate_pre_drop[5]], vmax_t=0.01, amax_t=0.01, rblend=0)
            robot.run_wps()
            step = 21

        if (step == 21) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(0.5)
            robot.add_wp_deg(t=1, des_x=[point_plate_pre_drop[0] + 0.005, point_plate_pre_drop[1] + 0.016, point_plate_pre_drop[2] - 0.007, point_plate_pre_drop[3], point_plate_pre_drop[4] + 3, point_plate_pre_drop[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_plate_pre_drop[0], point_plate_pre_drop[1] + 0.016, point_plate_pre_drop[2], point_plate_pre_drop[3], point_plate_pre_drop[4] + 3, point_plate_pre_drop[5]], vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.add_wp_deg(t=1, des_x=point_plate_pre_drop, vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.run_wps()
            step = 22

        if (step == 22) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=0, des_q=point_tweezers_return_help_j_2, vmax_t=2.5, amax_t=2.5, rblend=0)
            robot.run_wps()
            gripper_value = 180
            step = 23

        if (step == 23) and (gripper_message_received == 'RotateTo180') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0] + 0.050, point_tweezers_in[1], point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.2, amax_t=0.2, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.0015, point_tweezers_in[2] + 0.001, point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.02, amax_t=0.02, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_tweezers_in[0], point_tweezers_in[1] - 0.150, point_tweezers_in[2], point_tweezers_in[3], point_tweezers_in[4], point_tweezers_in[5]], vmax_t=0.2, amax_t=0.2, rblend=0)
            robot.run_wps()
            step = 24

        if (step == 24) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_3, vmax_t=0.5, amax_t=0.3, amax_j=1.5, amax_r=1.5, rblend=0.060)
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_4, vmax_t=0.5, amax_t=0.3, amax_j=1.5, amax_r=1.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_cap[0], point_dish_take_cap[1], point_dish_take_cap[2] - (counter_plate * 0.092 / 6), point_dish_take_cap[3], point_dish_take_cap[4], point_dish_take_cap[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 25

        if (step == 25) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 145
            step = 26

        if (step == 26) and (gripper_message_received == 'RotateTo145') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(1.0)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_cap[0], point_dish_take_cap[1], point_dish_take_cap[2] + (counter_plate * 0.092 / 6), point_dish_take_cap[3], point_dish_take_cap[4], point_dish_take_cap[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.add_wp_deg(t=0, des_q=point_dish_up_help_j_3, vmax_t=0.5, amax_t=0.3, amax_j=1.5, amax_r=1.5, rblend=0.050)
            robot.add_wp_deg(t=0, des_q=point_dish_drop_help_j_1, vmax_t=0.5, amax_t=0.3, amax_j=1.5, amax_r=1.5, rblend=0.080)
            robot.add_wp_deg(t=0, des_q=point_dish_drop_help_j_2, vmax_t=0.5, amax_t=0.3, amax_j=1.5, amax_r=1.5, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_base[0], point_dish_drop_base[1], point_dish_drop_base[2] + 0.033, point_dish_drop_base[3], point_dish_drop_base[4], point_dish_drop_base[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 27

        if (step == 27) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 180
            step = 28

        if (step == 28) and (gripper_message_received == 'RotateTo180') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(0.2)
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_base[0] + 0.050, point_dish_drop_base[1] - 0.050, point_dish_drop_base[2] + 0.083, point_dish_drop_base[3], point_dish_drop_base[4], point_dish_drop_base[5]], vmax_t=0.3, amax_t=0.05, amax_j=0.7, amax_r=0.7, rblend=0.030)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_ready[0] + 0.030, point_dish_take_ready[1] - 0.060, point_dish_take_ready[2] + 0.050, point_dish_take_ready[3], point_dish_take_ready[4], point_dish_take_ready[5]], vmax_t=0.3, amax_t=0.05, amax_j=0.7, amax_r=0.7, rblend=0.030)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_ready[0], point_dish_take_ready[1], point_dish_take_ready[2] + 0.050, point_dish_take_ready[3], point_dish_take_ready[4], point_dish_take_ready[5]], vmax_t=0.3, amax_t=0.05, amax_j=0.7, amax_r=0.7, rblend=0.030)
            robot.add_wp_deg(t=1, des_x=point_dish_take_ready, vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 29

        if (step == 29) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 155
            step = 30

        if (step == 30) and (gripper_message_received == 'RotateTo155') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            sleep(0.5)
            robot.add_wp_deg(t=1, des_x=[point_dish_take_ready[0], point_dish_take_ready[1], point_dish_take_ready[2] + 0.050, point_dish_take_ready[3], point_dish_take_ready[4], point_dish_take_ready[5]], vmax_t=0.3, amax_t=0.05, amax_j=0.7, amax_r=0.7, rblend=0.030)
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_out[0], point_dish_drop_out[1], point_dish_take_ready[2] + 0.050, point_dish_drop_out[3], point_dish_drop_out[4], point_dish_drop_out[5]], vmax_t=0.3, amax_t=0.05, amax_j=0.7, amax_r=0.7, rblend=0.100)
            robot.add_wp_deg(t=1, des_x=point_dish_drop_out, vmax_t=0.3, amax_t=0.05, rblend=0)
            robot.run_wps()
            step = 31

        if (step == 31) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 170
            step = 32

        if (step == 32) and (gripper_message_received == 'RotateTo170') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_out[0] - 0.050, point_dish_drop_out[1], point_dish_drop_out[2], point_dish_drop_out[3], point_dish_drop_out[4], point_dish_drop_out[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 33

        if (step == 33) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 80
            step = 34

        if (step == 34) and (gripper_message_received == 'RotateTo80') and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_out[0] + 0.024, point_dish_drop_out[1], point_dish_drop_out[2], point_dish_drop_out[3], point_dish_drop_out[4], point_dish_drop_out[5]], vmax_t=0.05, amax_t=0.05, rblend=0)
            robot.add_wp_deg(t=1, des_x=[point_dish_drop_out[0] - 0.050, point_dish_drop_out[1], point_dish_drop_out[2] + 0.030, point_dish_drop_out[3], point_dish_drop_out[4], point_dish_drop_out[5]], vmax_t=0.3, amax_t=0.3, rblend=0)
            robot.run_wps()
            step = 35

        if (step == 35) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            gripper_value = 180
            counter_plate += 1
            step = 36 if counter_plate == 7 else 2
            counter_plate = counter_plate if counter_plate != 7 else 0

        if (step == 36) and (robot.is_motion_stopped()):
            print("step: {0}".format(step))
            robot.add_wp_deg(t=0, des_q=point_home_j, vmax_t=0.1, amax_t=0.1, rblend=0)
            robot.run_wps()
            step = 37

        sleep(0.01)

    except Exception as e:
        print("!!! ERROR: {0} !!!".format(e))
