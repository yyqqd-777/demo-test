import time

from mqtt_service import *
from robot import *
from helper import *


"""Spider loading/unloading box depth instructions

    Front loading box depth: 705mm, double depth: 1365mm
    Front unloading box depth: 740mm, double depth: 1400mm
    Back loading box depth: 755mm, double depth: 1415mm
    Back unloading box depth: 790mm, double depth: 1450mm
"""

loading_depth = {
    "front_loading": 705,
    "front_unloading": 740,
    "back_loading": 755,
    "back_unloading": 790,
    "front_double_loading": 1365,
    "front_double_unloading": 1400,
    "back_double_loading": 1415,
    "back_double_unloading": 1450
}

with open('test_spyder2_1.json', 'r') as file:
    data = json.load(file)

mqtt_dict = {
    "server_ip": data['server_ip'],
    "server_port": data['server_port'],
    "username": data['username'],
    "password": data['password']
}

robot_dict = {
    "robot_vel": data['robot_vel'],
    "robot_acc": data['robot_acc']
}

spyder_path_list = data['spyder_path']

spyder_list = []
for i in data["spyder"][0]:
    spyder_list.append(i)

robots = []
for robot in spyder_list:
    robots.append(
        {
            'label': Spyder(robot),
            'shelf_height_1': data['spyder'][0][robot]['shelf_height_1'],
            'shelf_height_2': data['spyder'][0][robot]['shelf_height_2']
        }
    )


def main():
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

    # 机器人开始循环运行
    for _ in range(1):
        for robot in robots:
            for i in spyder_path_list:
                while robot['label'].state != "IDLE":
                    time.sleep(1)

                if i['action'] == 'MOVE':
                    msg = build_spyder_move_command_set(
                        robot_label=robot['label'].robot_label,
                        init_pos=robot['label'].position,
                        command_param=[[robot[i['position']]+i['offset'], robot_dict['robot_vel'], robot_dict['robot_acc']]],
                        load_sensor_front=i['load_sensor_front'],
                        load_sensor_rear=i['load_sensor_rear'],
                    )
                elif i['action'] == 'LOAD':
                    msg = build_spyder_action_command_set(
                        robot_label=robot['label'].robot_label,
                        init_pos=robot['label'].position,
                        load=i['load'],
                        forward=i['forward'],
                        distance=loading_depth[i['distance']]
                    )
                else:
                    raise ValueError(f"unknown command type {i['action']}")

                helper.last_complete_command_label = "UNKNOWN"
                last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]
                mqtt_client.publish(robot_label=robot['label'].robot_label, topic=msg.topic, payload=msg.payload)
                while helper.last_complete_command_label != last_command_label:
                    time.sleep(1)
        print(_ + 1)
    mqtt_client.stop()


if __name__ == "__main__":
    main()


# {"action": "MOVE", "position": "shelf_height_1", "offset": -5, "load_sensor_front": false, "load_sensor_rear": false},
# {"action": "LOAD", "load": true, "forward": false, "distance": "back_loading"},
# {"action": "MOVE", "position": "shelf_height_2", "offset": 5, "load_sensor_front": true, "load_sensor_rear": true},
# {"action": "LOAD", "load": false, "forward": false, "distance": "back_unloading"},
# {"action": "MOVE", "position": "shelf_height_2", "offset": -5, "load_sensor_front": false, "load_sensor_rear": false},
# {"action": "LOAD", "load": true, "forward": false, "distance": "back_loading"},
# {"action": "MOVE", "position": "shelf_height_1", "offset": 5, "load_sensor_front": true, "load_sensor_rear": true},
# {"action": "LOAD", "load": false, "forward": true, "distance": "back_unloading"}

# "spyder_path": [
#         {"action": "MOVE", "position": "shelf_height_1", "offset": -5, "load_sensor_front": false, "load_sensor_rear": false},
#         {"action": "LOAD", "load": true, "forward": false, "distance": "back_loading"},
#         {"action": "MOVE", "position": "shelf_height_2", "offset": 5, "load_sensor_front": true, "load_sensor_rear": true},
#         {"action": "LOAD", "load": false, "forward": false, "distance": "back_unloading"},
#         {"action": "MOVE", "position": "shelf_height_2", "offset": -5, "load_sensor_front": false, "load_sensor_rear": false},
#         {"action": "LOAD", "load": true, "forward": false, "distance": "back_loading"},
#         {"action": "MOVE", "position": "shelf_height_1", "offset": 5, "load_sensor_front": true, "load_sensor_rear": true},
#         {"action": "LOAD", "load": false, "forward": false, "distance": "back_unloading"}
#     ]