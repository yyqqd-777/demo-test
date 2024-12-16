from mqtt_service import *
from robot import *
from helper import *
import time


def main(args):
    print(args)

    robot = Robot("General", args.general)
    helper = Helper(robot_list=[robot])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(robot.robot_label)

    try:
        while not robot.state_update_flag:
            time.sleep(1)

        msg = build_robot_command_set(robot.robot_label, "RESET")

        mqtt_client.publish(robot_label=robot.robot_label,
                            topic=msg.topic, payload=msg.payload)
    except KeyboardInterrupt:
        pass

    mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
