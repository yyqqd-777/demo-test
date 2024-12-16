from mqtt_service import *
from robot import *
from helper import *
import time
import paramiko


def main(args):
    print(args)

    spyder = Spyder(args.spyder)
    helper = Helper(robot_list=[spyder])
    mqtt_client = MQTTClient(callback=helper.mqtt_receive_callback)
    mqtt_client.start(host=args.server_ip, port=args.server_port,
                      username=args.username, password=args.password)
    mqtt_client.add_robot(spyder.robot_label)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("192.168.10.100", 22, username="orangepi", password="orangepi")

    # 机器人移动
    # 508mm per row,
    row_height = 508
    offset = -27
    diff = 10

    INIT_POS = 5 * row_height + offset  # 初始位置
    FULL_VEL = 1000
    FULL_ACC = 500
    TEST_VEL = 200

    try:
        cnt = 0
        while True:
            cnt += 1
            print("=" * 20 + f"test {cnt}" + "=" * 20)
            msg = build_spyder_move_command_set(
                spyder.robot_label, INIT_POS + diff, [[INIT_POS - diff, FULL_VEL, FULL_ACC]])

            mqtt_client.publish(
                robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

            last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

            while helper.last_complete_command_label != last_command_label:
                time.sleep(0.2)

            # load
            # ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
            #     f"cd /home/orangepi/project/240509-saibo && python3 saibo_action.py -a right_load"
            # )
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
                f"cd /home/orangepi/project/spyder_pull_box && python3 spyder_right_load.py 1346679"
            )
            exit_status = ssh_stdout.channel.recv_exit_status()  # Blocking call
            if exit_status:
                print("Error", exit_status)

            msg = build_spyder_move_command_set(
                spyder.robot_label, INIT_POS - diff, [[INIT_POS + diff, FULL_VEL, FULL_ACC]])

            mqtt_client.publish(
                robot_label=spyder.robot_label, topic=msg.topic, payload=msg.payload)

            last_command_label = msg.payload["robotCommands"][-1]["robotCommandLabel"]

            while helper.last_complete_command_label != last_command_label:
                time.sleep(0.2)

            # unload
            # ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
            #     f"cd /home/orangepi/project/240509-saibo && python3 saibo_action.py -a right_unload"
            # )
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
                f"cd /home/orangepi/project/spyder_pull_box && python3 spyder_right_unload.py 1346679"
            )
            exit_status = ssh_stdout.channel.recv_exit_status()  # Blocking call
            if exit_status:
                print("Error", exit_status)

    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    main(parse_args())
