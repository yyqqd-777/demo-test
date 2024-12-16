import time

from helper import *


def main(args):
    print(args)

    spyder = Spyder(args.spyder)
    helper = Helper(robot_list=[spyder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(
        host=args.server_ip,
        port=args.server_port,
        username=args.username,
        password=args.password,
    )
    mqtt_client.add_robot(spyder.robot_label)

    box_space = 60
    box_length = 600
    load_depth_f = 705
    unload_depth_f = 740
    load_depth_b = 755
    unload_depth_b = 790

    test_cases = [

        [True, True, load_depth_f + box_length + box_space],
        [False, True, unload_depth_f],
        [True, True, load_depth_f],
        [False, True, unload_depth_f + box_length + box_space],

        [True, False, load_depth_b + box_length + box_space],
        [False, False, unload_depth_b],
        [True, False, load_depth_b],
        [False, False, unload_depth_b + box_length + box_space],
    ]

    try:
        for i in range(args.cycle_count):
            print(f"Iteration {i+1}")
            for load, forward, distance in test_cases:
                while not spyder.state_update_flag:
                    time.sleep(0.05)

                init_pos = spyder.position

                msg = build_spyder_action_command_set(
                    spyder.robot_label, init_pos, load, forward, distance
                )

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
                )

                last_command_label = msg.payload["robotCommands"][-1][
                    "robotCommandLabel"
                ]

                while helper.last_complete_command_label != last_command_label:
                    time.sleep(1)

                spyder.state_update_flag = False

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
