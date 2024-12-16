from mqtt_service import *
from robot import *
import json
import argparse
import math
import collections
from LogTool import LogTool


PD_LEVEL = -1770
C103_LEVEL = [
    -1016,
    -508,
    0,
    508,
    1016,
    1524,
    2032,
    2540,
    3150,
    3658,
    4166,
    4674,
    5182,
    5690,
    6198,
]

C103_COLUMN = [
    [0, 605, 1210, 1815],
    [2515, 3120, 3725, 4330],
    [5030, 5635],
    [7545, 8150, 8755, 9360],
    [10060, 10665, 11270, 11875],
    [12575, 13180, 13785, 14390],
    [15090, 15695, 16300, 16905],
    [17605, 18210, 18815, 19420],
    [20120, 20725],
    [22635, 23240, 23845, 24450],
    [25150, 25755, 26360, 26965],
    [27665, 28270, 28875, 29480],
]

FIRST_BAY = 0
C103_BAY = [
    2515,
    5030,
    7545,
    10060,
    12575,
    15090,
    17605,
    20120,
    # 22635, 25150, 27665, 30180
]

HZ_PD_LEVEL = 1000
HZ_C002_LEVEL = [
    2000,
    0,
    -50,
]


HZ_C002_BAY = [
    2000,
    5000,
    -2000,
]


class Cell:
    offset = -27
    diff = 10

    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z

    def __repr__(self):
        return f"Cell({self.x}, {self.z})"

    def get_load_pos(self):
        return self.z + self.offset - self.diff

    def get_unload_pos(self):
        return self.z + self.offset + self.diff


class Node:
    def __init__(self, x: int, y: int, ori: float = 180, lift: int = 0):
        self.x = x
        self.y = y
        self.ori = ori
        self.lift = lift

    def __repr__(self):
        return f"x: {self.x}, y: {self.y}, ori: {self.ori}, lift: {self.lift}"

    def get_state(self):
        return (self.x, self.y, self.ori, self.lift)


def parse_args():
    parser = argparse.ArgumentParser(description="new-pick-s test arguments")
    parser.add_argument(
        "-i",
        "--server-ip",
        type=str,
        default="10.0.7.136",
        help="MQTT broker ip, default = 10.31.183.153",
    )
    parser.add_argument(
        "-p",
        "--server-port",
        type=int,
        default=1883,
        help="MQTT broker port, default = 1883",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default="EE17G1eA",
        help="MQTT client username, default = ''",
    )
    parser.add_argument(
        "-w",
        "--password",
        type=str,
        default="EE17G1eB",
        help="MQTT client password, default = ''",
    )
    parser.add_argument(
        "-g",
        "--general",
        type=str,
        default="UNKNOWN",
        help="robot's label, default = 'UNKNOWN'",
    )
    parser.add_argument(
        "-a",
        "--ant",
        type=str,
        default="A100",
        help="ant's label, default = 'A100'",
    )
    parser.add_argument(
        "-l",
        "--ladder",
        type=str,
        default="L100",
        help="ladder's label, default = 'L100'",
    )
    parser.add_argument(
        "-s",
        "--spyder",
        type=str,
        default="S100",
        help="spyder's label, default = 'S100'",
    )
    parser.add_argument(
        "-x",
        "--origin-x",
        type=int,
        default="0",
        help="ladder's origin coordx, default = 0",
    )
    parser.add_argument(
        "-c",
        "--cycle-count",
        type=int,
        default=1,
        help="cycle task count",
    )
    return parser.parse_args()


def calculate_angle(x1, y1, x2, y2):
    # Calculate the differences
    delta_x = x2 - x1
    delta_y = y2 - y1

    # Calculate the angle in radians
    theta_radians = math.atan2(delta_y, delta_x)

    # Convert angle to degrees
    theta_degrees = math.degrees(theta_radians)

    # Normalize the angle to be within 0 to 360 degrees
    if theta_degrees < 0:
        theta_degrees += 360

    return theta_degrees


def find_path(start: Node, end: Node) -> list[list]:
    FULL_VEL = 2000
    FULL_ACC = 500

    path = []

    # 计算start - end行走路径的角度，结果范围为[0, 360)
    angle = calculate_angle(start.x, start.y, end.x, end.y)

    # 某些情况下，end点位对机器人角度有特定要求，比如：充电桩需要倒退进入，接驳位需要正向进入
    # 通过定义end点位的orientation，来进行限制
    # 当行进方向与限制方向正好相反时，优先以限制方向进行移动
    if abs(abs(angle - end.ori) - 180) <= 5:
        angle = end.ori

    # 当angle与start点位方向接近时，也无需旋转
    if abs(angle - start.ori) > 5:
        path.append(["SPIN", angle])

    path.append(["MOVE", end.x, end.y, FULL_VEL, FULL_ACC])

    # 当end点位的高度与start点位的高度不同时，需要进行高度调整
    if start.lift != end.lift:
        path.append(["LIFT", end.lift])
    return path


def find_full_path(node_list: list[Node]) -> list[list]:
    FULL_VEL = 2000
    FULL_ACC = 500

    path = []

    n = len(node_list)
    for i in range(n - 1):
        start, end = node_list[i], node_list[i + 1]

        # 计算start - end行走路径的角度，结果范围为[0, 360)
        angle = calculate_angle(start.x, start.y, end.x, end.y)

        # 某些情况下，end点位对机器人角度有特定要求，比如：充电桩需要倒退进入，接驳位需要正向进入
        # 通过定义end点位的orientation，来进行限制
        # 当行进方向与限制方向正好相反时，优先以限制方向进行移动
        if abs(abs(angle - end.ori) - 180) <= 5:
            angle = end.ori

        # 当angle与start点位方向接近时，也无需旋转
        if abs(angle - start.ori) > 5:
            path.append(["SPIN", angle])

        path.append(["MOVE", end.x, end.y, FULL_VEL, FULL_ACC])

        # 当end点位的高度与start点位的高度不同时，需要进行高度调整
        if start.lift != end.lift:
            path.append(["LIFT", end.lift])

        # 更新end点位方向，供后续路径规划
        node_list[i + 1].ori = angle

    return path


def test_pair_generator(nodes: list[Node]):
    commands = []
    for start, end in zip(nodes, nodes[1:]):
        commands += find_path(start, end)
    return commands


class Helper:
    robot_list: list[Robot]
    last_complete_command_label = "UNKNOWN"
    complete_command = collections.defaultdict(str)

    def __init__(self, robot_list: list[Robot], log_flag=False):
        self.robot_list = robot_list
        self.log = LogTool("helper", "helper.log").get_logger()
        self.log_flag = log_flag

    def log_info(self, msg):
        if self.log_flag:
            self.log.info(msg)
        else:
            print(msg)

    def is_robot_state(self, robot: Robot, topic: str):
        return f"robot/state/{robot.robot_label}" == topic

    def is_robot_command_state(self, robot: Robot, topic: str):
        return f"robot/command/status/{robot.robot_label}" == topic

    def mqtt_receive_callback(self, message: MQTTMsg):
        topic, payload = message.topic, json.loads(message.payload)
        for r in self.robot_list:
            if self.is_robot_state(r, topic):
                r.update_state(payload)
                r.state_update_flag = True
                self.log.info(r)
            if self.is_robot_command_state(r, topic):
                if payload["status"] == "COMPLETE_SUCCESS":
                    self.last_complete_command_label = payload["robotCommandLabel"]
                    self.complete_command[r.robot_label] = payload["robotCommandLabel"]
                self.log.info(
                    f"{r.robot_type} {r.robot_label} WORKING ==> {payload['robotCommandLabel']} {payload['status']}"
                )
