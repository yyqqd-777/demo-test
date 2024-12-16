from mqtt_service import *
from robot import *
from helper import *
import time


def ladder_move(ladder, test_case, mqtt_client, helper):
    # 机器人初始化
    while ladder.state != "IDLE":
        print(ladder.state)
        time.sleep(1)

    init_pos = ladder.position

    msg = build_ladder_move_command_set(
        ladder.robot_label, init_pos, test_case)

    mqtt_client.publish(robot_label=ladder.robot_label,
                        topic=msg.topic, payload=msg.payload)

    last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

    while helper.last_complete_command_label != last_command_label:
        time.sleep(1)


def main(args):
    print(args)

    ladder = Ladder(args.ladder)
    helper = Helper(robot_list=[ladder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(ladder.robot_label)

    # 机器人移动
    FULL_VEL = 1500
    FULL_ACC = 4500

    test_case_1 = [
        [7500, FULL_VEL, FULL_ACC],
    ]
    test_case_2 = [
        [0, FULL_VEL, FULL_ACC],
    ]

    try:
        for i in range(3):
            ladder_move(ladder, test_case_1, mqtt_client, helper)

            ladder_move(ladder, test_case_2, mqtt_client, helper)
            print(f'iteration {i + 1} done')

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
