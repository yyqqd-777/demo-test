import time
import json
from mqtt_service import *
from helper import Helper
from robot import Ant


def main():
    robots = []
    with open('test_ant_lift.json', 'r') as file:
        data = json.load(file)

    # 创建蚂蚁机器人
    for robot in data['ant_labels']:
        robots.append(
            {
                'ant': Ant(robot),
                'init_msg': [
                    data['initial_ant_position'][0][robot]['x'],
                    data['initial_ant_position'][0][robot]['y'],
                    data['initial_ant_position'][0][robot]['ori'],
                    0
                ]
            }
        )

    # 计算机器人路径
    robot_path = [
        ['LIFT', 370],
        ['LIFT', 0]
    ]

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
        while robot['ant'].state != "IDLE":
            print(f'robot state: {robot["ant"].state}')
            msg = build_robot_command_set(robot_label=robot['ant'].robot_label, command_type="INIT")
            mqtt_client.publish(robot_label=robot['ant'].robot_label, topic=msg.topic, payload=msg.payload)

            time.sleep(2)

    for i in range(500):
        for path in robot_path:
            for robot in robots:
                while robot['ant'].state != "IDLE":
                    time.sleep(1)

                msg = build_ant_action_command_set(
                    robot_label=robot['ant'].robot_label,
                    init_pos=robot['init_msg'],
                    command_param=[path]
                )
                last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
                mqtt_client.publish(
                    robot_label=robot['ant'].robot_label,
                    topic=msg.topic,
                    payload=msg.payload,
                )
                while helper.last_complete_command_label != last_command_label:
                    time.sleep(1)

                if path[0] == 'LIFT':
                    robot['init_msg'][3] = path[1]

            time.sleep(10)
        print(i+1, flush=True)

    mqtt_client.stop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

