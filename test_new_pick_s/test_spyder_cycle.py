from mqtt_service import *
from robot import *
from helper import *
import time


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

    FULL_VEL = 1000
    FULL_ACC = 500

    offset = -27
    try:
        for idx, l in enumerate(HZ_C002_LEVEL):
            up_time = down_time = 0
            print(
                f"testing PD to LEVEL {idx + 1}, down level = {HZ_PD_LEVEL}, up level = {l}, test cycle = {args.cycle_count}"
            )

            for i in range(args.cycle_count):
                print(f"Iteration {i+1}")
                spyder.state_update_flag = False
                while not spyder.state_update_flag:
                    time.sleep(0.2)

                init_pos = spyder.position
                test_case = [[l + offset, FULL_VEL, FULL_ACC]]

                msg = build_spyder_move_command_set(
                    spyder.robot_label, init_pos, test_case
                )

                last_command_label = msg.payload["robotCommands"][-1][
                    "robotCommandLabel"
                ]

                start = time.time()

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
                )

                while helper.last_complete_command_label != last_command_label:
                    time.sleep(0.002)

                end = time.time()
                up_time += end - start

                spyder.state_update_flag = False
                while not spyder.state_update_flag:
                    time.sleep(0.2)

                init_pos = spyder.position
                test_case = [[HZ_PD_LEVEL + offset, FULL_VEL, FULL_ACC]]

                msg = build_spyder_move_command_set(
                    spyder.robot_label, init_pos, test_case
                )

                last_command_label = msg.payload["robotCommands"][-1][
                    "robotCommandLabel"
                ]

                start = time.time()

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
                )

                while helper.last_complete_command_label != last_command_label:
                    time.sleep(0.002)

                end = time.time()
                down_time += end - start

            print(
                f"up time avg = {up_time / args.cycle_count}, down time avg = {down_time / args.cycle_count}"
            )
    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
