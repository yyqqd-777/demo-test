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

    # 参考面均是蜘蛛拖箱面
    # 下极限位偏差
    l0_offset = 90

    # 相机中心点偏差(手工测量)
    camera_offset = 152
    # 横梁高度(根据项目)
    beam_height = 60

    # 各层高度
    l1_height = 540
    l2_height = 525
    l3_height = 525

    try:
        # 机器人初始化
        while spyder.state != "UNKNOWN":
            time.sleep(0.5)

        msg = build_robot_command_set(spyder.robot_label, "INIT")

        mqtt_client.publish(
            robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
        )
        command_result = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        while helper.complete_command[spyder.robot_label] != command_result:
            time.sleep(0.05)

        while spyder.state != "LOCATION_UNKNOWN":
            time.sleep(0.5)

        msg = build_spyder_home_command_set(
            spyder.robot_label,
            command_type="HOME_SPYDER_MOVE_SCAN",
            distance_to_dm_codes=int(l0_offset + l1_height + l2_height +
                                     l3_height + (camera_offset - beam_height/2)),
        )

        mqtt_client.publish(
            robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

        command_result = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        while helper.complete_command[spyder.robot_label] != command_result:
            time.sleep(0.05)

        while spyder.state != "LOCATION_UNKNOWN":
            time.sleep(0.5)

        msg = build_home_command_set_simple(
            spyder.robot_label, command_type="HOME_SET_ORIGIN", origin_offset=l1_height + l2_height + l3_height
        )

        mqtt_client.publish(
            robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
        )

        command_result = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        while helper.complete_command[spyder.robot_label] != command_result:
            time.sleep(0.05)

        while spyder.state != "LOCATION_KNOWN":
            time.sleep(0.5)

        msg = build_home_command_set_simple(
            spyder.robot_label, command_type="HOME_HANDLER")

        mqtt_client.publish(
            robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload
        )
        command_result = msg.payload["robotCommands"][-1]["robotCommandLabel"]
        while helper.complete_command[spyder.robot_label] != command_result:
            time.sleep(0.05)

        while spyder.state != "IDLE":
            time.sleep(0.5)

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
