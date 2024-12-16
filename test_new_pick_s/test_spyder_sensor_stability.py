import time
from mqtt_service import *
from robot import *
from helper import *


"""机器人路径

example: 
    ['MOVE', init_postion, [target_postion, vel, acc], load_sensor_front, load_sensor_rear]
    ['LOAD', init_postion, load(True or False), forward(True or False), 764]
    ['UNLOAD', init_postion, load(True or False), forward(True or False), 824]

"""
# 机器人路径
robot_path = [
    ['MOVE', 200, [205, 1000, 500], False, False],
    ['LOAD', 205, True, True, 764],
    ['MOVE', 205, [195, 1000, 500], True, True],
    ['UNLOAD', 195, False, False, 824]
]


def main(args):
    spyder = Spyder(args.spyder)
    helper = Helper(robot_list=[spyder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port, username=args.username, password=args.password)
    mqtt_client.add_robot(spyder.robot_label)

    # 机器人初始化
    while not spyder.state_update_flag:
            time.sleep(1)

    # robot init
    if spyder.state == "UNKNOWN":
        msg = build_robot_command_set(robot_label=spyder.robot_label, command_type="INIT")
        last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        mqtt_client.publish(robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

        while helper.last_complete_command_label != last_command_label:
            time.sleep(1)
        helper.last_complete_command_label = "UNKNOWN"

    # robot homing set position
    while spyder.state != "LOCATION_UNKNOWN":
        time.sleep(1)

    msg = build_spyder_home_command_set(robot_label=spyder.robot_label, command_type="HOME_SPYDER_MOVE_SCAN", distanceToDmCodes=200, originOffset=0)
    mqtt_client.publish(robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

    while helper.last_complete_command_label != last_command_label:
            time.sleep(1)

    # robot homing move 
    while spyder.state != "LOCATION_UNKNOWN":
        time.sleep(1)

    msg = build_spyder_home_command_set(robot_label=spyder.robot_label, command_type="HOME_SET_ORIGIN", distanceToDmCodes=0, originOffset=0)
    mqtt_client.publish(robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

    while helper.last_complete_command_label != last_command_label:
            time.sleep(1)

    # 机器人开始循环运行
    for i in range(10):
        for i in robot_path:
            while spyder.state != "IDLE":
                time.sleep(1)

            if i[0] == 'MOVE':
                msg = build_spyder_move_command_set(robot_label=spyder.robot_label, init_pos=i[1], command_param=i[2], load_sensor_front=i[3], load_sensor_rear=i[4])

            if i[0] == 'LOAD' or i[0] == 'UNLOAD':
                msg = build_spyder_action_command_set(robot_label=spyder.robot_label, init_pos=i[1], load=i[2], forward=i[3], distance=i[4])

            last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
            mqtt_client.publish(robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)
            while helper.last_complete_command_label != last_command_label:
                time.sleep(1)

    mqtt_client.stop()

