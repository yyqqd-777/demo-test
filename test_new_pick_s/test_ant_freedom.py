import time
import json
from mqtt_service import *
from helper import Helper
from robot import Ant
robot_dict = {
    'speed': 2000,
    'acc': 650,
    'dec': 500
}
'''
机器人路径
example:
    ['MOVE', 106000, 102000, 2000, 500],
    ['SPIN', 180],
    ['LIFT', 370],
'''
robot_path = [
    # # 二楼模拟出入充电位及接驳位(入库取货)
    # ['MOVE', 109000, 105000, robot_dict['speed'], robot_dict['acc']],
    # ['MOVE', 109000, 104000, robot_dict['speed'], robot_dict['acc']],
    # ['LIFT', 370],
    # ['MOVE', 109000, 105000, robot_dict['speed'], robot_dict['acc']],
    # ['LIFT', 0],
    # ['SPIN', 90],
    # ['MOVE', 109000, 113000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 270],
    # ['MOVE', 109000, 114000, robot_dict['speed'], robot_dict['acc']]
    # #二楼模拟出入充电位及接驳位(运货入库)
    # ['MOVE', 109000, 105000, robot_dict['speed'], robot_dict['acc']],
    # ['LIFT', 370],
    # ['MOVE', 109000, 104000, robot_dict['speed'], robot_dict['acc']],
    # ['LIFT', 0],
    # ['MOVE', 109000, 105000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 90],
    # ['MOVE', 109000, 113000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 270],
    # ['MOVE', 109000, 114000, robot_dict['speed'], robot_dict['acc']]


    # #二楼 连续转向（3米）
    # ['MOVE', 108000, 106000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 90],
    # ['MOVE', 108000, 109000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 180],  # 屏幕朝向工位
    # ['MOVE', 105000, 109000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 270],
    # ['MOVE', 105000, 106000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 0]

    #二楼 连续转向（1米）
    # ['MOVE', 107000, 102000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 90],
    # ['MOVE', 107000, 103000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 180], #屏幕朝向工位（二楼）
    # ['MOVE', 106000, 103000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 270],
    # ['MOVE', 106000, 102000, robot_dict['speed'], robot_dict['acc']],
    # ['SPIN', 0]

    #二楼直线往返（直行）
    ['MOVE', 106000, 113000, robot_dict['speed'], robot_dict['acc']],
    ['SPIN', 270],#屏幕朝向货梯
    ['MOVE', 106000, 102000, robot_dict['speed'], robot_dict['acc']],
    ['SPIN', 90]

]
def main():
    robots = []
    with open('test_ant_freedom.json', 'r') as file:
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
    for i in range(20):
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
                if path[0] == 'MOVE':
                    robot['init_msg'][0] = path[1]
                    robot['init_msg'][1] = path[2]
                if path[0] == 'SPIN':
                    robot['init_msg'][2] = path[1]
            time.sleep(3)
        print(i+1, flush=True)
        # time.sleep(30)
    mqtt_client.stop()
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass