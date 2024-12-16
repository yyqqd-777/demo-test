import time
from mqtt_service import *
from robot import *
from helper import *

mqtt_dict = {
    "server_ip": "10.0.7.136",
    "server_port": 1883,
    "username": "EE17G1eA",
    "password": "EE17G1eB"
}

spyder_list = ['S360'] 
# spyder_list = ['S351', 'S352']
# spyder_list = ['S351', 'S352']
# spyder_list = ['S353', 'S354']
# spyder_list = ['S355', 'S356']
# spyder_list = ['S358', 'S359']
# spyder_list = ['S361', 'S360']
# spyder_list = ['S362', 'S363']
# spyder_list = ['S364', 'S365']
# spyder_list = ['S360', 'S367']
robots = []


def main():
    # 创建机器人
    for robot in spyder_list:
        robots.append(
            {
                'label': Spyder(robot)
            }
        )

    # 注册MQTT
    helper = Helper(robot_list=[robot['label'] for robot in robots])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(
        host=mqtt_dict['server_ip'],
        port=mqtt_dict['server_port'],
        username=mqtt_dict['username'],
        password=mqtt_dict['password']
    )
    for robot in robots:
        mqtt_client.add_robot(robot['label'].robot_label)

    # 机器人初始化
    for robot in robots:
        while not robot['label'].state_update_flag:
            time.sleep(1)

        if robot['label'].state == "UNKNOWN":
            print(f"robot {robot['label'].robot_label} state is UNKNOWN, please check it!")
            msg = build_robot_command_set(robot_label=robot['label'].robot_label, command_type="INIT")
            last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
            mqtt_client.publish(robot_label=robot['label'].robot_label, topic=msg.topic, payload=msg.payload)
            time.sleep(2)

            while helper.last_complete_command_label != last_command_label:
                time.sleep(1)

    for robot in robots:
        # robot HOME_SPYDER_MOVE_SCAN
        while robot['label'].state != "LOCATION_UNKNOWN":
            time.sleep(1)

        print(f"robot {robot['label'].robot_label} state is LOCATION_UNKNOWN, ready to HOME_SPYDER_MOVE_SCAN!")

        msg = build_spyder_home_command_set(robot_label=robot['label'].robot_label,
                                            command_type="HOME_SPYDER_MOVE_SCAN", distance_to_dm_codes=342,
                                            origin_offset=0)
        last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        mqtt_client.publish(robot_label=robot['label'].robot_label, topic=msg.topic, payload=msg.payload)

        while helper.last_complete_command_label != last_command_label:
            time.sleep(1)

        # robot HOME_SET_ORIGIN
        while robot['label'].state != "LOCATION_UNKNOWN":
            time.sleep(1)

        print(f"robot {robot['label'].robot_label} state is LOCATION_UNKNOWN, ready to HOME_SET_ORIGIN!")

        msg = build_spyder_home_command_set(robot_label=robot['label'].robot_label, command_type="HOME_SET_ORIGIN",
                                            distance_to_dm_codes=0, origin_offset=0)
        last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        mqtt_client.publish(robot_label=robot['label'].robot_label, topic=msg.topic, payload=msg.payload)

        while helper.last_complete_command_label != last_command_label:
            time.sleep(1)

        # robot HOME_HANDLER
        while robot['label'].state != "LOCATION_KNOWN":
            time.sleep(1)

        print(f"robot {robot['label'].robot_label} state is LOCATION_KNOWN, ready to HOME_HANDLER!")

        msg = build_spyder_home_command_set(robot_label=robot['label'].robot_label, command_type="HOME_HANDLER",
                                            distance_to_dm_codes=0, origin_offset=0)
        last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        mqtt_client.publish(robot_label=robot['label'].robot_label, topic=msg.topic, payload=msg.payload)

        while helper.last_complete_command_label != last_command_label:
            time.sleep(1)


if __name__ == "__main__":
    main()
