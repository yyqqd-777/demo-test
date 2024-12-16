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

        # 设置Homing模式
        motor.sdo.download(0x6060, 0x00, struct.pack('b', 6))
        logging.info(f"Motor {motor.id} set to Homing mode.")

        # 配置Homing方法和参数
        motor.sdo.download(0x6098, 0x00, struct.pack('b', 35))
        # motor.sdo.download(0x6099, 0x01, struct.pack('I', 1000))
        # motor.sdo.download(0x6099, 0x02, struct.pack('I', 500))
        # motor.sdo.download(0x6083, 0x00, struct.pack('I', 500))
        logging.info(f"Motor {motor.id} Homing parameters set.")

        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x06))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x07))
        # motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x0F))

        # 启动Homing操作
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x1F))
        logging.info(f"Motor {motor.id} started Homing operation.")

        # 等待Homing完成
        while True:
            homing_status_bytes = motor.sdo.upload(0x6041, 0x00)
            homing_status = struct.unpack('H', homing_status_bytes)[0]
            if homing_status & 0x1000:
                logging.info(f"Motor {motor.id} Homing completed.")
                break
            time.sleep(0.1)


        # 设置PP模式
        motor.sdo.download(0x6060, 0x00, struct.pack('b', 1))
        logging.info(f"Motor {motor.id} set to PP mode.")
        # motor.sdo.download(0x607A, 0x00, struct.pack('H', 0x27))
        # motor.sdo.download(0x6081, 0x00, struct.pack('H', 0x27))
        # 启动电机
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x06))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x07))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x0F))
        logging.info(f"Motor {motor.id} started in PP mode.")

    except Exception as e:
        logging.error(f"Error setting up motor {motor.id}: {e}")


def move_to_position(motor, position, velocity):
    try:
        motor.sdo.download(0x607A, 0x00, struct.pack('i', position))
        motor.sdo.download(0x6081, 0x00, struct.pack('i', velocity))
        motor.sdo.download(0x6040, 0x00, struct.pack('H', 0x3F))  # 启动移动
        logging.info(f"Motor {motor.id} moving to position {position}.")

        # 等待移动完成
        while True:
            position_reached_bytes = motor.sdo.upload(0x6041, 0x00)
            position_reached = struct.unpack('H', position_reached_bytes)[0]
            if position_reached & 0x1000:
                logging.info(f"Motor {motor.id} reached position {position}.")
                break
            time.sleep(0.5)

    except Exception as e:
        logging.error(f"Error moving motor {motor.id} to position {position}: {e}")


def main():
    # 设置电机1和电机2
    setup_motor(motor1)
    setup_motor(motor2)

    velocity = 275000  # 速度设定

    positions1 = [270000, ]  # 定义两个位置
    positions2 = [-25000, 0]
    try:
        while True:
            for position in positions1:
                move_to_position(motor1, position, velocity)
                time.sleep(1)
            for position in positions2:
                move_to_position(motor2, position, velocity)
                time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Interrupted by user. Disconnecting...")
    finally:
        # 断开连接
        network.disconnect()
        logging.info("Network disconnected.")


if __name__ == "__main__":
    main()
