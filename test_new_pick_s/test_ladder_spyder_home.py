import time
from enum import Enum

from helper import *

# 机器人对原点参数
SPYDER_CODE_HEIGHT = 1055  # mm
LADDER_CODE_DISTANCE = 500  # mm


# Ladder & Spyder对原点流程相关控制状态枚举
class STATE(Enum):
    # 初始状态，对Ladder & Spyder发送INIT指令
    START = 0
    # 持续发送Spyder HOME_SPYDER_MOVE_SCAN指令，移动到distanceToDmCodes高度
    SPYDER_MOVE_SEEKING_CODE = 1
    # Ladder左右移动找码，对Spyder发送HOME_SPYDER_SCAN指令，对Ladder发送HOME_LADDER_MOVE指令，移动范围distanceBetweenDmCodes
    LADDER_MOVE_SEEKING_CODE = 3
    # 对Ladder发送HOME_LADDER_STOP指令
    LADDER_MOVE_SEEKING_CODE_DONE_STOPPING = 4
    # 对Ladder & Spyder发送HOME_SET_ORIGIN指令，设置originOffset（x/z）坐标
    SETTING_X_AND_Z_POS = 10
    # 对Spyder发送HOME_HANDLE指令，进行拉还箱机构对原点
    SPYDER_HOME_HANDLE = 11
    # 完成
    FINISHED = 20
    # 失败
    FAILED = 30
    # 报错
    ERROR = 40


def main(args):
    print(args)

    ladder = Ladder(args.ladder)
    spyder = Spyder(args.spyder)
    helper = Helper(robot_list=[ladder, spyder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(spyder.robot_label)
    mqtt_client.add_robot(ladder.robot_label)

    try:
        home_state = STATE.START

        while True:
            print(home_state)

            if home_state == STATE.START:
                # wait robot to online
                while spyder.state != "UNKNOWN" or ladder.state != "UNKNOWN":
                    time.sleep(1)

                # send INIT
                msg = build_robot_command_set(spyder.robot_label, "INIT")

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                msg = build_robot_command_set(ladder.robot_label, "INIT")

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

                # INIT complete
                while spyder.state != "LOCATION_UNKNOWN" or ladder.state != "LOCATION_UNKNOWN":
                    time.sleep(1)

                home_state = STATE.SPYDER_MOVE_SEEKING_CODE

            elif home_state == STATE.SPYDER_MOVE_SEEKING_CODE:
                msg = build_spyder_home_command_set(
                    spyder.robot_label, command_type="HOME_SPYDER_MOVE_SCAN", distance_to_dm_codes=SPYDER_CODE_HEIGHT)

                last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                while helper.complete_command[spyder.robot_label] != last_command_label:
                    time.sleep(0.01)

                time.sleep(2)  # ensure to get the latest scan_state of spyder

                if spyder.is_dm_code():
                    home_state = STATE.SETTING_X_AND_Z_POS
                else:
                    home_state = STATE.LADDER_MOVE_SEEKING_CODE

            elif home_state == STATE.LADDER_MOVE_SEEKING_CODE:
                msg = build_spyder_home_command_set(
                    spyder.robot_label, command_type="HOME_SPYDER_SCAN")

                command_spyder = msg.payload["robotCommands"][-1]["robotCommandLabel"]

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                msg = build_ladder_home_command_set(
                    ladder.robot_label, command_type="HOME_LADDER_MOVE", distance_between_dm_codes=LADDER_CODE_DISTANCE)

                command_ladder = msg.payload["robotCommands"][-1]["robotCommandLabel"]

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

                # if any of the robot completes, we can move forward
                while (
                        helper.complete_command[ladder.robot_label] != command_ladder
                        and
                        helper.complete_command[spyder.robot_label] != command_spyder
                ):
                    time.sleep(0.01)

                home_state = STATE.LADDER_MOVE_SEEKING_CODE_DONE_STOPPING

            elif home_state == STATE.LADDER_MOVE_SEEKING_CODE_DONE_STOPPING:
                msg = build_ladder_home_command_set(
                    ladder.robot_label, command_type="HOME_LADDER_STOP")

                last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

                mqtt_client.publish(
                    robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

                while helper.complete_command[ladder.robot_label] != last_command_label:
                    time.sleep(0.01)

                time.sleep(2)  # ensure to get the latest scan_state of spyder

                if spyder.is_dm_code():
                    home_state = STATE.SETTING_X_AND_Z_POS
                else:
                    home_state = STATE.FAILED

            elif home_state == STATE.SETTING_X_AND_Z_POS:
                scan_data, offset_x, offset_z = spyder.scan_data, spyder.scan_x, spyder.scan_z
                if len(scan_data) == 16 and scan_data.isdigit():
                    coord_x = int(scan_data[:6]) + offset_x
                    coord_z = int(scan_data[6:11]) + offset_z
                    print(scan_data, offset_x, offset_z, coord_x, coord_z)

                    msg = build_spyder_home_command_set(
                        spyder.robot_label, command_type="HOME_SET_ORIGIN", origin_offset=coord_z)

                    mqtt_client.publish(
                        robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                    msg = build_ladder_home_command_set(
                        ladder.robot_label, command_type="HOME_SET_ORIGIN", origin_offset=coord_x)

                    mqtt_client.publish(
                        robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

                    while spyder.state != "LOCATION_KNOWN" or ladder.state != "IDLE":
                        time.sleep(1)

                    home_state = STATE.SPYDER_HOME_HANDLE
                else:
                    home_state = STATE.FAILED

            elif home_state == STATE.SPYDER_HOME_HANDLE:
                msg = build_spyder_home_command_set(
                    spyder.robot_label, command_type="HOME_HANDLER")

                mqtt_client.publish(
                    robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

                while spyder.state != "IDLE":
                    time.sleep(1)

                home_state = STATE.FINISHED

            elif home_state == STATE.FAILED:
                print("=" * 20 + "FAILED" + "=" * 20)
                break

            elif home_state == STATE.FINISHED:
                print("=" * 20 + "COMPLETE" + "=" * 20)
                break

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
