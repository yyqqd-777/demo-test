import itertools
import threading
import time

from helper import *

global FUXK_RUNNING
MAIN_LOG = True
ENABLE_LHD = True

FULL_VEL_L = 1500
FULL_VEL_S = 1000
FULL_ACC = 500

CHARGER = Node(101655, 102539, ori=180)


def load_ant_1_path() -> list[Node]:
    return [
        Node(103354, 102539),
        Node(103354, 110520),
        Node(103354, 102539, ori=90),
        CHARGER,
    ]


def load_ant_2_path() -> list[Node]:
    return [
        Node(106783, 102539, ori=180),
        Node(106783, 103539),
        Node(111891, 103539),
        Node(111891, 135648),
        Node(111052, 135648),
        Node(111052, 103539),
        Node(106783, 103539),
        Node(106783, 102539),
        CHARGER,
    ]


def load_ant_3_path() -> list[Node]:
    return [
        Node(106783, 102539, ori=180),
        CHARGER,
    ]


def load_ant_4_path() -> list[Node]:
    return [
        Node(103354, 102539),
        Node(103354, 104362),
        Node(104204, 104362),
        Node(104208, 102539),
    ]


def load_ant_5_path() -> list[Node]:
    return [
        Node(103354, 105500),
        Node(103354, 113924),
        Node(102515, 113924),
        Node(102515, 105500),
    ]


def load_ant_6_path() -> list[Node]:
    return [
        Node(107622, 105185),
        Node(107622, 104362, ori=90),
    ]


def load_ant_simpl_path() -> list[Node]:
    return [
        Node(107455, 103737),
        Node(107455, 105563),
        Node(110783, 105563),
        Node(110783, 103737),
    ]


def load_shelf_1_path() -> list[tuple[Cell, bool, bool, int]]:
    # BAY 1 TO BAY 2, WITH LHD
    C1 = Cell(605, -508)
    C2 = Cell(3120, 1016)
    return [
        # cell, load, forward, distance
        (C1, True, False, 804),
        (C2, False, False, 844),
        (C2, True, False, 804),
        (C1, False, False, 844),
    ]


def load_shelf_2_path() -> list[tuple[Cell, bool, bool, int]]:
    # BAY 4 TO BAY 5, WITH LHD
    C1 = Cell(8150, -1016)
    C2 = Cell(10665, -508)
    return [
        # cell, load, forward, distance
        (C1, True, False, 804),
        (C2, False, False, 844),
        (C2, True, False, 804),
        (C1, False, False, 844),
    ]


def load_shelf_hz_path() -> list[tuple[Cell, bool, bool, int]]:
    C1 = Cell(0, 455)
    C2 = Cell(4920, 455 + 400 + 350 + 400)
    C3 = Cell(500, 455 + 400)
    return [
        # cell, load, forward, distance
        (C1, True, True, 680),
        (C2, False, True, 740),
        (C2, True, True, 680),
        (C3, False, True, 740 + 20 + 600),
        (C3, True, True, 680 + 20 + 600),
        (C1, False, True, 740),
    ]


def ladder_spyder_task(ladder: Ladder, spyder: Spyder, path: list[tuple[Cell, bool, bool, int]], mqtt_client: MQTTClient, helper: Helper):
    if not path:
        return

    cnt = itertools.count(start=1, step=1)

    global FUXK_RUNNING
    while FUXK_RUNNING:
        helper.log_info("=" * 20 + f"test {next(cnt)}" + "=" * 20)

        for cell, load, forward, distance in path:
            # before next step, wait for robot state update
            ladder.state_update_flag = False
            spyder.state_update_flag = False
            while not ladder.state_update_flag or not spyder.state_update_flag:
                time.sleep(0.05)

            # generate the init_cell
            init_cell = Cell(ladder.position, spyder.position)
            target_x = cell.x
            target_z = cell.get_load_pos() if load else cell.get_unload_pos()

            helper.log_info(f"process move init_cell = {init_cell}, "
                            f"target_x = {target_x}, "
                            f"target_z = {target_z}...")

            # SPYDER MOVE START
            if abs(init_cell.z - target_z) > 5:
                msg = build_spyder_move_command_set(
                    spyder.robot_label,
                    init_cell.z,
                    [[target_z, FULL_VEL_S, FULL_ACC]],
                    spyder.load_sensor_front,
                    spyder.load_sensor_rear
                )

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                command_spyder = msg.payload["robotCommands"][-1]["robotCommandLabel"]
            else:
                command_spyder = None

            # LADDER MOVE START
            if abs(init_cell.x - target_x) > 5:
                msg = build_ladder_move_command_set(
                    ladder.robot_label, init_cell.x, [[target_x, FULL_VEL_L, FULL_ACC]])

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

                command_ladder = msg.payload["robotCommands"][-1]["robotCommandLabel"]
            else:
                command_ladder = None

            while (
                    (command_spyder and helper.complete_command[spyder.robot_label] != command_spyder)
                    or
                    (command_ladder and helper.complete_command[ladder.robot_label] != command_ladder)
            ):
                time.sleep(0.05)

            if ENABLE_LHD:
                spyder.state_update_flag = False
                while not spyder.state_update_flag:
                    time.sleep(0.05)

                init_pos = spyder.position

                helper.log_info(f"process load = {load}, "
                                f"forward = {forward}, "
                                f"distance = {distance}...")

                # SPYDER LOAD/UNLOAD START
                msg = build_spyder_action_command_set(
                    spyder.robot_label, init_pos, load, forward, distance)

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                command_spyder = msg.payload["robotCommands"][-1]["robotCommandLabel"]

                while helper.complete_command[spyder.robot_label] != command_spyder:
                    time.sleep(0.05)


def ant_move_task(ant: Ant, path: list[Node], mqtt_client: MQTTClient, helper):
    if not path:
        return

    global FUXK_RUNNING
    while FUXK_RUNNING:
        # get the latest ant state
        ant.state_update_flag = False
        while not ant.state_update_flag:
            time.sleep(0.1)

        # generate the init_node
        init_node = Node(ant.position_x, ant.position_y,
                         ant.orientation / 100, ant.height)

        full_path = find_full_path([init_node] + path)

        msg = build_ant_action_command_set(
            ant.robot_label, init_node.get_state(), full_path)

        command_ant = msg.payload["robotCommands"][-1]["robotCommandLabel"]

        mqtt_client.publish(
            robot_label=ant.robot_label, topic=msg.topic, payload=msg.payload)

        while helper.complete_command[ant.robot_label] != command_ant:
            time.sleep(0.05)


def main(args):
    print(args)

    ant_task = [
        # ("A100", load_ant_1_path),
        # ("A100", load_ant_2_path),
        # ("A100", load_ant_3_path),
        # ("A100", load_ant_4_path),
        # ("A100", load_ant_4_path),
        # ("A102", load_ant_5_path),
        # ("SplPWal-A101", load_ant_simpl_path),
        # ("A131", load_ant_6_path)
    ]

    shelf_task = [
        ("L102", "S302", load_shelf_hz_path)
    ]

    robot_list: list[Robot] = []
    work: list[tuple] = []

    for ant_label, ant_path_func in ant_task:
        ant = Ant(ant_label)
        robot_list.append(ant)
        work.append((ant, ant_path_func()))

    for ladder, spyder, shelf_path_func in shelf_task:
        spyder = Spyder(spyder)
        ladder = Ladder(ladder)
        robot_list.append(spyder)
        robot_list.append(ladder)
        work.append((ladder, spyder, shelf_path_func()))

    helper = Helper(robot_list=robot_list, log_flag=MAIN_LOG)
    helper.log_info(args)

    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)

    for robot in robot_list:
        mqtt_client.add_robot(robot.robot_label)

    try:
        # wait for robot online and report their states
        while any([robot.state_update_flag is False for robot in robot_list]):
            time.sleep(0.1)

        for robot in robot_list:
            if type(robot) is Ant:
                # init ANT
                while robot.state == "UNKNOWN":
                    msg = build_robot_command_set(robot.robot_label, "INIT")

                    mqtt_client.publish(
                        robot_label=robot.robot_label, topic=msg.topic, payload=msg.payload)

                    time.sleep(2)

        # check robot init state
        while any([robot.state != "IDLE" for robot in robot_list]):
            time.sleep(1)

        thread_list = []

        # TASK START
        global FUXK_RUNNING
        FUXK_RUNNING = True
        for w in work:
            if w and type(w[0]) is Ant:
                ant, path = w
                ant_thread = threading.Thread(
                    target=ant_move_task, args=(ant, path, mqtt_client, helper), daemon=True)
                thread_list.append(ant_thread)
                ant_thread.start()
            else:
                ladder, spyder, path = w
                ladder_spyder_thread = threading.Thread(
                    target=ladder_spyder_task, args=(ladder, spyder, path, mqtt_client, helper), daemon=True)
                thread_list.append(ladder_spyder_thread)
                ladder_spyder_thread.start()

        input("press any key to stop...")
        FUXK_RUNNING = False

        while any(thread.is_alive() for thread in thread_list):
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    mqtt_client.stop()
    print("fuxking done")


if __name__ == "__main__":
    main(parse_args())
