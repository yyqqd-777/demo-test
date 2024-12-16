import time

from helper import *

FULL_VEL = 1000
FULL_ACC = 500


def main(args):
    print(args)

    spyder = Spyder(args.spyder)
    helper = Helper(robot_list=[spyder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(spyder.robot_label)

    # 508mm per row,
    row_height = 508
    offset = -27
    diff = 10
    test_case = [
        [245, FULL_VEL, FULL_ACC],
        # [3658 + offset, FULL_VEL, FULL_ACC],
    ]

    try:
        while spyder.state != "IDLE":
            time.sleep(0.2)

        init_pos = spyder.position

        msg = build_spyder_move_command_set(
            spyder.robot_label,
            init_pos,
            test_case,
            spyder.load_sensor_front,
            spyder.load_sensor_rear
        )

        mqtt_client.publish(
            robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

        last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

        while helper.last_complete_command_label != last_command_label:
            time.sleep(1)

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
