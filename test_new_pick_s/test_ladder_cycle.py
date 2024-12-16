from mqtt_service import *
from robot import *
from helper import *
import time


def main(args):
    print(args)

    ladder = Ladder(args.ladder)
    helper = Helper(robot_list=[ladder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(
        host=args.server_ip,
        port=args.server_port,
        username=args.username,
        password=args.password,
    )
    mqtt_client.add_robot(ladder.robot_label)

    FULL_VEL = 100
    FULL_ACC = 100

    try:
        for idx, l in enumerate(HZ_C002_BAY):
            forward_time = backward_time = 0
            print(
                f"testing BAY 0 to BAY {idx + 1}, start pos = {FIRST_BAY}, end pos = {l}, test cycle = {args.cycle_count}"
            )
            for i in range(args.cycle_count):
                print(f"Iteration {i+1}")
                ladder.state_update_flag = False
                while not ladder.state_update_flag:
                    time.sleep(0.2)

                init_pos = ladder.position
                test_case = [[l, FULL_VEL, FULL_ACC]]

                msg = build_ladder_move_command_set(
                    ladder.robot_label, init_pos, test_case
                )

                last_command_label = msg.payload["robotCommands"][-1][
                    "robotCommandLabel"
                ]

                start = time.time()

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload
                )

                while helper.last_complete_command_label != last_command_label:
                    time.sleep(0.002)

                end = time.time()
                forward_time += end - start

                ladder.state_update_flag = False
                while not ladder.state_update_flag:
                    time.sleep(0.2)

                init_pos = ladder.position
                test_case = [[FIRST_BAY, FULL_VEL, FULL_ACC]]

                msg = build_ladder_move_command_set(
                    ladder.robot_label, init_pos, test_case
                )

                last_command_label = msg.payload["robotCommands"][-1][
                    "robotCommandLabel"
                ]

                start = time.time()

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload
                )

                while helper.last_complete_command_label != last_command_label:
                    time.sleep(0.002)

                end = time.time()
                backward_time += end - start

            print(
                f"forward time avg = {forward_time / args.cycle_count}, backward time avg = {backward_time / args.cycle_count}"
            )
    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
