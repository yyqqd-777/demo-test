from mqtt_service import *
from robot import *
from helper import *
import time


def main(args):
    print(args)

    ladder = Ladder(args.ladder)
    helper = Helper(robot_list=[ladder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(ladder.robot_label)

    try:
        # 机器人初始化
        while ladder.state != "UNKNOWN":
            time.sleep(1)

        msg = build_robot_command_set(ladder.robot_label, "INIT")

        mqtt_client.publish(
            robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

        while ladder.state != "LOCATION_UNKNOWN":
            time.sleep(1)

        msg = build_ladder_home_command_set(
            ladder.robot_label, command_type="HOME_SET_ORIGIN", originOffset=0)

        mqtt_client.publish(
            robot_label=ladder.robot_label, topic=msg.topic, payload=msg.payload)

        while ladder.state != "IDLE":
            time.sleep(1)

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
