import time
import json
import math
from mqtt_service import *
from helper import Helper
from robot import Ant


def get_rotation(current_point: list, next_point: list) -> object:
    """根据当前点和下一个点的坐标，判断旋转方向

    :param current_point: 当前点
    :param next_point: 下一个点
    :return: 旋转方向
    """
    theta = math.atan2(next_point[1] - current_point[1], next_point[0] - current_point[0])
    theta_degrees = math.degrees(theta)
    if theta_degrees < 0:
        theta_degrees += 360
    return theta_degrees


def plan_robot_path(ant_label, initial_ant_position, home_positions, door_positions, ant_path):
    """计算机器人经过的点位

    :param ant_label: 机器人标签, 如"A100"
    :param initial_ant_position: 机器人初始位置
    :param home_positions: 充电位位置
    :param door_positions: 预备充电位位置
    :param ant_path: 机器人路径
    :return: 计算出的机器人路径
    """
    path = []

    if ant_label in initial_ant_position[0]:
        # 找到当前机器人的x，y坐标
        ant_x = initial_ant_position[0][ant_label]['x']
        ant_y = initial_ant_position[0][ant_label]['y']

        # 找到"home"中的下标（在哪个家）
        charge_index = next(
            (i for i, pos in enumerate(home_positions) if pos['x'] == ant_x and pos['y'] == ant_y), None)
        if charge_index is not None:
            # 添加"door_positions"中对应位置，预备充电位
            path.append([door_positions[charge_index]['x'], door_positions[charge_index]['y']])

            for i in ant_path:
                path.append([i['x'], i['y']])

            # 添加"door_positions"中的位置，预备充电位
            path.append([door_positions[charge_index]['x'], door_positions[charge_index]['y']])
            path.append([ant_x, ant_y])
        else:
            print("机器人未找到充电桩")
            path.clear()
            return path
    else:
        print("机器人未找到")
        return path

    # 删除列表中相邻且相同的点
    path = [path[i] for i in range(len(path)) if i == 0 or path[i] != path[i - 1]]
    return path


def plan_robot_action(path, vel, acc, dec, charge_positions, home_positions):
    """计算机器人动作

    :param path: 机器人路径
    :param vel: 机器人速度
    :param acc: 机器人加速度
    :param dec: 机器人减速度
    :param charge_positions: 充电位
    :param home_positions: 初始位置
    :return: 计算出的机器人动作
    """
    actions = [["MOVE", path[0][0], path[0][1], vel, acc, dec]]
    current_position = path[0]

    for i in range(len(path)):
        next_position = path[i]
        if current_position != next_position:
            direction = get_rotation(current_position, next_position)
            # 计算下个点位是不是充电位
            charge_index = next((i for i, pos in enumerate(charge_positions) if
                                 pos['x'] == next_position[0] and pos['y'] == next_position[1]), None)
            # 计算下个点位是不是初始位
            home_index = next((i for i, pos in enumerate(home_positions) if
                               pos['x'] == next_position[0] and pos['y'] == next_position[1]), None)
            if charge_index is not None or home_index is not None:
                if int(direction) <= 180:
                    actions.append(["SPIN", int(direction) + 180])
                else:
                    actions.append(["SPIN", int(direction) - 180])
                actions.append(["MOVE", next_position[0], next_position[1], vel, acc, dec])

                # 如果充电位，添加等待
                if charge_index is not None:
                    actions.append(["WAIT", 20])
            else:
                actions.append(["SPIN", int(direction)])
                actions.append(["MOVE", next_position[0], next_position[1], vel, acc, dec])
            current_position = next_position
    return actions


def main():
    ant_vel = 2000
    ant_acc = 800
    ant_dec = 800
    robot_list = []
    robots = []

    with open('test_ant_party.json', 'r') as file:
        data = json.load(file)

    for i in data["initial_ant_position"][0]:
        robot_list.append(i)

    # 创建蚂蚁机器人
    for robot in robot_list:
        robots.append(
            {
                'ant': Ant(robot),
                'path': [],
                'init_msg': [
                    data['initial_ant_position'][0][robot]['x'],
                    data['initial_ant_position'][0][robot]['y'],
                    data['initial_ant_position'][0][robot]['ori'],
                    0
                ]
            }
        )

    # 计算机器人路径
    for robot in robots:
        path = plan_robot_path(
            robot['ant'].robot_label,
            data['initial_ant_position'],
            data['home_positions'],
            data['door_positions'],
            data['ant_path']
        )
        robot['path'] = plan_robot_action(path, ant_vel, ant_acc, ant_dec, data['charge_positions'], data['home_positions'])

    # 注册MQTT
    helper = Helper(robot_list=[robot['ant'] for robot in robots])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(
        host=data['server_ip'],
        port=data['server_port'],
        username=data['username'],
        password=data['password'],
    )
    for robot in robots:
        mqtt_client.add_robot(robot['ant'].robot_label)

    # 机器人初始化
    for robot in robots:
        while not robot['ant'].state_update_flag:
            time.sleep(1)

        print(f'robot state: {robot["ant"].state}')
        if robot['ant'].state == "UNKNOWN":
            msg = build_robot_command_set(robot_label=robot['ant'].robot_label, command_type="INIT")
            last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
            mqtt_client.publish(robot_label=robot['ant'].robot_label, topic=msg.topic, payload=msg.payload)
            time.sleep(2)

            while helper.last_complete_command_label != last_command_label:
                time.sleep(1)

    for i in range(10):
        for robot in robots:
            while robot['ant'].state != "IDLE":
                time.sleep(1)

            for pos in robot['path']:
                if pos[0] == 'WAIT':
                    time.sleep(pos[1])
                    continue

                msg = build_ant_action_command_set(
                    robot_label=robot['ant'].robot_label,
                    init_pos=robot['init_msg'],
                    command_param=[pos]
                )
                last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
                mqtt_client.publish(
                    robot_label=robot['ant'].robot_label,
                    topic=msg.topic,
                    payload=msg.payload,
                )
                while helper.last_complete_command_label != last_command_label:
                    time.sleep(1)

                if pos[0] == 'MOVE':
                    robot['init_msg'][0] = pos[1]
                    robot['init_msg'][1] = pos[2]
                if pos[0] == 'SPIN':
                    robot['init_msg'][2] = pos[1]

        print(i+1, flush=True)

    mqtt_client.stop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
