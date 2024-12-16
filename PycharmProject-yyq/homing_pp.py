import canopen
import time
import struct
import logging


# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化CAN总线
network = canopen.Network()
network.connect(channel='COM7', bustype='slcan', bitrate=1000000)

# 加载电机EDS文件
motor1 = canopen.RemoteNode(1, 'flowservo_20240131.eds')
motor2 = canopen.RemoteNode(2, 'flowservo_20240131.eds')
network.add_node(motor1)
network.add_node(motor2)


def setup_motor(motor):
    try:
        # 进入预操作模式
        motor.nmt.state = 'PRE-OPERATIONAL'
        logging.info(f"Motor {motor.id} set to PRE-OPERATIONAL mode.")

        # 设置PP模式
        motor.sdo.download(0x6060, 0x00, struct.pack('b', 1))
        logging.info(f"Motor {motor.id} set to PP mode.")

        # 启动电机
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x06))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x07))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x0F))
        logging.info(f"Motor {motor.id} started in PP mode.")

    except Exception as e:
        logging.error(f"Error setting up motor {motor.id}: {e}")


def move_to_position(motor,position):
    try:
        motor.sdo.download(0x607A, 0x00, struct.pack('i', position))
        motor.sdo.download(0x6081, 0x00, struct.pack('i', 273000))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x3F))  # 启动移动
        logging.info(f"Motor {motor.id} moving to position")

        while True:
            statusword = struct.unpack('H', motor.sdo.upload(0x6041, 0x00))[0]
            if statusword & 0x400:  # 检查是否到达目标位置
                logging.info(f"Motor {motor.id} reached position .")
                break
            time.sleep(0.1)

    except Exception as e:
        logging.error(f"Error moving motor {motor.id} to position : {e}")


def main():
    # 设置电机1和电机2
    setup_motor(motor1)
    setup_motor(motor2)

    positions1 = [2730, 0]
    positions2 = [-2730, 0]
    try:
        while True:
            for position in positions1:
                move_to_position(motor1, position)
                logging.info(f"Motor {motor1.id} moved ")
                # move_to_position(motor2, position)
                time.sleep(1)
            for position in positions2:
                move_to_position(motor2, position)
                logging.info(f"Motor {motor2.id} moved ")
                # move_to_position(motor2, position)
                time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Interrupted by user. Disconnecting...")
    finally:
        # 断开连接
        network.disconnect()
        logging.info("Network disconnected.")


if __name__ == "__main__":
    main()
